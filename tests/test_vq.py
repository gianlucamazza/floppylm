"""Independent code generation, nearest-code oracle, gradients and actual byte accounting."""

import shutil
import subprocess

import numpy as np
import pytest
import torch

from floppylm.codec import CodecError
from floppylm.vq import BOOK_HEADER, VectorBook, VectorCodec, pack_vectors, pcg32, unpack_vectors


def test_pcg_matches_independent_unsigned_c(tmp_path):
    compiler = shutil.which("cc")
    if not compiler:
        pytest.skip("C compiler unavailable; generator interoperability unqualified")
    source = tmp_path / "pcg.c"
    source.write_text("""#include <stdint.h>
#include <stdio.h>
static uint64_t state;
static uint32_t next(void) {
    uint64_t previous = state;
    state = previous * UINT64_C(6364136223846793005) + UINT64_C(1442695040888963407);
    uint32_t x = (uint32_t)(((previous >> 18u) ^ previous) >> 27u);
    uint32_t r = (uint32_t)(previous >> 59u);
    return (x >> r) | (x << ((-r) & 31u));
}
int main(void) {
    next(); state += 19; next();
    for (int i=0; i<128; ++i) printf("%u\\n", next());
    return 0;
}
""")
    binary = tmp_path / "pcg"
    subprocess.run([compiler, "-std=c99", "-O2", str(source), "-o", str(binary)], check=True)
    expected = np.array(subprocess.check_output([str(binary)], text=True).split(), dtype=np.uint32)
    assert np.array_equal(pcg32(19, 128), expected)


@pytest.mark.parametrize("dimension,rate", [(8, 0.5), (8, 0.75), (16, 0.5), (16, 0.75)])
def test_book_storage_counts_actual_entries_and_seed(dimension, rate):
    fixed = VectorBook(dimension, rate, 19)
    learned = VectorBook(dimension, rate, 19, learned=True)
    assert torch.equal(fixed.values, learned.values)
    assert len(fixed.to_bytes()) == BOOK_HEADER.size
    assert len(learned.to_bytes()) == BOOK_HEADER.size + learned.levels * dimension * 2
    for book in (fixed, learned):
        assert VectorBook.from_bytes(book.to_bytes()).to_bytes() == book.to_bytes()


@pytest.mark.parametrize("policy", ["row16", "row8log"])
def test_nearest_assignment_matches_explicit_numpy_and_zero_row(policy):
    book = VectorBook(8, 0.5, 19)
    codec = VectorCodec(book, policy, chunk=1)
    weights = torch.tensor([[0.0] * 11, list(np.linspace(-0.9, 0.7, 11))], dtype=torch.float32)
    symbols, scales = codec.encode(weights)
    scale = codec.scales.scale_from_bytes(scales, 2).numpy()
    normalized = weights.numpy() / np.where(scale > 0, scale, 1)
    groups = np.pad(normalized, ((0, 0), (0, 5))).reshape(-1, 8)
    distances = np.sum(
        (groups[:, None].astype(np.float64) - book.values.detach().numpy()[None]) ** 2, axis=-1
    )
    assert np.array_equal(symbols, np.argmin(distances, axis=1))
    decoded = codec.decode(symbols, scales, tuple(weights.shape))
    assert torch.equal(decoded[0], torch.zeros(11))
    assert len(symbols) == 4  # Padded tails pay for an entire group index.


def test_lowest_index_wins_tie_and_chunks_do_not_change_assignment():
    book = VectorBook(8, 0.5, 19, learned=True)
    with torch.no_grad():
        book.values.zero_()
    weights = torch.ones(3, 16)
    a, _ = VectorCodec(book, chunk=1).encode(weights)
    b, _ = VectorCodec(book, chunk=64).encode(weights)
    assert np.array_equal(a, b) and np.all(a == 0)


def test_partial_gradient_matches_explicit_group_accumulation():
    book = VectorBook(8, 0.5, 19, learned=True)
    codec = VectorCodec(book)
    weights = torch.arange(16, dtype=torch.float32).reshape(2, 8).div(20).requires_grad_()
    symbols, scales = codec.encode(weights)
    output = codec.partial_weight(weights, 1, 7, symbols=symbols)
    output.sum().backward()
    assert torch.equal(weights.grad, torch.ones_like(weights))
    expected = torch.zeros_like(book.values)
    stored = codec.scales.scale_from_bytes(scales, 2)
    for row, index in enumerate(symbols):
        expected[index] += stored[row]
    assert torch.equal(book.values.grad, expected)
    assert torch.equal(codec.partial_weight(weights, 0, 7), weights)


def test_shared_book_counted_once_and_fixture_decodes_exactly():
    book = VectorBook(8, 0.75, 19, learned=True)
    codec = VectorCodec(book)
    weights = {"a": torch.ones(2, 9), "b": torch.zeros(3, 8)}
    blob, parts = pack_vectors(weights, {"a": codec, "b": codec})
    assert parts["shared"] == len(book.to_bytes())
    assert sum(parts.values()) == len(blob)
    assert blob == pack_vectors(weights, {"a": codec, "b": codec})[0]
    actual = unpack_vectors(blob)
    for name, weight in weights.items():
        symbols, scales = codec.encode(weight)
        assert torch.equal(actual[name], codec.decode(symbols, scales, tuple(weight.shape)))
    for corrupted in (blob[:-1], blob + b"extra"):
        with pytest.raises(CodecError):
            unpack_vectors(corrupted)


def test_mutated_fixed_book_and_nonfinite_weights_fail():
    fixed = VectorBook(8, 0.5, 19)
    with torch.no_grad():
        fixed.values[0, 0] += 1
    with pytest.raises(CodecError, match="fixed book was modified"):
        fixed.to_bytes()
    codec = VectorCodec(VectorBook(8, 0.5, 19))
    with pytest.raises(CodecError, match="nonfinite"):
        codec.encode(torch.full((1, 8), float("nan")))
    with pytest.raises(CodecError):
        codec.decode(np.array([codec.book.levels]), bytes(2), (1, 8))
