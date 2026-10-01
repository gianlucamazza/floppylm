"""Byte fidelity and frozen tokenizer storage are independent of language quality."""

import json

import numpy as np
import pytest

from floppylm.bpe import ByteBPE


def test_round_trip_all_bytes_and_unseen_invalid_utf8():
    tokenizer = ByteBPE.train(b"the cat sat.\x03the cat ran. " * 100)
    data = bytes(range(256)) + b"\xff\xfe\x00\x03" + "caffè 👋".encode()
    assert tokenizer.decode(tokenizer.encode(data)) == data
    assert ByteBPE.from_bytes(tokenizer.to_bytes()).to_bytes() == tokenizer.to_bytes()


def test_tied_pairs_are_deterministic_and_boundary_never_merged():
    tokenizer = ByteBPE.train(b"ab ac\x03ab ac", vocab=257)
    assert tokenizer.merges == ((97, 98),)
    encoded = tokenizer.encode(b"ab\x03ab")
    assert encoded.tolist() == [256, 3, 256]
    assert ByteBPE.train(b"a", vocab=512).vocab == 256


@pytest.mark.parametrize("tokens", [[-1], [512], [True], [1.5]])
def test_invalid_token_ids_are_rejected(tokens):
    with pytest.raises(ValueError):
        ByteBPE().decode(tokens)


@pytest.mark.parametrize("merges", [((3, 97),), ((256, 97),), ((97, 98), (97, 98))])
def test_malformed_merge_tables_are_rejected(merges):
    with pytest.raises(ValueError):
        ByteBPE(merges)


def test_no_normalization_empty_and_random_input():
    rng = np.random.default_rng(7)
    tokenizer = ByteBPE.train(b"Alpha ALPHA alpha\t\nalpha 123", 280)
    for data in (b"", b"A\r\nA  \tA", rng.integers(0, 256, 4096, dtype=np.uint8).tobytes()):
        assert tokenizer.decode(tokenizer.encode(data)) == data
    with pytest.raises(ValueError, match="noncanonical"):
        ByteBPE.from_bytes(json.dumps(json.loads(tokenizer.to_bytes()), indent=1).encode())
