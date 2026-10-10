import json
import math
import struct

import pytest
import torch

from floppylm.codec import SCALE_POLICIES
from floppylm.model import GPTConfig, QLinear, TinyGPT
from floppylm.pack import FormatError, pack, pack_sections, unpack
from floppylm.shapes import nominal_bits
from floppylm.vq import VectorBook

CASES = [
    {"core_fmt": f, "scale_policy": p} for f in ("ternary", "2bit", "4bit") for p in SCALE_POLICIES
] + [
    {"core_fmt": "ternary", "delta": 0.7, "mlp": "swiglu"},
    {"core_fmt": "2bit", "mlp": "relu2", "qk_norm": True},
]


def _model(**kw) -> TinyGPT:
    torch.manual_seed(0)
    base = dict(vocab=256, d=32, n_layers=2, n_heads=2, d_ff=80)
    return TinyGPT(GPTConfig(**(base | kw)))


@pytest.mark.parametrize("kw", CASES)
def test_roundtrip_is_byte_identical_with_equal_logits(kw: dict) -> None:
    m = _model(**kw).eval()
    blob, parts = pack_sections(m)
    assert sum(parts.values()) == len(blob)
    assert parts["shared"] == 0
    m2 = unpack(blob).eval()
    assert pack(m2) == blob
    assert pack_sections(m2)[1] == parts
    assert m2.cfg == m.cfg
    x = torch.randint(0, 256, (2, 16))
    assert torch.equal(m(x), m2(x))


def test_resave_does_not_requantize() -> None:
    m2 = unpack(pack(_model()))
    rec = m2.blocks[0].qkv.canonical
    assert rec is not None and pack(m2).count(rec) == 1


def test_counted_bytes_track_nominal_bits() -> None:
    m = _model()
    blob, parts = pack_sections(m)
    payload = 8 * (len(blob) - parts["header"])
    assert 0.95 < payload / m.nominal_bits() < 1.03


def _blob() -> bytes:
    return pack(_model())


