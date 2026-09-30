import pytest
import torch

from floppylm.model import GPTConfig, TinyGPT
from floppylm.pack import pack_sections, unpack


def _model(**kw) -> TinyGPT:
    torch.manual_seed(0)
    base = dict(vocab=256, d=32, n_layers=2, n_heads=2, d_ff=80)
    return TinyGPT(GPTConfig(**(base | kw)))


@pytest.mark.parametrize(
    "kw",
    [
        {"core_fmt": "ternary"},
        {"core_fmt": "2bit"},
        {"core_fmt": "ternary", "scale_policy": "row8log", "delta": 0.7},
        {"core_fmt": "2bit", "scale_policy": "tensor16", "mlp": "swiglu"},
        {"core_fmt": "ternary", "mlp": "relu2", "qk_norm": True},
    ],
)
def test_roundtrip_reproduces_logits(kw: dict) -> None:
    m = _model(**kw).eval()
    blob, parts = pack_sections(m)
    assert sum(parts.values()) == len(blob)
    m2 = unpack(blob).eval()
    x = torch.randint(0, 256, (2, 16))
    assert torch.allclose(m(x), m2(x), atol=1e-4)
    assert m2.cfg == m.cfg


def test_counted_bytes_track_nominal_bits() -> None:
    m = _model()
    blob, parts = pack_sections(m)
    payload = 8 * (len(blob) - parts["header"])
    assert 0.95 < payload / m.nominal_bits() < 1.03
