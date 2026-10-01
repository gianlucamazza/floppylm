"""Temporal evidence and strict ownership at the host recovery boundary."""

import json
from unittest.mock import Mock

import pytest

from floppylm_xbox.runtime import RuntimeMonitor, validate_worker
from test_xbox_portal import portal, recovery_job, worker

SHA = "a" * 64


def sample(seq=1):
    return worker("job", SHA, seq)


def report(**fields):
    return {"state": "running", "job_sha256": SHA, "trunk_step": 64, **fields}


def test_snapshot_cannot_prove_liveness_or_progress():
    got = RuntimeMonitor("job", SHA).observe(report(), sample(), 0)
    assert (got["liveness"], got["progress"]) == ("unverified", "unverified")


def test_heartbeats_are_not_work_and_stall_alarm_is_edge_triggered():
    monitor = RuntimeMonitor("job", SHA)
    monitor.observe(report(), sample(), 0)
    got = monitor.observe(report(), sample(2), 600)
    assert (got["liveness"], got["progress"]) == ("live", "stalled")
    assert got["events"] == ["no_progress"]
    assert not monitor.observe(report(), sample(3), 605)["events"]
    advanced = sample(4)
    advanced["progress"]["sequence"] = 1
    got = monitor.observe(report(cooldown_step=65), advanced, 610)
    assert got["progress"] == "observed"
    assert got["cleared"] == ["no_progress"]


def test_stale_heartbeat_and_owner_changes_never_prove_liveness():
    monitor = RuntimeMonitor("job", SHA)
    monitor.observe(report(), sample(), 0)
    assert monitor.observe(report(), sample(), 30)["events"] == ["worker_heartbeat_stalled"]
    changed = sample(2)
    changed["worker_id"] = "new-instance"
    assert "worker_instance_changed" in monitor.observe(report(), changed, 31)["issues"]
    changed["heartbeat_seq"] = 3
    assert monitor.observe(report(), changed, 36)["liveness"] == "unavailable"


def test_progress_counter_regression_does_not_clear_stall():
    monitor = RuntimeMonitor("job", SHA)
    w = sample()
    w["progress"]["sequence"] = 4
    monitor.observe(report(), w, 0)
    w["progress"]["sequence"] = 3
    w["heartbeat_seq"] = 2
    got = monitor.observe(report(), w, 600)
    assert {"progress_sequence_regressed", "no_progress"} <= set(got["issues"])


@pytest.mark.parametrize(
    "edit",
    [
        lambda w: w.update(package="other"),
        lambda w: w.update(commit="other"),
        lambda w: w.update(pid=True),
        lambda w: w.pop("fault"),
        lambda w: w["progress"].update(sequence=-1),
        lambda w: w["active_job"].update(job_sha256="bad"),
    ],
)
def test_worker_contract_cannot_authorize_recovery_when_malformed(edit):
    w = sample()
    edit(w)
    with pytest.raises(RuntimeError):
        validate_worker(w, "test-package", "source")


def test_live_worker_requires_advancing_same_instance_heartbeat(monkeypatch):
    client = portal()
    client.worker = Mock(side_effect=[worker(heartbeat=1), worker(heartbeat=2)])
    monkeypatch.setattr("floppylm_xbox.portal.time.sleep", lambda _: None)
    assert client.live_worker()["heartbeat_seq"] == 2
    client.worker = Mock(side_effect=[worker(), {**worker(heartbeat=2), "worker_id": "other"}])
    with pytest.raises(RuntimeError, match="instance"):
        client.live_worker()


def test_live_worker_stale_document_is_not_a_live_process(monkeypatch):
    client = portal()
    client.worker = Mock(return_value=worker())
    clock = iter(range(0, 100, 10))
    monkeypatch.setattr("floppylm_xbox.portal.time.monotonic", lambda: next(clock))
    monkeypatch.setattr("floppylm_xbox.portal.time.sleep", lambda _: None)
    with pytest.raises(TimeoutError, match="heartbeat"):
        client.live_worker()


@pytest.mark.parametrize("owner", [worker(), worker("another", SHA)])
def test_stale_running_report_cannot_be_reattached(tmp_path, owner):
    client = portal()
    recovery_job(tmp_path, client, "running")
    client.live_worker = Mock(return_value=owner)
    with pytest.raises(RuntimeError, match="orphan"):
        client.recover(tmp_path, purpose="functional", acceptance=None)
    client.resume.assert_not_called()
    client.submit.assert_not_called()


def test_interrupted_recovery_requires_idle_worker(tmp_path):
    client = portal()
    recovery_job(tmp_path, client, "interrupted")
    client.live_worker = Mock(return_value=worker("another", SHA))
    with pytest.raises(RuntimeError, match="idle"):
        client.recover(tmp_path, purpose="functional", acceptance=None)
    client.retrieve.assert_not_called()
    client.resume.assert_not_called()


def test_wait_persists_stall_and_clears_without_cancel(tmp_path, monkeypatch):
    client = portal()
    records = [report(), report(), report(cooldown_step=65), report(state="completed")]
    client.status = Mock(side_effect=records)
    client.worker = Mock(side_effect=[sample(), sample(2), sample(3)])
    client.cancel = Mock()
    now = [0.0]
    monkeypatch.setattr("floppylm_xbox.portal.time.monotonic", lambda: now[0])
    monkeypatch.setattr(
        "floppylm_xbox.portal.time.sleep", lambda _: now.__setitem__(0, now[0] + 601)
    )
    root = tmp_path / "observations"
    assert (
        client.wait("job", expected_sha=SHA, observation_dir=root, log=lambda _: None)["state"]
        == "completed"
    )
    events = [json.loads(line) for line in (root / "runtime-events.jsonl").read_text().splitlines()]
    assert sum(e["event"] == "no_progress" for e in events) == 1
    assert any(e.get("alarm") == "no_progress" for e in events)
    assert json.loads((root / "runtime.json").read_text())["progress"] == "observed"
    client.cancel.assert_not_called()


def test_missing_worker_contract_is_explicitly_unavailable():
    client = portal()
    client.get = Mock(side_effect=FileNotFoundError)
    with pytest.raises(RuntimeError, match="acceptance"):
        client.worker()


def test_transport_failure_persists_unknown_not_dead(tmp_path):
    client = portal()
    client._runtime_event(tmp_path, {"event": "worker_transport_unknown"}, lambda _: None)
    assert json.loads((tmp_path / "runtime.json").read_text())["liveness"] == "unknown"


def test_busy_worker_refuses_fixture_before_upload():
    client = portal()
    client.live_worker = Mock(return_value=sample())
    client.upload = Mock()
    with pytest.raises(RuntimeError, match="idle"):
        client.fixture({}, "fixture")
    client.upload.assert_not_called()
