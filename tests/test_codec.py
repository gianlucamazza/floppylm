import numpy as np
import pytest
import torch

from floppylm.codec import SCALE_POLICIES, scalar

FORMATS = ("ternary", "2bit", "4bit")


@pytest.mark.parametrize("policy", SCALE_POLICIES)
@pytest.mark.parametrize("fmt", FORMATS)
def test_symbols_in_range_and_roundtrip(fmt: str, policy: str) -> None:
    c = scalar(fmt, policy)
    w = torch.randn(24, 40)
    sym, scale = c.encode(w)
    assert sym.min() >= 0 and sym.max() < c.levels
    assert len(scale) == c.scale_nbytes(24)
    back = c.decode(sym, scale, (24, 40))
    assert torch.allclose(back, c.weight(w).detach(), rtol=1e-5, atol=1e-7)


def test_ternary_is_idempotent() -> None:
    # absmean-scaled even-level formats are not idempotent by design (unpack freezes weights)
    c = scalar("ternary")
    w = torch.randn(16, 32)
    q1 = c.weight(w).detach()
    assert torch.allclose(c.weight(q1).detach(), q1, rtol=1e-3, atol=1e-6)


@pytest.mark.parametrize("policy", SCALE_POLICIES)
def test_zero_row_has_no_nan(policy: str) -> None:
    w = torch.randn(4, 8)
    w[1] = 0
    for fmt in FORMATS:
        q = scalar(fmt, policy).weight(w)
        assert torch.isfinite(q).all()


def test_ternary_delta_controls_sparsity() -> None:
    w = torch.randn(64, 256)
    zeros = [
        (scalar("ternary", delta=d).quantize(w)[0] == 1).float().mean().item()
        for d in (0.5, 0.7, 1.0)
    ]
    assert zeros[0] < zeros[1] < zeros[2]
    assert abs(zeros[0] - 0.31) < 0.03  # Gaussian: P(|w| < 0.5 * 0.798 sigma)


def test_4bit_edges_clamp() -> None:
    c = scalar("4bit")
    w = torch.cat([torch.tensor([100.0, -100.0]), torch.full((100,), 0.01)]).view(1, -1)
    sym, _ = c.quantize(w)
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
