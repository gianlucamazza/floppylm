"""Regression tests for the independent review of E0 v2."""

import argparse
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

import pytest
import torch

from floppylm.model import GPTConfig, TinyGPT
from floppylm.pack import FormatError, pack, unpack

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("e0_v2_review", ROOT / "experiments/e0_v2.py")
e0 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e0)


def model():
    return TinyGPT(GPTConfig(d=32, n_layers=1, n_heads=2, d_ff=48, ctx=16))


def test_loaded_model_is_inference_only():
    m = unpack(pack(model()))
    assert not m.training
    assert not any(p.requires_grad for p in m.parameters())
    with pytest.raises(RuntimeError, match="inference"):
        m.train()
    m.eval()


@pytest.mark.parametrize("tensor", ["emb", "norm"])
def test_mutated_loaded_model_cannot_serialize(tensor):
    m = unpack(pack(model()))
    with torch.no_grad():
        getattr(m, tensor).weight.add_(0.125)
    with pytest.raises(FormatError, match="modified"):
        pack(m)


def test_grid_preserves_requested_limits_and_shape(tmp_path, monkeypatch):
    a = argparse.Namespace(
        mlp="gelu",
        fmt="ternary",
        scale_policy="row16",
        delta=0.5,
        ctx=64,
        budget_frac=1 / 16,
        jobs=1,
        seed=0,
        lr=0.003,
        wd=0.1,
        batch=8,
        qk_norm=False,
        tokens=8192,
        branches=2,
        val_bytes=16384,
    )
    cfg = GPTConfig(d=32, n_layers=1, n_heads=2, d_ff=48, ctx=64)
    commands = []

    class Proc:
        def __init__(self, cmd, **kw):
            commands.append(cmd)

        def poll(self):
            return 0

        def wait(self):
            return 0

    monkeypatch.setattr(e0, "RUNS", tmp_path)
    with (
        patch.object(e0.shapes, "grid", return_value=[cfg]),
        patch.object(e0.subprocess, "Popen", Proc),
    ):
        assert e0.cmd_grid(a) == 0
    cmd = commands[0]
    for flag, value in [
        ("--tokens", "8192"),
        ("--branches", "2"),
        ("--val-bytes", "16384"),
        ("--d-ff", "48"),
    ]:
        assert flag in cmd and cmd[cmd.index(flag) + 1] == value


def fixture_run(tmp_path, name, size=1000, target=1000, smoke=False, verdict="saturo"):
    artifact = tmp_path / f"{name}.flp"
    artifact.write_bytes(b"x" * size)
    return {
        "status": "completed",
        "smoke": smoke,
        "target_bytes": target,
        "saturation": {"verdict": verdict},
        "branches": [
            {
                "artifact": str(artifact),
                "sha256": e0.runlog.sha256_file(artifact),
                "model_bytes": size,
                "val_bpb": 2.0,
            }
        ],
    }


def freeze(tmp_path, monkeypatch, summaries, functional=False):
    monkeypatch.setattr(e0, "EVIDENCE", tmp_path / "evidence")
    monkeypatch.setattr(e0, "_summary", summaries.__getitem__)
    return e0.cmd_freeze(
        argparse.Namespace(freeze=list(summaries), name="selection", functional=functional)
    )


@pytest.mark.parametrize("kwargs", [{"smoke": True}, {"verdict": "non saturo"}, {"size": 900}])
def test_scientific_freeze_rejects_ineligible(tmp_path, monkeypatch, kwargs):
    s = fixture_run(tmp_path, "a", **kwargs)
    with pytest.raises(SystemExit):
        freeze(tmp_path, monkeypatch, {"a": s})
    assert not (tmp_path / "evidence/selections/selection.json").exists()


def test_freeze_rejects_pairwise_spread(tmp_path, monkeypatch):
    sums = {"a": fixture_run(tmp_path, "a", size=992), "b": fixture_run(tmp_path, "b", size=1008)}
    with pytest.raises(SystemExit):
        freeze(tmp_path, monkeypatch, sums)


