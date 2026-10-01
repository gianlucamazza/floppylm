"""Train-only, byte-exact BPE oracle for ADR 0013 functional qualification."""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass

import numpy as np

SCHEMA = "floppylm.e1.bpe.v1"
PRETOKENIZER = "ascii-runs-v1"
RUNS = re.compile(rb"\x03|[A-Za-z]+|[0-9]+|[ \t\r\n\v\f]+|[^A-Za-z0-9 \t\r\n\v\f\x03]+")


def _merge(tokens: tuple[int, ...], pair: tuple[int, int], token: int) -> tuple[int, ...]:
    result, index = [], 0
    while index < len(tokens):
        if index + 1 < len(tokens) and tokens[index : index + 2] == pair:
            result.append(token)
            index += 2
        else:
            result.append(tokens[index])
            index += 1
    return tuple(result)


@dataclass(frozen=True)
class ByteBPE:
    merges: tuple[tuple[int, int], ...] = ()

    def __post_init__(self):
        if len(self.merges) > 256:
            raise ValueError("qualification vocabulary exceeds 512")
        seen = set()
        for index, pair in enumerate(self.merges):
            if (
                len(pair) != 2
                or any(type(x) is not int or not 0 <= x < 256 + index for x in pair)
                or 3 in pair
                or pair in seen
            ):
                raise ValueError("invalid, duplicate or boundary-crossing merge")
            seen.add(pair)

    @property
    def vocab(self) -> int:
        return 256 + len(self.merges)

    @classmethod
    def train(cls, train_bytes: bytes, vocab: int = 512) -> ByteBPE:
        if not isinstance(train_bytes, bytes) or type(vocab) is not int or not 256 <= vocab <= 512:
            raise ValueError("bytes and vocabulary in [256, 512] required")
        words = Counter(tuple(word) for word in RUNS.findall(train_bytes))
        merges = []
        while len(merges) < vocab - 256:
            counts = Counter()
            for word, frequency in words.items():
                for pair in zip(word, word[1:]):
                    if 3 not in pair:
                        counts[pair] += frequency
            if not counts:
                break
            pair = min(counts, key=lambda p: (-counts[p], p))
            token = 256 + len(merges)
            merged = Counter()
            for word, frequency in words.items():
                merged[_merge(word, pair, token)] += frequency
            words = merged
            merges.append(pair)
        return cls(tuple(merges))

    def encode(self, data: bytes) -> np.ndarray:
        if not isinstance(data, bytes):
            raise ValueError("BPE encodes raw bytes without normalization")
        cached = {}
        result = []
        for word in RUNS.findall(data):
            if word not in cached:
                tokens = tuple(word)
                for index, pair in enumerate(self.merges):
                    tokens = _merge(tokens, pair, 256 + index)
                cached[word] = tokens
            result.extend(cached[word])
        return np.asarray(result, dtype=np.uint16)

    def decode(self, tokens) -> bytes:
        table = [bytes([byte]) for byte in range(256)]
        for left, right in self.merges:
            table.append(table[left] + table[right])
        result = []
        for token in tokens:
            if isinstance(token, (bool, np.bool_)) or not isinstance(token, (int, np.integer)):
                raise ValueError("token IDs must be integers")
            if not 0 <= token < len(table):
                raise ValueError("token ID outside vocabulary")
            result.append(table[token])
        return b"".join(result)

    def to_bytes(self) -> bytes:
        return json.dumps(
            {"schema": SCHEMA, "pretokenizer": PRETOKENIZER, "merges": self.merges},
            sort_keys=True,
            separators=(",", ":"),
        ).encode()

    @classmethod
    def from_bytes(cls, data: bytes) -> ByteBPE:
        try:
            value = json.loads(data)
            if (
                set(value) != {"schema", "pretokenizer", "merges"}
                or value["schema"] != SCHEMA
                or value["pretokenizer"] != PRETOKENIZER
            ):
                raise ValueError("unknown tokenizer contract")
            model = cls(tuple(tuple(pair) for pair in value["merges"]))
            if model.to_bytes() != data:
                raise ValueError("noncanonical tokenizer")
            return model
        except (TypeError, KeyError, json.JSONDecodeError) as error:
            raise ValueError("malformed tokenizer") from error
