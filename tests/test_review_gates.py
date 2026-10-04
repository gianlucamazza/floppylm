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
from floppylm.train import TrainSpec

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
        ]
        * (1 if smoke else 3),
    }


def freeze(tmp_path, monkeypatch, summaries, functional=False):
    monkeypatch.setattr(e0, "EVIDENCE", tmp_path / "evidence")
    monkeypatch.setattr(e0, "_summary", summaries.__getitem__)
    return e0.cmd_freeze(
        argparse.Namespace(freeze=list(summaries), name="selection", functional=functional)
    )


@pytest.mark.parametrize("kwargs", [{"smoke": True}, {"size": 900}])
def test_scientific_freeze_rejects_ineligible(tmp_path, monkeypatch, kwargs):
    s = fixture_run(tmp_path, "a", **kwargs)
    with pytest.raises(SystemExit):
        freeze(tmp_path, monkeypatch, {"a": s})
    assert not (tmp_path / "evidence/selections/selection.json").exists()


def test_scientific_freeze_accepts_unsaturated_byte_ok_runs(tmp_path, monkeypatch):
    s = fixture_run(tmp_path, "a", verdict="non saturo")
    assert freeze(tmp_path, monkeypatch, {"a": s}) == 0
    sel = json.loads((tmp_path / "evidence/selections/selection.json").read_text())
    assert sel["purpose"] == "scientific"


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


def test_scientific_selection_uses_4t_not_last_branch(tmp_path, monkeypatch):
    s = fixture_run(tmp_path, "a")
    s["branches"].append({"artifact": "missing-8t.flp"})
    assert freeze(tmp_path, monkeypatch, {"a": s}) == 0


def test_parity_checks_actual_artifact(tmp_path, monkeypatch):
    s = fixture_run(tmp_path, "a")
    monkeypatch.setattr(e0, "_summary", lambda r: s)
    Path(s["branches"][2]["artifact"]).write_bytes(b"changed")
    with pytest.raises(SystemExit, match="size"):
        e0.cmd_parity(argparse.Namespace(parity=["a"]))


def test_final_test_existing_reservation_does_not_read_test(tmp_path, monkeypatch):
    selections = tmp_path / "selections"
    selections.mkdir()
    (selections / "a.json").write_text('{"purpose": "scientific", "items": []}')
    (selections / "a.test.reservation.json").write_text('{"state": "running"}')
    monkeypatch.setattr(e0, "EVIDENCE", tmp_path)
    monkeypatch.setattr(e0.data_mod, "load", lambda *a: pytest.fail("test was read"))
    with pytest.raises(SystemExit, match="reservation"):
        e0.cmd_final_test(argparse.Namespace(final_test="a"))


def test_run_data_failure_records_failed_status(tmp_path, monkeypatch):
    monkeypatch.setattr(e0, "RUNS", tmp_path / "runs")
    monkeypatch.setattr(e0, "EVIDENCE", tmp_path / "evidence")
    monkeypatch.setattr(e0.data_mod, "manifest", lambda *a: {"verified": {"prepared": {}}})
    monkeypatch.setattr(e0.data_mod, "load", lambda *a: (_ for _ in ()).throw(OSError("data")))
    a = argparse.Namespace(
        smoke=True,
        d=32,
        layers=1,
        d_ff=48,
        ctx=64,
        budget_frac=1 / 16,
        tokens=8192,
        batch=8,
        val_bytes=65,
        mlp="gelu",
        fmt="ternary",
        scale_policy="row16",
        delta=0.5,
        qk_norm=False,
        seed=0,
        threads=1,
        branches=3,
        lr=0.003,
        wd=0.1,
    )
    with pytest.raises(OSError, match="data"):
        e0.cmd_run(a)
    states = list((tmp_path / "runs").glob("*/status.json"))
    assert len(states) == 1 and json.loads(states[0].read_text())["state"] == "failed"
    summaries = list((tmp_path / "evidence/runs").glob("*/summary.json"))
    assert json.loads(summaries[0].read_text())["status"] == "failed"


