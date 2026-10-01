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
    portal = Mock(spec=["get", "status"])
    portal.get.return_value = json.dumps({"package": "different", "commit": "commit"}).encode()
    portal.status.return_value = {"state": "running", "job_sha256": "wrong", "hardware_gpu": False}
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    result = module.report(campaign, workspace=tmp_path, portal=portal)
    assert len(result["issues"]) == 3
    assert before == {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert [call[0] for call in portal.mock_calls] == ["get", "status"]


@pytest.mark.parametrize("state", ["failed", "interrupted"])
def test_interrupted_or_failed_console_is_not_reported_as_healthy(campaign, tmp_path, state):
    submitted = tmp_path / "runs/trial/xbox"
    submitted.mkdir(parents=True)
    (submitted / "submitted.json").write_text(json.dumps({"package": "package", "sha256": "bound"}))
    portal = Mock(spec=["get", "status"])
    portal.get.return_value = json.dumps({"package": "package", "commit": "commit"}).encode()
    portal.status.return_value = {"state": state, "job_sha256": "bound", "hardware_gpu": True}
    result = module.report(campaign, workspace=tmp_path, portal=portal)
    assert result["trial"]["console"]["state"] == state
    assert result["issues"] == ["Console trial requires diagnosis or explicit recovery"]