def test_freeze_rejects_different_targets(tmp_path, monkeypatch):
    sums = {
        "a": fixture_run(tmp_path, "a"),
        "b": fixture_run(tmp_path, "b", size=2000, target=2000),
    }
    with pytest.raises(SystemExit):
        freeze(tmp_path, monkeypatch, sums)


@pytest.mark.parametrize("functional", [False, True])
def test_valid_selection_has_explicit_purpose(tmp_path, monkeypatch, functional):
    s = fixture_run(
        tmp_path, "a", smoke=functional, verdict="non determinato" if functional else "saturo"
    )
    assert freeze(tmp_path, monkeypatch, {"a": s}, functional) == 0
    sel = json.loads((tmp_path / "evidence/selections/selection.json").read_text())
    assert sel["purpose"] == ("functional" if functional else "scientific")


def test_functional_freeze_does_not_bypass_scientific_gates(tmp_path, monkeypatch):
    with pytest.raises(SystemExit):
        freeze(tmp_path, monkeypatch, {"a": fixture_run(tmp_path, "a")}, True)


def test_grid_child_runs_with_exact_limits(tmp_path, monkeypatch):
    """Exercise the real child process without touching research data or evidence."""
    import shutil

    import numpy as np

    (tmp_path / "experiments").mkdir()
    shutil.copy(ROOT / "experiments/e0_v2.py", tmp_path / "experiments/e0_v2.py")
    shutil.copytree(
        ROOT / "src/floppylm",
        tmp_path / "src/floppylm",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    data = tmp_path / "data/tinystories"
    data.mkdir(parents=True)
    for split in ("train", "val", "test"):
        (data / f"{split}.bin").write_bytes(b"abc xyz " * 128)
    a = argparse.Namespace(
        mlp="gelu",
        fmt="ternary",
        scale_policy="row16",
        delta=0.5,
        ctx=16,
        budget_frac=1 / 16,
        jobs=1,
        seed=0,
        lr=0.003,
        wd=0.1,
        batch=2,
        qk_norm=False,
        tokens=128,
        branches=2,
        val_bytes=65,
    )
    cfg = GPTConfig(d=32, n_layers=1, n_heads=2, d_ff=48, ctx=16)
    monkeypatch.setattr(e0, "RUNS", tmp_path / "runs")
    monkeypatch.setattr(e0, "__file__", str(tmp_path / "experiments/e0_v2.py"))
    with patch.object(e0.shapes, "grid", return_value=[cfg]):
        assert e0.cmd_grid(a) == 0
    summaries = list((tmp_path / "docs/evidence/e0-v2/runs").glob("*/summary.json"))
    assert len(summaries) == 1
    s = json.loads(summaries[0].read_text())
    assert s["status"] == "completed"
    assert s["config"]["d_ff"] == 48
    assert s["spec"]["tokens"] == 128 and s["spec"]["branches"] == 2
    assert [b["tokens_seen"] for b in s["branches"]] == [128, 256]
    assert all(b["val_scored_bytes"] == 64 and np.isfinite(b["val_bpb"]) for b in s["branches"])


def test_final_test_propagates_functional_purpose(tmp_path, monkeypatch):
    import numpy as np

    blob = pack(model())
    artifact = tmp_path / "model.flp"
    artifact.write_bytes(blob)
    selections = tmp_path / "evidence/selections"
    selections.mkdir(parents=True)
    sel = {
        "purpose": "functional",
        "items": [
            {"run_id": "smoke", "artifact": str(artifact), "sha256": e0.runlog.sha256_bytes(blob)}
        ],
    }
    (selections / "smoke.json").write_text(json.dumps(sel))
    monkeypatch.setattr(e0, "EVIDENCE", tmp_path / "evidence")
    monkeypatch.setattr(e0.data_mod, "load", lambda *args: np.zeros(40, dtype=np.uint8))
    monkeypatch.setattr(
        e0.data_mod,
        "manifest",
        lambda *args: {"verified": {"prepared": {"test": {"sha256": "test"}}}},
    )
    assert e0.cmd_final_test(argparse.Namespace(final_test="smoke")) == 0
    assert json.loads((selections / "smoke.test.json").read_text())["purpose"] == "functional"
    with pytest.raises(SystemExit, match="once"):
        e0.cmd_final_test(argparse.Namespace(final_test="smoke"))