def test_byte_repair_preserves_shape_recipe_and_rejects_second_attempt(tmp_path, monkeypatch):
    cfg = GPTConfig(d=64, n_layers=6, n_heads=4, d_ff=318, ctx=256)
    previous = fixture_run(tmp_path, "original", size=100000, target=11000000 / 16 / 8)
    previous.update(
        config=cfg.to_dict(),
        retry_count=0,
        backend_name="xbox",
        token_policy="per_parameter",
        spec={"tokens": 1234, "batch": 32, "lr": 0.001, "wd": 0.1, "seed": 3},
    )
    repaired, ratio = e0.repair_shape(previous)
    assert (repaired.d, repaired.n_layers) == (cfg.d, cfg.n_layers)
    assert repaired.d_ff < cfg.d_ff
    assert ratio == 100000 * 8 / cfg.nominal_bits()
    (tmp_path / "original").mkdir()
    monkeypatch.setattr(e0, "RUNS", tmp_path)
    monkeypatch.setattr(e0, "_summary", lambda _: previous)
    calls = []
    monkeypatch.setattr(e0, "cmd_run", lambda args: calls.append(vars(args).copy()) or 0)
    args = argparse.Namespace(retry="original")
    assert e0.cmd_retry(args) == 0
    assert calls[0]["backend"] == "xbox"
    assert calls[0]["tokens"] == 0
    assert (calls[0]["batch"], calls[0]["lr"], calls[0]["wd"], calls[0]["seed"]) == (
        32,
        0.001,
        0.1,
        3,
    )
    with pytest.raises(SystemExit, match="reservation exists"):
        e0.cmd_retry(args)
    previous["retry_count"] = 1
    with pytest.raises(SystemExit, match="at most one retry"):
        e0.repair_shape(previous)


@pytest.mark.parametrize("purpose", ["functional", "scientific"])
def test_final_test_checks_all_artifacts_before_reservation(tmp_path, monkeypatch, purpose):
    selections = tmp_path / "selections"
    selections.mkdir()
    good = tmp_path / "good.flp"
    good.write_bytes(pack(model()))
    bad = tmp_path / "bad.flp"
    bad.write_bytes(b"tampered")
    items = [
        {"run_id": "good", "artifact": str(good), "sha256": e0.runlog.sha256_file(good)},
        {"run_id": "bad", "artifact": str(bad), "sha256": "expected"},
    ]
    (selections / "a.json").write_text(json.dumps({"purpose": purpose, "items": items}))
    monkeypatch.setattr(e0, "EVIDENCE", tmp_path)
    monkeypatch.setattr(e0, "_summary", lambda _: {"data_sha256": {"test": "frozen"}})
    monkeypatch.setattr(e0.data_mod, "load", lambda *a: pytest.fail("protected data was read"))
    monkeypatch.setattr(e0, "sliding_bpb", lambda *a: pytest.fail("earlier model was evaluated"))
    with pytest.raises(SystemExit, match="artifact hash"):
        e0.cmd_final_test(argparse.Namespace(final_test="a"))
    assert not (selections / "a.test.reservation.json").exists()


def test_final_test_rejects_changed_scientific_corpus_before_reservation(tmp_path, monkeypatch):
    selections = tmp_path / "selections"
    selections.mkdir()
    artifact = tmp_path / "model.flp"
    artifact.write_bytes(pack(model()))
    (tmp_path / "test.bin").write_bytes(b"different corpus")
    selection = {
        "purpose": "scientific",
        "items": [
            {"run_id": "a", "artifact": str(artifact), "sha256": e0.runlog.sha256_file(artifact)}
        ],
    }
    (selections / "a.json").write_text(json.dumps(selection))
    monkeypatch.setattr(e0, "EVIDENCE", tmp_path)
    monkeypatch.setattr(e0, "DATA", tmp_path)
    monkeypatch.setattr(e0, "_summary", lambda _: {"data_sha256": {"test": "frozen"}})
    monkeypatch.setattr(e0.data_mod, "load", lambda *a: pytest.fail("protected data was read"))
    with pytest.raises(SystemExit, match="test corpus differs"):
        e0.cmd_final_test(argparse.Namespace(final_test="a"))
    assert not (selections / "a.test.reservation.json").exists()


