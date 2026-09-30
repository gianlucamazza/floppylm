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
    assert state["protocol"]["paired_seeds"] == [0, 1, 2, 3, 4]
    with pytest.raises(BlockingIOError):
        campaign_module.Campaign(tmp_path / "campaign", proof, speed)
    first.lock.close()
    proof.write_text(json.dumps({"ok": True, "package": "package", "commit": "different"}))
    with pytest.raises(RuntimeError, match="same hardware package"):
        campaign_module.Campaign(tmp_path / "campaign", proof, speed)


def test_interrupted_trial_is_not_silently_retrained(tmp_path, monkeypatch, campaign_module):
    proof, speed = inputs(tmp_path)
    campaign = campaign_module.Campaign(tmp_path / "campaign", proof, speed)
    run_dir = tmp_path / "evidence/runs/fixed"
    run_dir.mkdir(parents=True)
    (run_dir / "summary.json").write_text(json.dumps({"status": "interrupted"}))
    monkeypatch.setattr(campaign_module, "EVIDENCE", tmp_path / "evidence")

    def interrupted(_):
        raise SystemExit("fixed is interrupted, not completed")

    monkeypatch.setattr(campaign_module, "_summary", interrupted)
    process = Mock()
    monkeypatch.setattr(campaign_module.subprocess, "run", process)
    with pytest.raises(SystemExit, match="interrupted"):
        campaign.execute("fixed", ["unused"])
    process.assert_not_called()
    campaign.lock.close()
