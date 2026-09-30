from floppylm.model import GPTConfig, TinyGPT
from floppylm.shapes import fill_d_ff, grid, nominal_bits


def test_meta_nominal_matches_instance() -> None:
    cfg = GPTConfig(d=64, n_layers=3, n_heads=4, d_ff=200)
    assert nominal_bits(cfg) == TinyGPT(cfg).nominal_bits()


def test_fill_d_ff_hits_budget() -> None:
    budget = 687_500
    for mlp in ("gelu", "swiglu"):
        cfg = fill_d_ff(GPTConfig(d=64, n_layers=5, n_heads=4, mlp=mlp), budget)
        bits = nominal_bits(cfg)
        assert 0.995 * budget <= bits <= budget


def test_grid_members_fill_budget() -> None:
    budget = 687_500
    cfgs = grid(GPTConfig(), budget)
    assert cfgs
    for c in cfgs:
        assert 0.995 * budget <= nominal_bits(c) <= budget