def test_scientific_resume_refuses_changed_implementation_before_training(tmp_path, monkeypatch):
    run = tmp_path / "runs/frozen"
    run.mkdir(parents=True)
    (run / "xbox").mkdir()
    (run / "xbox/submitted.json").write_text("{}")
    (run / "manifest.json").write_text(
        json.dumps(
            {"backend": "xbox", "smoke": False, "sources": {"files": {"engine.py": "frozen"}}}
        )
    )
    evidence = tmp_path / "evidence/runs/frozen"
    evidence.mkdir(parents=True)
    (evidence / "summary.json").write_text('{"status": "interrupted"}')
    monkeypatch.setattr(e0, "RUNS", tmp_path / "runs")
    monkeypatch.setattr(e0, "EVIDENCE", tmp_path / "evidence")
    monkeypatch.setattr(e0.runlog, "sources", lambda _: {"files": {"engine.py": "changed"}})
    with pytest.raises(RuntimeError, match="frozen trial sources"):
        e0.cmd_resume(argparse.Namespace(resume="frozen"))


def test_resume_returns_130_when_the_native_job_is_interrupted(tmp_path, monkeypatch):
    run = tmp_path / "runs/frozen"
    (run / "xbox").mkdir(parents=True)
    (run / "xbox/submitted.json").write_text("{}")
    cfg = GPTConfig(d=32, n_layers=1, n_heads=2, d_ff=48, ctx=16)
    spec = TrainSpec(tokens=128, batch=4, lr=0.003, wd=0.1, seed=0)
    manifest = {
        "backend": "xbox",
        "smoke": False,
        "sources": {"files": {"engine.py": "frozen"}},
        "config": cfg.to_dict(),
        "spec": {
            "tokens": spec.tokens,
            "branches": spec.branches,
            "batch": spec.batch,
            "lr": spec.lr,
            "wd": spec.wd,
            "warmup_frac": spec.warmup_frac,
            "cooldown_frac": spec.cooldown_frac,
            "seed": spec.seed,
        },
        "budget_bits": 11_000_000,
        "evaluation": {"val_bytes": 256},
        "environment": {"torch_threads": 1},
        "token_policy": "fixed",
        "data": {"verified": {"prepared": "corpus"}},
    }
    (run / "manifest.json").write_text(json.dumps(manifest))
    evidence = tmp_path / "evidence/runs/frozen"
    evidence.mkdir(parents=True)
    (evidence / "summary.json").write_text('{"status": "interrupted", "branches": []}')
    monkeypatch.setattr(e0, "RUNS", tmp_path / "runs")
    monkeypatch.setattr(e0, "EVIDENCE", tmp_path / "evidence")
    monkeypatch.setattr(e0.runlog, "sources", lambda _: {"files": {"engine.py": "frozen"}})
    monkeypatch.setattr(e0.data_mod, "manifest", lambda *_: {"verified": {"prepared": "corpus"}})
    monkeypatch.setattr(e0, "TinyGPT", lambda *_: object())

    def interrupted(*_args, **_kwargs):
        raise RuntimeError("Xbox job did not complete: interrupted")

    monkeypatch.setattr(e0, "_execute_run", interrupted)
    code = e0.cmd_resume(argparse.Namespace(resume="frozen"))
    recorded = json.loads((evidence / "summary.json").read_text())
    assert code == 130
    assert recorded["status"] == "interrupted"
    assert json.loads((run / "status.json").read_text())["state"] == "interrupted"


def test_final_test_rejects_invalid_flp2_before_protected_data(tmp_path, monkeypatch):
    selections = tmp_path / "selections"
    selections.mkdir()
    artifact = tmp_path / "invalid.flp"
    artifact.write_bytes(b"invalid FLP2")
    selection = {
        "purpose": "functional",
        "items": [
            {"run_id": "a", "artifact": str(artifact), "sha256": e0.runlog.sha256_file(artifact)}
        ],
    }
    (selections / "a.json").write_text(json.dumps(selection))
    monkeypatch.setattr(e0, "EVIDENCE", tmp_path)
    monkeypatch.setattr(e0.data_mod, "load", lambda *a: pytest.fail("protected data was read"))
    with pytest.raises(FormatError):
        e0.cmd_final_test(argparse.Namespace(final_test="a"))
    assert not (selections / "a.test.reservation.json").exists()