def test_truncation_at_every_boundary_is_rejected() -> None:
    blob = _blob()
    for n in (0, 3, 5, 20, len(blob) // 2, len(blob) - 1):
        with pytest.raises(FormatError):
            unpack(blob[:n])


def test_trailing_bytes_rejected() -> None:
    with pytest.raises(FormatError, match="trailing"):
        unpack(_blob() + b"\0")


def test_bad_magic_and_headers_rejected() -> None:
    blob = _blob()
    (hlen,) = struct.unpack_from("<H", blob, 4)
    header = json.loads(blob[6 : 6 + hlen])

    def with_header(h: dict | bytes) -> bytes:
        raw = (
            h
            if isinstance(h, bytes)
            else json.dumps(h, separators=(",", ":"), sort_keys=True).encode()
        )
        return blob[:4] + struct.pack("<H", len(raw)) + raw + blob[6 + hlen :]

    with pytest.raises(FormatError, match="magic"):
        unpack(b"XXXX" + blob[4:])
    with pytest.raises(FormatError):
        unpack(with_header(b"{not json"))
    with pytest.raises(FormatError):
        unpack(with_header({**header, "extra": 1}))
    with pytest.raises(FormatError):
        unpack(with_header({**header, "d": -32}))
    with pytest.raises(FormatError):
        unpack(with_header({**header, "core_fmt": "7bit"}))
    with pytest.raises(FormatError):
        unpack(with_header(json.dumps(header, sort_keys=True).encode()))  # non-canonical spacing


def _vq_config(**kw) -> GPTConfig:
    base = dict(
        vocab=32,
        d=32,
        n_layers=1,
        n_heads=2,
        d_ff=20,
        ctx=16,
        core_fmt="vq",
        emb_fmt="4bit",
        scale_policy="row8log",
    )
    return GPTConfig(**(base | kw))


def _vq_model(book: VectorBook, **kw) -> TinyGPT:
    torch.manual_seed(0)
    return TinyGPT(_vq_config(**kw), book)


def _shared(blob: bytes) -> bytes:
    hlen = struct.unpack_from("<H", blob, 4)[0]
    off = 6 + hlen
    n = struct.unpack_from("<I", blob, off)[0]
    return blob[off + 4 : off + 4 + n]


def _body(blob: bytes) -> bytes:
    hlen = struct.unpack_from("<H", blob, 4)[0]
    off = 6 + hlen
    n = struct.unpack_from("<I", blob, off)[0]
    return blob[off + 4 + n :]


@pytest.mark.parametrize("dimension,rate", [(8, 0.5), (8, 0.75), (16, 0.5), (16, 0.75)])
@pytest.mark.parametrize("learned", [False, True])
def test_vq_flp2_roundtrip_stores_one_book(dimension: int, rate: float, learned: bool) -> None:
    book = VectorBook(dimension, rate, 19, learned=learned)
    m = _vq_model(book).eval()
    blob, parts = pack_sections(m)
    assert parts["shared"] == len(book.to_bytes())
    assert _shared(blob) == book.to_bytes()
    assert sum(parts.values()) == len(blob)
    fc2 = m.blocks[0].fc2
    symbols, scale = fc2.codec.encode(fc2.weight.detach())
    rows, cols = fc2.weight.shape
    assert len(symbols) == rows * math.ceil(cols / dimension)
    assert len(scale) == 2 + rows
    assert all(layer.codec.book is m.book for layer in (m.blocks[0].qkv, fc2))
    m2 = unpack(blob).eval()
    assert pack(m2) == blob
    assert m2.book is not None and m2.book.to_bytes() == book.to_bytes()
    assert m2.cfg == m.cfg and set(m2.cfg.to_dict()) == set(GPTConfig.__dataclass_fields__)
    x = torch.randint(0, m.cfg.vocab, (2, 8))
    assert torch.equal(m(x), m2(x))
    matrices = sum(t.weight.numel() for t in m.stored_tensors() if isinstance(t, QLinear))
    extra = book.values.numel() if learned else 0
    assert m.stored_params() == matrices + extra


def test_vq_core_ignores_delta_and_swiglu_roundtrips() -> None:
    book = VectorBook(8, 0.5, 3, learned=True)
    other = VectorBook(8, 0.5, 3, learned=True)
    plain = _vq_model(book, delta=0.5)
    shifted = _vq_model(other, delta=0.7)
    assert pack(plain) != pack(shifted)
    assert _body(pack(plain)) == _body(pack(shifted))
    swiglu = _vq_model(VectorBook(8, 0.5, 3, learned=True), mlp="swiglu")
    blob = pack(swiglu)
    assert pack(unpack(blob)) == blob


def test_vq_layout_rejects_a_missing_extra_or_scalar_book() -> None:
    cfg = _vq_config()
    with pytest.raises(ValueError, match="shared book"):
        nominal_bits(cfg)
    with pytest.raises(ValueError, match="VectorBook"):
        TinyGPT(cfg)
    with pytest.raises(ValueError, match="no book"):
        TinyGPT(_vq_config(core_fmt="ternary", scale_policy="row16"), VectorBook(8, 0.5, 1))
    with pytest.raises(ValueError, match="row8log"):
        _vq_config(scale_policy="row16")
    with pytest.raises(ValueError, match="4-bit"):
        _vq_config(emb_fmt="2bit")

    book = VectorBook(8, 0.5, 1)
    blob = pack(_vq_model(book))
    hlen = struct.unpack_from("<H", blob, 4)[0]
    off = 6 + hlen
    n = struct.unpack_from("<I", blob, off)[0]
    start = off + 4
    empty = blob[:off] + struct.pack("<I", 0) + blob[start + n :]
    payload = blob[start : start + n] + b"\x00"
    extra = blob[:off] + struct.pack("<I", n + 1) + payload + blob[start + n :]
    corrupt = bytearray(blob)
    corrupt[start] ^= 0xFF
    with pytest.raises(FormatError, match="one shared book"):
        unpack(empty)
    with pytest.raises(FormatError, match="shared book"):
        unpack(extra)
    with pytest.raises(FormatError, match="shared book"):
        unpack(bytes(corrupt))

    scalar = pack(_model())
    hlen = struct.unpack_from("<H", scalar, 4)[0]
    off = 6 + hlen
    planted = scalar[:off] + struct.pack("<I", 16) + book.to_bytes() + scalar[off + 4 :]
    with pytest.raises(FormatError, match="no shared section"):
        unpack(planted)


def test_corrupt_stream_rejected() -> None:
    blob = bytearray(_blob())
    blob[-100] ^= 0xFF  # inside the last quantized record or norms
    blob2 = bytearray(_blob())
    blob2[200] ^= 0x55
    rejected = 0
    for b in (bytes(blob), bytes(blob2)):
        try:
            unpack(b)
        except FormatError:
            rejected += 1
    assert rejected >= 1
