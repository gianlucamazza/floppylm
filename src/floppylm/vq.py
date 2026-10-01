"""Standalone vector-weight oracles; not a scientific model or FLP2 extension."""

from __future__ import annotations

import hashlib
import json
import math
import struct

import numpy as np
import torch
import torch.nn.functional as F

from . import rans
from .codec import FP16_MAX, CodecError, scalar

MASK64 = (1 << 64) - 1
BOOK_HEADER = struct.Struct("<4sBBBBQ")
GENERATOR_ID = 1


def pcg32(seed: int, count: int) -> np.ndarray:
    """PCG XSH-RR with fixed odd stream; exact unsigned integer operations."""
    if type(seed) is not int or not 0 <= seed <= MASK64 or count < 0:
        raise CodecError("invalid PCG seed or count")
    state, increment = 0, 1442695040888963407

    def step():
        nonlocal state
        old = state
        state = (old * 6364136223846793005 + increment) & MASK64
        shifted = (((old >> 18) ^ old) >> 27) & 0xFFFFFFFF
        rotation = old >> 59
        return ((shifted >> rotation) | (shifted << ((-rotation) & 31))) & 0xFFFFFFFF

    step()
    state = (state + seed) & MASK64
    step()
    return np.fromiter((step() for _ in range(count)), dtype=np.uint32, count=count)


class VectorBook(torch.nn.Module):
    def __init__(self, dimension: int, rate: float, seed: int, *, learned: bool = False):
        super().__init__()
        if type(dimension) is not int or dimension not in (8, 16) or rate not in (0.5, 0.75):
            raise CodecError("unknown qualification dimension or rate")
        if type(learned) is not bool:
            raise CodecError("learned must be boolean")
        self.dimension, self.bits, self.seed, self.learned = (
            dimension,
            int(dimension * rate),
            seed,
            learned,
        )
        draws = pcg32(seed, self.levels * dimension * 12).astype(np.uint64) & 0xFFFF
        summed = draws.reshape(self.levels, dimension, 12).sum(-1).astype(np.int64)
        values = ((summed - 393210) / 65536).astype(np.float32)
        self.values = torch.nn.Parameter(
            torch.from_numpy(values).half().float(), requires_grad=learned
        )

    @property
    def levels(self):
        return 1 << self.bits

    def stored_values(self):
        if not torch.isfinite(self.values).all() or self.values.abs().max() > FP16_MAX:
            raise CodecError("book entries cannot be stored as finite fp16")
        stored = self.values.detach().half().float()
        return stored + (self.values - self.values.detach()) if self.learned else stored

    def to_bytes(self):
        header = BOOK_HEADER.pack(
            b"VQB1", self.dimension, self.bits, GENERATOR_ID, int(self.learned), self.seed
        )
        values = self.stored_values().detach().numpy().astype("<f2").tobytes()
        if not self.learned:
            regenerated = VectorBook(self.dimension, self.bits / self.dimension, self.seed)
            if not torch.equal(self.values.detach(), regenerated.values.detach()):
                raise CodecError("fixed book was modified")
        return header + (values if self.learned else b"")

    @classmethod
    def from_bytes(cls, blob):
        if len(blob) < BOOK_HEADER.size:
            raise CodecError("truncated book")
        magic, dimension, bits, generator, learned, seed = BOOK_HEADER.unpack_from(blob)
        if magic != b"VQB1" or generator != GENERATOR_ID or learned not in (0, 1) or not dimension:
            raise CodecError("invalid book header")
        book = cls(dimension, bits / dimension, seed, learned=bool(learned))
        expected = BOOK_HEADER.size + (book.levels * dimension * 2 if learned else 0)
        if len(blob) != expected:
            raise CodecError("book payload length differs")
        if learned:
            values = np.frombuffer(blob, "<f2", offset=BOOK_HEADER.size).astype(np.float32)
            with torch.no_grad():
                book.values.copy_(torch.from_numpy(values).reshape_as(book.values))
        if book.to_bytes() != blob:
            raise CodecError("noncanonical book")
        return book


