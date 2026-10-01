"""Read-only campaign diagnostics must distinguish reservation from hardware evidence."""

import importlib.util
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("e0_status", ROOT / "scripts/e0_status.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


@pytest.fixture
def campaign(tmp_path):
    path = tmp_path / "campaign"
    path.mkdir()
    (path / "campaign.json").write_text(
        json.dumps(
            {
                "id": "campaign",
                "status": "running",
                "phase": "neutral-scale",
                "package": "package",
                "commit": "commit",
                "sources": {"files": {}},
                "trials": {"first": {"run_id": "trial", "status": "reserved"}},
            }
        )
    )
    return path


def test_reservation_does_not_claim_hardware_progress(campaign, tmp_path):
    result = module.report(campaign, workspace=tmp_path)
    assert result["trial"]["console_state"] == "waiting_for_submission"
    assert "console" not in result["trial"]
    assert not result["issues"]


def test_source_added_after_freeze_is_detected(campaign, tmp_path):
    source = tmp_path / "experiments"
    source.mkdir()
    (source / "new.py").write_text("# Changed implementation\n")
    result = module.report(campaign, workspace=tmp_path)
    assert result["source_drift"] == ["experiments/new.py"]
    assert result["issues"]


def test_live_provenance_mismatch_is_reported_without_writes(campaign, tmp_path):
    submitted = tmp_path / "runs/trial/xbox"
    submitted.mkdir(parents=True)
    (submitted / "submitted.json").write_text(json.dumps({"package": "package", "sha256": "bound"}))
    portal = Mock(spec=["get", "status", "worker"])
    portal.get.return_value = json.dumps({"package": "different", "commit": "commit"}).encode()
    portal.status.return_value = {"state": "running", "job_sha256": "wrong", "hardware_gpu": False}
    portal.worker.side_effect = RuntimeError("worker contract unavailable")
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    result = module.report(campaign, workspace=tmp_path, portal=portal)
    assert len(result["issues"]) == 4
    assert before == {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert [call[0] for call in portal.mock_calls] == ["get", "status", "worker"]


@pytest.mark.parametrize("state", ["failed", "interrupted"])
def test_interrupted_or_failed_console_is_not_reported_as_healthy(campaign, tmp_path, state):
    submitted = tmp_path / "runs/trial/xbox"
    submitted.mkdir(parents=True)
    (submitted / "submitted.json").write_text(json.dumps({"package": "package", "sha256": "bound"}))
    portal = Mock(spec=["get", "status", "worker"])
    portal.get.return_value = json.dumps({"package": "package", "commit": "commit"}).encode()
    portal.status.return_value = {"state": state, "job_sha256": "bound", "hardware_gpu": True}
    result = module.report(campaign, workspace=tmp_path, portal=portal)
    assert result["trial"]["console"]["state"] == state
    assert result["issues"] == ["Console trial requires diagnosis or explicit recovery"]


@pytest.fixture
def live_portal(tmp_path):
    submitted = tmp_path / "runs/trial/xbox"
    submitted.mkdir(parents=True)
    (submitted / "submitted.json").write_text(
        json.dumps({"package": "package", "sha256": "a" * 64})
    )
    portal = Mock(spec=["get", "status", "worker"])
    portal.get.return_value = json.dumps({"package": "package", "commit": "commit"}).encode()
    portal.status.return_value = {
        "state": "running",
        "job_sha256": "a" * 64,
        "hardware_gpu": True,
        "trunk_step": 32,
        "cooldown_step": 0,
        "phase": "trunk",
        "branches": [],
    }
    portal.worker.return_value = {
        "schema": "floppylm.worker.v1",
        "worker_id": "instance",
        "pid": 15,
        "package": "package",
        "commit": "commit",
        "state": "running",
        "heartbeat_seq": 1,
        "active_job": {"job_id": "trial", "job_sha256": "a" * 64},
        "fault": None,
        "progress": {
            "sequence": 1,
            "trunk_step": 32,
            "cooldown_step": 0,
            "phase": "trunk",
            "operation": "train",
            "completed_fence": 5,
        },
    }
    return portal


def test_single_snapshot_cannot_prove_liveness_or_progress(campaign, tmp_path, live_portal):
    result = module.report(campaign, workspace=tmp_path, portal=live_portal)
    assert result["host_liveness"] == "unknown"
    assert result["trial"]["runtime"]["liveness"] == "unverified"
    assert result["trial"]["runtime"]["progress"] == "unverified"
    assert result["provenance"] == {"sources": "matching", "device": "matching"}


def test_heartbeat_does_not_reset_progress_clock(campaign, tmp_path, live_portal):
    monitors = {}
    module.report(
        campaign, workspace=tmp_path, portal=live_portal, monitors=monitors, observed_at=0
    )
    live_portal.worker.return_value["heartbeat_seq"] = 2
    result = module.report(
        campaign, workspace=tmp_path, portal=live_portal, monitors=monitors, observed_at=600
    )
    assert result["trial"]["runtime"]["liveness"] == "live"
    assert result["trial"]["runtime"]["progress"] == "stalled"
    assert "no_progress" in result["issues"]
    live_portal.status.return_value["trunk_step"] = 64
    live_portal.worker.return_value["progress"].update(sequence=2, completed_fence=6)
    result = module.report(
        campaign, workspace=tmp_path, portal=live_portal, monitors=monitors, observed_at=601
    )
    assert result["trial"]["runtime"]["progress"] == "observed"
    assert "no_progress" in result["trial"]["runtime"]["cleared"]


def test_unchanged_heartbeat_becomes_unavailable(campaign, tmp_path, live_portal):
    monitors = {}
    module.report(
        campaign, workspace=tmp_path, portal=live_portal, monitors=monitors, observed_at=0
    )
    result = module.report(
        campaign, workspace=tmp_path, portal=live_portal, monitors=monitors, observed_at=30
    )
    assert result["trial"]["runtime"]["liveness"] == "unavailable"
    assert "worker_heartbeat_stalled" in result["issues"]


@pytest.mark.parametrize("method", ["get", "status", "worker"])
def test_transport_error_is_unknown_not_dead(campaign, tmp_path, live_portal, method):
    getattr(live_portal, method).side_effect = TimeoutError("unreachable")
    result = module.report(campaign, workspace=tmp_path, portal=live_portal)
    if method == "get":
        assert result["provenance"]["device"] == "unknown"
    else:
        assert result["trial"]["runtime"]["liveness"] == "unknown"
    assert any("transport unknown" in issue for issue in result["issues"])


def test_legacy_runtime_is_unavailable(campaign, tmp_path, live_portal):
    live_portal.worker.side_effect = RuntimeError("new runtime acceptance required")
    result = module.report(campaign, workspace=tmp_path, portal=live_portal)
    assert result["trial"]["runtime"]["liveness"] == "unavailable"
    assert "Worker runtime contract unavailable" in result["issues"]


def test_watch_persists_alarm_once_and_bounds_duration(campaign, tmp_path, live_portal):
    elapsed = [0.0]

    def sleep(seconds):
        elapsed[0] += seconds
        live_portal.worker.return_value["heartbeat_seq"] += 1

    emitted = []
    output = tmp_path / "observations/events.jsonl"
    result = module.watch(
        campaign,
        workspace=tmp_path,
        portal=live_portal,
        interval=400,
        duration=1000,
        observations=output,
        clock=lambda: elapsed[0],
        sleep=sleep,
        emit=emitted.append,
    )
    records = [json.loads(line) for line in output.read_text().splitlines()]
    assert elapsed[0] == 1000
    assert [r["elapsed_seconds"] for r in records] == [0, 400, 800, 1000]
    assert sum("no_progress" in r["events"] for r in records) == 1
    assert records[-1]["trial"]["runtime"]["progress"] == "stalled"
    assert json.loads(output.with_suffix(".json").read_text()) == records[-1]
    assert result == 1
    assert len(emitted) == 4


def test_mismatched_host_lock_owner_is_an_issue(campaign, tmp_path, monkeypatch):
    monkeypatch.setattr(module.runlog, "host_liveness", lambda *_: "lock_owner_mismatch")
    result = module.report(campaign, workspace=tmp_path)
    assert result["host_liveness"] == "lock_owner_mismatch"
    assert "Campaign host is not a live lock owner" in result["issues"]


def test_watch_json_filename_preserves_journal(campaign, tmp_path):
    elapsed = [0.0]

    def sleep(seconds):
        elapsed[0] += seconds

    output = tmp_path / "observations.json"
    module.watch(
        campaign,
        workspace=tmp_path,
        duration=1,
        observations=output,
        clock=lambda: elapsed[0],
        sleep=sleep,
        emit=lambda _: None,
    )
    records = [json.loads(line) for line in output.read_text().splitlines()]
    assert len(records) == 2
    assert json.loads(output.with_suffix(".latest.json").read_text()) == records[-1]
