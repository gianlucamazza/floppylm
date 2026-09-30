import math

import numpy as np
import pytest

from floppylm.rans import (
    bitpack_decode,
    bitpack_encode,
    decode_best,
    encode_best,
    rans_decode,
    rans_encode,
)


@pytest.mark.parametrize("alphabet", [2, 3, 4, 16, 256, 4096])
def test_rans_roundtrip(alphabet: int) -> None:
    sym = np.random.default_rng(0).integers(0, alphabet, size=5000)
    assert np.array_equal(rans_decode(rans_encode(sym, alphabet)), sym)


@pytest.mark.parametrize("alphabet", [2, 3, 5, 4, 16, 4096, 4097, 65536])
def test_bitpack_roundtrip(alphabet: int) -> None:
    sym = np.random.default_rng(1).integers(0, alphabet, size=3001)
    assert np.array_equal(bitpack_decode(bitpack_encode(sym, alphabet)), sym)


def test_edge_cases() -> None:
    for sym in (np.array([], dtype=np.int64), np.array([2]), np.zeros(1000, dtype=np.int64)):
        assert np.array_equal(rans_decode(rans_encode(sym, 3)), sym)
        assert np.array_equal(decode_best(encode_best(sym, 3)), sym)


def test_rans_near_entropy_skewed() -> None:
    n = 200_000
    sym = np.random.default_rng(2).choice(3, size=n, p=[0.25, 0.5, 0.25])
    bits = 8 * len(rans_encode(sym, 3)) / n
    assert 1.5 * 0.99 < bits < 1.5 * 1.01


def test_rans_very_skewed_many_rare_symbols() -> None:
    rng = np.random.default_rng(3)
    sym = np.where(rng.random(50_000) < 0.99, 0, rng.integers(1, 4096, size=50_000))
    assert np.array_equal(rans_decode(rans_encode(sym, 4096)), sym)


def test_best_picks_shorter_and_bitpack_is_exact_for_pow2() -> None:
    n = 40_000
    sym = np.random.default_rng(4).integers(0, 4096, size=n)
    blob = encode_best(sym, 4096)
    assert blob[0] == 1  # uniform 12-bit symbols: bitpack beats rANS + 8 KB table
    assert len(blob) == 1 + 6 + n * 12 // 8
    tern = np.random.default_rng(5).integers(0, 3, size=n)
    assert 8 * len(encode_best(tern, 3)) / n < math.log2(3) * 1.02
