"""Host init-pack adjustment before the first scientific attempt (ADR 0019)."""

import argparse
import importlib.util
from pathlib import Path

from floppylm.model import GPTConfig, TinyGPT
from floppylm.pack import pack_sections
from floppylm.parity import admissible
from floppylm.seed import seed_all

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("e0_v2_host_pack", ROOT / "experiments/e0_v2.py")
e0 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e0)

TARGET = 11_000_000 / 16 / 8


def _neutral(policy: str, d_ff: int) -> GPTConfig:
    return GPTConfig(
        d=96, n_layers=3, n_heads=6, d_ff=d_ff, scale_policy=policy, ctx=256
    )


def test_inside_parity_keeps_the_solver_shape():
    cfg = GPTConfig(d=32, n_layers=1, n_heads=2, d_ff=48, ctx=16)
    seed_all(0)
    nbytes = len(pack_sections(TinyGPT(cfg))[0])
    seed_all(0)
    adjusted, record = e0.host_pack_adjustment(cfg, float(nbytes))
    assert adjusted == cfg
    assert record["submitted_d_ff"] == cfg.d_ff
    assert record["init_model_bytes"] == nbytes
    assert record["init_fill"] == 1


def test_unusable_adjustment_keeps_the_solver_shape():
    cfg = _neutral("row16", 391)
    seed_all(0)
    adjusted, record = e0.host_pack_adjustment(cfg, 1.0)
    assert adjusted == cfg
    assert record["submitted_d_ff"] == cfg.d_ff


def test_published_neutral_shapes_use_the_init_pack_not_the_trained_repair():
    # Trained S3 repairs were d_ff 400 (row16) and 424 (row8log). The init pack is
    # slightly less compact, so fill_d_ff stops two steps earlier. Both submitted
    # init packs are inside ±1%.
    expected = {"row16": (391, 398, 400), "row8log": (415, 422, 424)}
    for policy, (solver_ff, submitted_ff, trained_ff) in expected.items():
        cfg = _neutral(policy, solver_ff)
        seed_all(0)
        adjusted, record = e0.host_pack_adjustment(cfg, TARGET)
        assert adjusted.d_ff == submitted_ff, (
            f"{policy} init pack chose d_ff {adjusted.d_ff} "
            f"ratio {record['host_ratio']}; trained S3 repair was {trained_ff}"
        )
        assert record["submitted_d_ff"] == submitted_ff
        assert (adjusted.d, adjusted.n_layers, adjusted.mlp, adjusted.scale_policy) == (
            cfg.d,
            cfg.n_layers,
            cfg.mlp,
            cfg.scale_policy,
        )
        seed_all(0)
        submitted = len(pack_sections(TinyGPT(adjusted))[0])
        ok, reasons = admissible({"init": submitted}, TARGET)
        assert ok, reasons


def test_host_adjustment_skips_smoke_retry_and_resume():
    assert e0._host_adjusts(argparse.Namespace(smoke=False))
    assert not e0._host_adjusts(argparse.Namespace(smoke=True))
    assert not e0._host_adjusts(argparse.Namespace(smoke=False, retry_of="previous"))
    assert not e0._host_adjusts(argparse.Namespace(smoke=False, resume="run"))
