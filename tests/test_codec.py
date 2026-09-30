import numpy as np
import pytest
import torch

from floppylm.codec import FP16_MIN, SCALE_POLICIES, CodecError, scalar

FORMATS = ("ternary", "2bit", "4bit")
ALL = [(f, p) for f in FORMATS for p in SCALE_POLICIES]


@pytest.mark.parametrize(("fmt", "policy"), ALL)
def test_symbols_in_range_and_decode_matches_forward(fmt: str, policy: str) -> None:
    c = scalar(fmt, policy)
    w = torch.randn(24, 40)
    sym, scale = c.encode(w)
    assert sym.min() >= 0 and sym.max() < c.levels
    assert len(scale) == c.scale_nbytes(24)
    back = c.decode(sym, scale, (24, 40))
    assert torch.equal(back, c.weight(w).detach())


@pytest.mark.parametrize(("fmt", "policy"), ALL)
def test_zero_rows_reconstruct_exactly_zero(fmt: str, policy: str) -> None:
    c = scalar(fmt, policy)
    w = torch.randn(6, 16)
    w[2] = 0
    sym, scale = c.encode(w)
    back = c.decode(sym, scale, (6, 16))
    assert torch.isfinite(back).all()
    if policy != "tensor16":
        assert torch.equal(back[2], torch.zeros(16))
    zero = torch.zeros(4, 8)
    assert torch.equal(c.decode(*c.encode(zero), (4, 8)), zero)


@pytest.mark.parametrize(("fmt", "policy"), ALL)
def test_tiny_weights_stay_finite_and_bounded(fmt: str, policy: str) -> None:
    c = scalar(fmt, policy)
    w = torch.randn(5, 16) * 1e-9
    back = c.decode(*c.encode(w), (5, 16))
    assert torch.isfinite(back).all()
    assert back.abs().max() <= c.half * FP16_MIN * 1.01


@pytest.mark.parametrize(("fmt", "policy"), ALL)
def test_non_finite_weights_and_overflow_raise(fmt: str, policy: str) -> None:
    c = scalar(fmt, policy)
    for bad in (float("nan"), float("inf")):
        w = torch.randn(3, 8)
        w[1, 2] = bad
        with pytest.raises(CodecError):
            c.encode(w)
    with pytest.raises(CodecError):
        c.encode(torch.full((2, 8), 1e6))


@pytest.mark.parametrize("policy", SCALE_POLICIES)
def test_corrupt_scale_bytes_raise(policy: str) -> None:
    c = scalar("2bit", policy)
    sym, scale = c.encode(torch.randn(4, 8))
    with pytest.raises(CodecError):
        c.decode(sym, scale[:-1], (4, 8))
    nan = np.array([np.nan], dtype="<f2").tobytes()
    with pytest.raises(CodecError):
        c.decode(sym, nan + scale[2:], (4, 8))
    with pytest.raises(CodecError):
        c.decode(sym[:-1], scale, (4, 8))


def test_ternary_is_idempotent() -> None:
    c = scalar("ternary")
    q1 = c.weight(torch.randn(16, 32)).detach()
    assert torch.allclose(c.weight(q1).detach(), q1, rtol=1e-3, atol=1e-6)


def test_ternary_delta_controls_sparsity() -> None:
    w = torch.randn(64, 256)
    zeros = [
        (scalar("ternary", delta=d).quantize(w)[0] == 1).float().mean().item()
        for d in (0.5, 0.7, 1.0)
    ]
    assert zeros[0] < zeros[1] < zeros[2]
    assert abs(zeros[0] - 0.31) < 0.03  # Gaussian: P(|w| < 0.5 * 0.798 sigma)


def test_4bit_edges_clamp() -> None:
    w = torch.cat([torch.tensor([100.0, -100.0]), torch.full((100,), 0.01)]).view(1, -1)
    sym, _ = scalar("4bit").quantize(w)
    assert sym.min() == 0 and sym.max() == 15


def test_straight_through_gradient() -> None:
    w = torch.randn(4, 4, requires_grad=True)
    scalar("2bit").weight(w).sum().backward()
    assert torch.allclose(w.grad, torch.ones_like(w))


def test_scale_bits() -> None:
    assert scalar("ternary", "row16").scale_bits(10) == 160
    assert scalar("ternary", "row8log").scale_bits(10) == 96
    assert scalar("ternary", "tensor16").scale_bits(10) == 16
    assert np.isclose(scalar("ternary").nominal_bits((10, 20)), 200 * np.log2(3) + 160)
