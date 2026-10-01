"""Critical orchestration guards: fixed provenance, exclusive worker and no replay."""

import importlib.util
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def campaign_module(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "experiments"))
    spec = importlib.util.spec_from_file_location(
        "campaign_test", ROOT / "experiments/e0_campaign.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def inputs(tmp_path):
    proof = tmp_path / "acceptance.json"
    proof.write_text(json.dumps({"ok": True, "package": "package", "commit": "source"}))
    benchmark = tmp_path / "benchmark.json"
    benchmark.write_text(json.dumps({"package": "package", "commit": "source"}))
    return proof, benchmark


def test_campaign_freezes_protocol_and_disallows_second_worker(tmp_path, campaign_module):
    proof, speed = inputs(tmp_path)
    first = campaign_module.Campaign(tmp_path / "campaign", proof, speed)
    state = json.loads(first.path.read_text())
    assert state["trials"] == {}
    assert state["protocol_adr"] == "0015"
    assert state["protocol"]["scale_order"] == ["row16", "row8log"]
    assert state["protocol"]["paired_seeds"] == [0, 1, 2, 3, 4]
    with pytest.raises(BlockingIOError):
        campaign_module.Campaign(tmp_path / "campaign", proof, speed)
    first.lock.close()
    proof.write_text(json.dumps({"ok": True, "package": "package", "commit": "different"}))
    with pytest.raises(RuntimeError, match="same hardware package"):
        campaign_module.Campaign(tmp_path / "campaign", proof, speed)


def test_existing_0011_campaign_is_not_migrated(tmp_path, campaign_module):
    proof, speed = inputs(tmp_path)
    first = campaign_module.Campaign(tmp_path / "campaign", proof, speed)
    first.state["protocol_adr"] = "0011"
    first.save()
    first.lock.close()
    with pytest.raises(RuntimeError, match="no implicit migration"):
        campaign_module.Campaign(tmp_path / "campaign", proof, speed)


def test_interrupted_trial_is_not_silently_retrained(tmp_path, monkeypatch, campaign_module):
    proof, speed = inputs(tmp_path)
    campaign = campaign_module.Campaign(tmp_path / "campaign", proof, speed)
    run_dir = tmp_path / "evidence/runs/fixed"
    run_dir.mkdir(parents=True)
    (run_dir / "summary.json").write_text(json.dumps({"status": "interrupted"}))
    monkeypatch.setattr(campaign_module, "EVIDENCE", tmp_path / "evidence")
    monkeypatch.setitem(campaign_module._summary.__globals__, "EVIDENCE", tmp_path / "evidence")

    def interrupted(_):
        raise SystemExit("fixed is interrupted, not completed")

    monkeypatch.setattr(campaign_module, "_summary", interrupted)
    process = Mock()
    monkeypatch.setattr(campaign, "run_command", process)
    with pytest.raises(SystemExit, match="interrupted"):
        campaign.execute("fixed", ["unused"])
    process.assert_not_called()
    campaign.lock.close()


def test_campaign_recovery_uses_resume_instead_of_fresh_training(
    tmp_path, monkeypatch, campaign_module
):
    proof, speed = inputs(tmp_path)
    campaign = campaign_module.Campaign(tmp_path / "campaign", proof, speed, recover=True)
    run_dir = tmp_path / "evidence/runs/fixed"
    run_dir.mkdir(parents=True)
    path = run_dir / "summary.json"
    path.write_text(json.dumps({"status": "interrupted"}))
    monkeypatch.setattr(campaign_module, "EVIDENCE", tmp_path / "evidence")
    monkeypatch.setitem(campaign_module._summary.__globals__, "EVIDENCE", tmp_path / "evidence")
    completed = {
        "run_id": "fixed",
        "status": "completed",
        "backend_name": "xbox",
        "backend": {"hardware_gpu": True},
    }

    def process(cmd, **kwargs):
        assert "--resume" in cmd and "fixed" in cmd and "--run" not in cmd
        path.write_text(json.dumps(completed))

    monkeypatch.setattr(campaign, "run_command", process)
    monkeypatch.setattr(campaign_module, "selection_branch", lambda _: {})
    monkeypatch.setattr(campaign_module, "verified_branch", lambda _: {})
    assert campaign.execute("fixed", ["fresh-training"]) == completed
    campaign.lock.close()


def test_final_report_reads_seed_metadata_from_bound_trial_summaries(
    tmp_path, monkeypatch, campaign_module
):
    proof, speed = inputs(tmp_path)
    campaign = campaign_module.Campaign(tmp_path / "campaign", proof, speed)
    evidence = tmp_path / "evidence"
    monkeypatch.setattr(campaign_module, "EVIDENCE", evidence)
    monkeypatch.setitem(campaign_module._summary.__globals__, "EVIDENCE", evidence)
    (evidence / "selections").mkdir(parents=True)
    campaign.state.update(status="completed", selection="frozen", paired={"gate_bpb": 0.02})
    results = []
    for fmt in ("ternary", "2bit"):
        for seed in range(5):
            run_id = fmt + str(seed)
            directory = evidence / "runs" / run_id
            directory.mkdir(parents=True)
            (directory / "summary.json").write_text(
                json.dumps(
                    {"status": "completed", "config": {"core_fmt": fmt}, "spec": {"seed": seed}}
                )
            )
            results.append({"run_id": run_id, "test_bpb": 1.0 if fmt == "ternary" else 1.1})
    (evidence / "selections/frozen.json").write_text(json.dumps({"items": results}))
    (evidence / "selections/frozen.test.json").write_text(json.dumps({"results": results}))
    campaign.report()
    report = json.loads((campaign.root / "summary.json").read_text())
    assert report["test_paired"]["n"] == 5
    assert report["test_paired"]["mean"] == pytest.approx(-0.1)
    assert report["frozen_gate_bpb"] == 0.02
    campaign.lock.close()


def _branches(bpb_t, bpb_2t, bpb_4t, size=1000):
    return [
        {"model_bytes": size, "val_bpb": bpb_t},
        {"model_bytes": size, "val_bpb": bpb_2t},
        {"model_bytes": size, "val_bpb": bpb_4t},
    ]


def _summary_run(run_id, bpb_t, bpb_2t, bpb_4t, size=1000, verdict="non saturo"):
    return {
        "run_id": run_id,
        "target_bytes": size,
        "saturation": {"verdict": verdict},
        "branches": _branches(bpb_t, bpb_2t, bpb_4t, size),
    }


def test_unsaturated_byte_ok_trial_is_eligible(tmp_path, monkeypatch, campaign_module):
    proof, speed = inputs(tmp_path)
    campaign = campaign_module.Campaign(tmp_path / "campaign", proof, speed)
    summary = _summary_run("trial", 1.5, 1.4, 1.32)
    monkeypatch.setattr(campaign, "execute", lambda *a: summary)
    monkeypatch.setattr(campaign_module, "selection_branch", lambda s: s["branches"][2])
    cfg = campaign_module.GPTConfig(d=32, n_layers=1, n_heads=2, d_ff=48, ctx=16)
    assert campaign.trial("k", cfg, 0) is summary
    assert campaign.state["trials"]["k"]["status"] == "eligible"
    campaign.lock.close()


def test_rank_stable_accepts_shared_minimizer(campaign_module):
    valid = [
        (0, [_summary_run("a0", 1.4, 1.3, 1.2), _summary_run("a1", 1.42, 1.32, 1.22)]),
        (1, [_summary_run("b0", 1.5, 1.4, 1.3), _summary_run("b1", 1.52, 1.42, 1.32)]),
    ]
    assert campaign_module.Campaign.rank_stable("neutral-scale", valid) == 0


def test_rank_stable_rejects_flip(campaign_module):
    valid = [
        (0, [_summary_run("a0", 1.5, 1.3, 1.2), _summary_run("a1", 1.52, 1.32, 1.22)]),
        (1, [_summary_run("b0", 1.4, 1.4, 1.3), _summary_run("b1", 1.42, 1.42, 1.32)]),
    ]
    with pytest.raises(RuntimeError, match="rank unstable"):
        campaign_module.Campaign.rank_stable("neutral-scale", valid)


def test_paired_rank_stable_requires_matching_sign(campaign_module):
    stable = {
        "ternary": [_summary_run("t0", 1.4, 1.3, 1.2)],
        "2bit": [_summary_run("b0", 1.5, 1.4, 1.3)],
    }
    campaign_module.Campaign.paired_rank_stable(stable)
    flipped = {
        "ternary": [_summary_run("t0", 1.6, 1.3, 1.2)],
        "2bit": [_summary_run("b0", 1.5, 1.4, 1.3)],
    }
    with pytest.raises(RuntimeError, match="rank unstable at T"):
        campaign_module.Campaign.paired_rank_stable(flipped)
