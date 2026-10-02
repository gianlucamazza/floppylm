"""Explicit recover starts a missing process once and never kills a live one."""

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from floppylm_xbox.portal import Portal

ROOT = Path(__file__).resolve().parents[1]
PIN = "c098b8239dad720ba440e13db6b181b86bcb71242645824b4ef0eaf0dd428d22"
spec = importlib.util.spec_from_file_location("e0_recover", ROOT / "scripts/e0_recover.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def portal():
    return Portal("https://127.0.0.1:11443", "user", "pass", "pkg", cert_sha256=PIN)


def processes(*names):
    return {
        "Processes": [
            {"ImageName": name, "PackageFullName": "pkg"} for name in names
        ]
    }


def idle_worker():
    return {
        "state": "ready",
        "active_job": None,
        "heartbeat_seq": 2,
        "package": "pkg",
        "commit": "source",
    }


def test_app_processes_match_package_or_image(monkeypatch):
    client = portal()
    client.request = Mock(
        return_value={
            "Processes": [
                {"ImageName": "DevHome.exe", "PackageFullName": "other"},
                {"ImageName": "XgpuE0.exe", "PackageFullName": "pkg"},
            ]
        }
    )
    found = module.app_processes(client)
    assert [p["ImageName"] for p in found] == ["XgpuE0.exe"]


def test_start_package_is_noop_when_process_listed():
    client = portal()
    client.request = Mock(return_value=processes("XgpuE0.exe"))
    run = Mock()
    assert module.start_package(client, run=run) == "already_running"
    run.assert_not_called()


def test_start_package_uses_openappx_not_taskmanager(monkeypatch):
    client = portal()
    listing = iter([processes(), processes(), processes("XgpuE0.exe")])
    client.request = Mock(side_effect=lambda *a, **k: next(listing))
    monkeypatch.setenv("XBOX_PASS", "secret")
    monkeypatch.setenv("XBOX_USER", "user")
    monkeypatch.setenv("XBOX_CERT_SHA256", PIN)
    monkeypatch.setattr(module.time, "monotonic", Mock(side_effect=[0, 1, 2]))
    monkeypatch.setattr(module.time, "sleep", lambda _: None)
    run = Mock(return_value=SimpleNamespace(returncode=0, stdout="ok", stderr=""))
    assert module.start_package(client, run=run, which=lambda _: "/bin/openappx") == "started"
    command = run.call_args.args[0]
    assert command[0] == "/bin/openappx"
    assert command[1:3] == ["deploy", "--device"]
    assert "--start" in command and "pkg" in command
    assert "/api/taskmanager/app" not in " ".join(command)
    assert run.call_args.kwargs["env"]["OPENAPPX_DEVICE_PASSWORD"] == "secret"


def test_prepare_idle_worker_starts_only_when_missing(monkeypatch):
    client = portal()
    client.live_worker = Mock(return_value=idle_worker())
    client.request = Mock(return_value=processes())
    started = Mock(return_value="started")
    monkeypatch.setattr(module, "start_package", started)
    assert module.prepare_idle_worker(client, restart_if_missing=True)["state"] == "ready"
    started.assert_called_once()
    client.request = Mock(return_value=processes("XgpuE0.exe"))
    started.reset_mock()
    assert module.prepare_idle_worker(client, restart_if_missing=True)["state"] == "ready"
    started.assert_not_called()


def test_prepare_idle_worker_refuses_silent_restart_when_missing():
    client = portal()
    client.request = Mock(return_value=processes())
    client.live_worker = Mock()
    with pytest.raises(RuntimeError, match="explicit app restart"):
        module.prepare_idle_worker(client, restart_if_missing=False)
    client.live_worker.assert_not_called()


def test_prepare_campaign_runtime_binds_package_and_idle_worker(tmp_path, monkeypatch):
    out = tmp_path / "campaign"
    out.mkdir()
    (out / "campaign.json").write_text(
        json.dumps({"package": "pkg", "commit": "source", "id": "c"})
    )
    proof = tmp_path / "acceptance.json"
    proof.write_text(json.dumps({"ok": True, "package": "pkg", "commit": "source"}))
    speed = tmp_path / "benchmark.json"
    speed.write_text(json.dumps({"package": "pkg", "commit": "source"}))
    client = portal()
    client.get = Mock(
        return_value=json.dumps(
            {
                "package": "pkg",
                "commit": "source",
                "hardware_gpu": True,
                "state": "ready",
            }
        ).encode()
    )
    client.request = Mock(return_value=processes("XgpuE0.exe"))
    client.live_worker = Mock(return_value=idle_worker())
    got = module.prepare_campaign_runtime(out, proof, speed, portal=client)
    assert got["process_was_missing"] is False
    assert got["worker"]["state"] == "ready"


def test_prepare_campaign_runtime_rejects_package_drift(tmp_path):
    out = tmp_path / "campaign"
    out.mkdir()
    (out / "campaign.json").write_text(
        json.dumps({"package": "pkg", "commit": "source"})
    )
    proof = tmp_path / "acceptance.json"
    proof.write_text(json.dumps({"package": "other", "commit": "source"}))
    speed = tmp_path / "benchmark.json"
    speed.write_text(json.dumps({"package": "pkg", "commit": "source"}))
    with pytest.raises(RuntimeError, match="package mismatch"):
        module.prepare_campaign_runtime(out, proof, speed, portal=portal())


def test_campaign_command_is_recover_not_run():
    command = module.campaign_command(Path("out"), Path("a.json"), Path("b.json"))
    assert "--recover" in command
    assert "--run" not in command
    assert str(ROOT / "experiments/e0_campaign.py") in command
