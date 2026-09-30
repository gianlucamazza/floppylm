"""Transport invariants: content binding, package provenance and stale resume state."""

import hashlib
import json
from unittest.mock import Mock

import pytest

from floppylm.xbox_portal import Portal


def portal():
    return Portal("https://127.0.0.1:11443", "test", "test", "test-package")


def test_asset_chunks_reused_and_download_hash_verified(tmp_path):
    client = portal()
    client.upload = Mock()
    source = tmp_path / "data.bin"
    source.write_bytes(b"corpus")
    digest = hashlib.sha256(b"corpus").hexdigest()
    descriptor = client.asset(source, {digest + ".chunk": 6})
    client.upload.assert_not_called()
    assert descriptor["chunks"][0]["sha256"] == digest
    client.get = Mock(return_value=b"changed")
    with pytest.raises(RuntimeError, match="integrity"):
        client.retrieve(descriptor, tmp_path / "result")
    assert not (tmp_path / "result").exists()


def test_scientific_submit_rejects_different_source_commit(tmp_path):
    client = portal()
    client.get = Mock(
        return_value=json.dumps(
            {
                "state": "ready",
                "hardware_gpu": True,
                "package": client.package,
                "commit": "new",
            }
        ).encode()
    )
    proof = tmp_path / "acceptance.json"
    proof.write_text(
        json.dumps(
            {
                "schema": "floppylm.xbox.acceptance.v1",
                "ok": True,
                "package": client.package,
                "commit": "old",
                "kernels": {"ok": True},
            }
        )
    )
    with pytest.raises(RuntimeError, match="source commit"):
        client.submit(tmp_path, purpose="scientific", acceptance=proof)


def test_resume_wait_ignores_previous_interrupted_status(monkeypatch):
    client = portal()
    client.status = Mock(
        side_effect=[
            {"state": "interrupted", "job_sha256": "old"},
            {"state": "running", "job_sha256": "new", "trunk_step": 9},
            {"state": "completed", "job_sha256": "new", "trunk_step": 29},
        ]
    )
    monkeypatch.setattr("floppylm.xbox_portal.time.sleep", lambda _: None)
    assert client.wait("job", log=lambda _: None, expected_sha="new")["state"] == "completed"


def test_remote_artifact_cannot_escape_inbox(tmp_path):
    with pytest.raises(ValueError, match="escapes"):
        portal().retrieve({"path": "../private", "bytes": 1, "sha256": "unused"}, tmp_path / "out")


def test_existing_connection_config_is_sourced_without_shell_quote_breakage(tmp_path, monkeypatch):
    config = tmp_path / ".config/xllama/xbox-env"
    config.parent.mkdir(parents=True)
    config.write_text("XBOX_IP=127.0.0.1\nXBOX_USER=test\nXBOX_PASS='test $literal'\n")
    for key in ("XBOX_IP", "XBOX_USER", "XBOX_PASS"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr("floppylm.xbox_portal.Path.home", lambda: tmp_path)
    client = Portal.configured(package="known")
    assert client.host == "127.0.0.1"
    assert client.package == "known"