class VectorCodec:
    def __init__(self, book: VectorBook, policy: str = "row16", chunk: int = 64):
        if policy not in ("row16", "row8log") or type(chunk) is not int or not 1 <= chunk <= 1024:
            raise CodecError("invalid vector scale policy or assignment chunk")
        self.book, self.policy, self.chunk = book, policy, chunk
        self.scales = scalar("2bit", policy)

    def _inputs(self, weight):
        if weight.ndim != 2 or min(weight.shape) < 1 or weight.device.type != "cpu":
            raise CodecError("nonempty CPU matrix required")
        detached = weight.detach().float()
        if not torch.isfinite(detached).all():
            raise CodecError("nonfinite vector weights")
        raw = detached.square().mean(1, keepdim=True).sqrt()
        scale_bytes = self.scales.scale_to_bytes(self.scales.store_scale(raw))
        scale = self.scales.scale_from_bytes(scale_bytes, weight.shape[0])
        normalized = detached / torch.where(scale > 0, scale, torch.ones_like(scale))
        padded = F.pad(normalized, (0, (-weight.shape[1]) % self.book.dimension))
        return padded.reshape(-1, self.book.dimension), scale, scale_bytes

    @torch.no_grad()
    def encode(self, weight):
        groups, _, scale_bytes = self._inputs(weight)
        book = self.book.stored_values().detach()
        symbols = []
        for group in groups.split(self.chunk):
            distances = (group[:, None, :] - book[None, :, :]).square().sum(-1)
            symbols.append(distances.argmin(-1))
        return torch.cat(symbols).numpy(), scale_bytes

    def _reconstruct(self, symbols, scale, shape):
        rows, cols = shape
        groups = math.ceil(cols / self.book.dimension)
        symbols = np.asarray(symbols)
        if (
            symbols.dtype.kind not in "iu"
            or symbols.size != rows * groups
            or symbols.min() < 0
            or symbols.max() >= self.book.levels
        ):
            raise CodecError("vector symbol stream differs from shape/alphabet")
        indices = torch.from_numpy(np.ascontiguousarray(symbols.astype(np.int64))).reshape(-1)
        values = F.embedding(indices, self.book.stored_values()).reshape(
            rows, groups * self.book.dimension
        )
        return values[:, :cols] * scale

    def decode(self, symbols, scale_bytes, shape):
        if len(shape) != 2 or any(type(x) is not int or x < 1 for x in shape):
            raise CodecError("invalid vector shape")
        scale = self.scales.scale_from_bytes(scale_bytes, shape[0])
        return self._reconstruct(symbols, scale, shape)

    def partial_weight(self, weight, probability: float, seed: int, *, symbols=None):
        """Partial QAT oracle; callers may reuse assignments between declared snap steps."""
        if not 0 <= probability <= 1 or type(seed) is not int or seed < 0:
            raise CodecError("invalid partial-quantization recipe")
        _, scale, scale_bytes = self._inputs(weight)
        if symbols is None:
            symbols, scale_bytes = self.encode(weight)
        reconstructed = self.decode(symbols, scale_bytes, tuple(weight.shape))
        groups = math.ceil(weight.shape[1] / self.book.dimension)
        rng = torch.Generator().manual_seed(seed)
        mask = torch.rand((weight.shape[0], groups), generator=rng) < probability
        mask = mask.repeat_interleave(self.book.dimension, -1)[:, : weight.shape[1]]
        quantized = reconstructed + (weight - weight.detach())
        return torch.where(mask, quantized, weight)

    @torch.no_grad()
    def snap(self, weight):
        symbols, scale = self.encode(weight)
        weight.copy_(self.decode(symbols, scale, tuple(weight.shape)))
        return symbols


