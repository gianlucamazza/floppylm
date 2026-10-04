"""Acceptance observation must prove the real timeout, ownership and exact recovery."""

import importlib.util
from pathlib import Path

import pytest

from test_xbox_portal import worker


@pytest.fixture
def acceptance(monkeypatch):
    path = Path(__file__).resolve().parents[1] / "experiments/xbox_watchdog_acceptance.py"
    spec = importlib.util.spec_from_file_location("watchdog_acceptance", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "duration, advancing, succeeds", [(604, True, True), (30, True, False), (604, False, False)]
)
def test_observation_rejects_early_exit_or_frozen_heartbeat(
    tmp_path, acceptance, duration, advancing, succeeds
):
    now = [0.0]
    sha = "a" * 64

    class Portal:
        def worker(self, **kwargs):
            return worker("probe", sha, 1 + int(now[0]) if advancing else 1)

    def observe():
        return acceptance.observe_exit(
            Portal(),
            "probe",
            sha,
            "source",
            tmp_path,
            clock=lambda: now[0],
            sleep=lambda n: now.__setitem__(0, now[0] + n),
            processes=lambda _: [{}] if now[0] < duration else [],
        )

    if succeeds:
        result = observe()
        assert result["elapsed_seconds"] == 604
        assert result["process_exited"] and result["heartbeat_advanced"]
    else:
        with pytest.raises(RuntimeError):
            observe()


@pytest.mark.parametrize(
    "field,value",
    [
        ("kind", "gpu_wait_timeout"),
        ("error", "published GPU fence frozen"),
        ("elapsed_ms", 1),
        ("requested_fence", 4),
    ],
)
def test_fault_must_be_the_published_fence_watchdog(acceptance, field, value):
    fault = {
        "kind": "progress_stall",
        "error": "published progress frozen without an in-flight GPU request",
        "requested_fence": 0,
        "elapsed_ms": 600000,
    }
    status = {
        "state": "interrupted",
        "job_sha256": "a" * 64,
        "checkpoint": {"sha256": "b" * 64},
        "runtime_fault": fault,
    }
    acceptance.verify_fault(status, "a" * 64)
    fault[field] = value
    with pytest.raises(RuntimeError, match="evidence"):
        acceptance.verify_fault(status, "a" * 64)


def test_recovery_compares_optimizer_and_artifacts(acceptance):
    result = {"branches": [{"artifact": {"sha256": str(i)}} for i in range(3)]}
    checkpoint = {"step": 10, "stream_position": 10, "tensors": [1], "moments": [2]}
    assert acceptance.compare_results(result, result, checkpoint, checkpoint)
    assert not acceptance.compare_results(
        result, result, checkpoint, {**checkpoint, "moments": [3]}
    )


def test_pending_inbox_work_refuses_qualification(acceptance):
    class Portal:
        def files(self):
            return {"science.ready": 5}

    with pytest.raises(RuntimeError, match="pending"):
        acceptance.protected_snapshot(Portal())


def test_observation_refuses_an_unrelated_owner(tmp_path, acceptance):
    class Portal:
        def worker(self, **kwargs):
            return worker("another-job", "a" * 64)

    with pytest.raises(RuntimeError, match="exact job owner"):
        acceptance.observe_exit(
            Portal(),
            "probe",
            "a" * 64,
            "source",
            tmp_path,
            clock=lambda: 0,
            sleep=lambda _: None,
            processes=lambda _: [{}],
        )


def test_protection_hashes_bound_science_without_downloading_archived_fixtures(acceptance):
    class Portal:
        def files(self):
            return {"science.job.json": 20, "old-fixture.job.json": 10000000, "data.chunk": 99}

        def get(self, name):
            assert name == "science.job.json"
            return b'{"job_id":"science","purpose":"scientific"}'

        def status(self, job_id):
            assert job_id == "science"
            return {"state": "interrupted", "checkpoint": {"sha256": "a" * 64}}

    result = acceptance.protected_snapshot(Portal(), job_ids={"science"})
    assert "sha256" in result["science.job.json"]
    assert result["science.job.json"]["scientific_status"]["state"] == "interrupted"
    assert result["old-fixture.job.json"] == {"bytes": 10000000}