def pack_vectors(weights: dict[str, torch.Tensor], codecs: dict[str, VectorCodec]):
    """Count each shared book once in a standalone functional fixture container."""
    if not weights or weights.keys() != codecs.keys():
        raise CodecError("named weights and codecs differ")
    books, records, tensors = {}, [], []
    scale_bytes, symbol_bytes = 0, 0
    for name in sorted(weights):
        if not isinstance(name, str) or not name:
            raise CodecError("invalid tensor name")
        codec, weight = codecs[name], weights[name]
        book = codec.book.to_bytes()
        book_id = hashlib.sha256(book).hexdigest()
        books[book_id] = book
        symbols, scales = codec.encode(weight)
        stream = rans.encode_best(symbols, codec.book.levels)
        records.append(scales + stream)
        scale_bytes += len(scales)
        symbol_bytes += len(stream)
        tensors.append(
            {
                "name": name,
                "shape": list(weight.shape),
                "policy": codec.policy,
                "book": book_id,
                "symbol_bytes": len(stream),
            }
        )
    metadata = {
        "schema": "floppylm.e1.vector-fixture.v1",
        "books": [{"id": key, "bytes": len(books[key])} for key in sorted(books)],
        "tensors": tensors,
    }
    header = json.dumps(metadata, sort_keys=True, separators=(",", ":")).encode()
    blob = b"VQF1" + struct.pack("<I", len(header)) + header
    blob += b"".join(books[key] for key in sorted(books)) + b"".join(records)
    parts = {
        "header": 8 + len(header),
        "shared": sum(map(len, books.values())),
        "scales": scale_bytes,
        "symbols": symbol_bytes,
    }
    if sum(parts.values()) != len(blob):
        raise AssertionError("vector byte accounting differs")
    return blob, parts


def unpack_vectors(blob):
    """Decode functional fixture records; no scientific model/runtime format is implied."""
    offset = 0

    def take(count):
        nonlocal offset
        if type(count) is not int or count < 0 or offset + count > len(blob):
            raise CodecError("truncated or invalid vector fixture")
        value = blob[offset : offset + count]
        offset += count
        return value

    if take(4) != b"VQF1":
        raise CodecError("unknown vector fixture")
    raw = take(struct.unpack("<I", take(4))[0])
    try:
        metadata = json.loads(raw)
        if (
            set(metadata) != {"schema", "books", "tensors"}
            or metadata["schema"] != "floppylm.e1.vector-fixture.v1"
            or json.dumps(metadata, sort_keys=True, separators=(",", ":")).encode() != raw
        ):
            raise CodecError("invalid vector fixture metadata")
        books = {}
        for row in metadata["books"]:
            payload = take(row["bytes"])
            if row["id"] in books or hashlib.sha256(payload).hexdigest() != row["id"]:
                raise CodecError("duplicate or hash-mismatched book")
            books[row["id"]] = VectorBook.from_bytes(payload)
        weights, used = {}, set()
        for row in metadata["tensors"]:
            if not isinstance(row["name"], str) or not row["name"] or row["name"] in weights:
                raise CodecError("invalid or duplicate tensor name")
            codec = VectorCodec(books[row["book"]], row["policy"])
            shape = tuple(row["shape"])
            if len(shape) != 2 or any(type(x) is not int or x < 1 for x in shape):
                raise CodecError("invalid fixture shape")
            scales = take(codec.scales.scale_nbytes(shape[0]))
            stream = take(row["symbol_bytes"])
            if (
                len(stream) < 7
                or (struct.unpack_from("<H", stream, 5)[0] or 65536) != codec.book.levels
            ):
                raise CodecError("symbol alphabet differs from book")
            symbols = rans.decode_best(stream)
            weights[row["name"]] = codec.decode(symbols, scales, shape).detach()
            used.add(row["book"])
        if offset != len(blob) or not weights or used != books.keys():
            raise CodecError("trailing bytes, empty weights or unused books")
        return weights
    except (TypeError, KeyError, ValueError, struct.error, rans.StreamError) as error:
        raise CodecError("malformed vector fixture: " + str(error)) from error
