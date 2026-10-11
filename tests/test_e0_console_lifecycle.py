"""Host wiring for xbox-gpu-training#46. Device Portal and the tool are mocked."""

from __future__ import annotations

import importlib.util
import json
import sys
import time
from pathlib import Path
from unittest.mock import Mock

import pytest

from floppylm_xbox import portal
from floppylm_xbox.console_lifecycle import (
    CONFIG_FILE_ENV,
    DEFAULT_ON_TOOL_UNREACHABLE,
    DEFAULT_REFUSE_ORPHAN,
    TOOL_ENV,
    TOOL_FLAGS,
    TOOL_HEARTBEAT_INTERVAL_DEFAULT,
    heartbeat,
    heartbeat_seconds,
    idle_gpu,
    is_orphan,
    is_valid_idle_report,
    is_valid_prepare_report,
    lifecycle_environ,
    load_lifecycle_config,
    prepare,
    prepare_verdict,
    record_console_lifecycle,
    resolve_tool,
    run_tool,
    stop_console,
    tool_command,
)

ROOT = Path(__file__).resolve().parents[1]
RETIRED_FLAGS = (
    "--engine",
    "--adapter",
    "--image",
    "--pid",
    "--engine-percent",
    "--cpu-idle-percent",
    "--wait-seconds",
    "--password",
    "--pass",
    "-p",
)
GLOBAL_FLAGS = set(TOOL_FLAGS.values())

GPU_ADVISORY_NOTE = (
    "GPU utilisation is advisory and not decisive. On Xbox the foreground "
    "engine often reads ~100% for any idle foreground app."
)

MOCK_TOOL = r"""
import json, os, sys
from pathlib import Path

NOTE = (
    "GPU utilisation is advisory and not decisive. On Xbox the foreground "
    "engine often reads ~100% for any idle foreground app."
)
log = Path(os.environ["LIFECYCLE_LOG"])
mode = os.environ.get("LIFECYCLE_MODE", "ok")
entry = {
    "argv": sys.argv[1:],
    "XGPU_PORTAL_URL": os.environ.get("XGPU_PORTAL_URL"),
    "XGPU_PORTAL_USER": os.environ.get("XGPU_PORTAL_USER"),
    "has_password": bool(os.environ.get("XGPU_PORTAL_PASSWORD")),
    "has_pin": bool(os.environ.get("XGPU_PORTAL_TLS_PIN")),
}
log.write_text(log.read_text() + json.dumps(entry) + "\n")
args = sys.argv[1:]
flags = {
    "--idle-exit-seconds", "--heartbeat-interval-seconds",
    "--heartbeat-stale-seconds", "--poll-interval-seconds",
    "--gpu-threshold-percent", "--gpu-sample-count",
    "--gpu-sample-interval-seconds", "--gpu-engine",
    "--gpu-engine-exclude", "--idle-cpu-percent",
    "--teardown-wait-seconds", "--process-image", "--package",
    "--package-family", "--terminate-by", "--portal-url",
    "--portal-port", "--tls-verify", "--tls-pin", "--credentials",
}
i = 0
while i < len(args) and args[i] in flags:
    i += 2
command = args[i]
if mode == "crash":
    raise SystemExit("tool crashed")
if mode == "unreachable":
    sys.stderr.write("connection refused\n")
    raise SystemExit(2)

def gpu_advisory(pinned=False, excluded=None):
    return {
        "decisive": False,
        "note": NOTE,
        "engine_pinned": pinned,
        "pinned": [{"adapter": 0, "engine": 5, "percent": 100.0}] if pinned else [],
        "excluded": list(excluded or []),
        "adapters": [[0.0, 0.0, 0.0, 0.0, 0.0, 100.0 if pinned else 0.0, 0.0]],
    }

def idle_report(
    when, *, orphan=False, job_active=False, after_fail=False, pinned=False,
    start_unknown=False,
):
    leftover = 4000.0 if orphan else None
    stale = orphan or leftover is None
    heartbeat_age = 4000.0 if orphan else None
    present = orphan or job_active or after_fail or pinned or when == "before"
    if after_fail:
        present = True
    if when == "after" and not after_fail:
        present = False
        leftover = None
        heartbeat_age = None
        stale = True
        orphan = False
        job_active = False
        start_unknown = False
    running = job_active
    queued = False
    claimed = job_active
    ready = (not job_active) and (not running)
    if when == "before":
        if job_active:
            ok, reason = False, "job_active"
        elif orphan:
            ok, reason = False, "orphan_stale_idle"
        elif start_unknown:
            ok, reason = True, "start_time_unknown"
        else:
            ok, reason = True, "ok"
    elif present:
        ok, reason = False, "process_still_running"
    else:
        ok, reason = True, "ok"
    if start_unknown:
        app_age = idle_age = leftover = None
        orphan_value = None
    elif orphan:
        app_age = idle_age = 4000.0
        orphan_value = True
    elif present:
        app_age = idle_age = 12.0
        orphan_value = False
    else:
        app_age = idle_age = leftover
        orphan_value = orphan
    return {
        "when": when,
        "ok": ok,
        "reason": reason,
        "process_present": present,
        "job_active": job_active,
        "queued": queued,
        "claimed": claimed,
        "claimed_live": ["job.claimed"] if claimed else [],
        "running": running,
        "ready": ready,
        "worker_state": "running" if running else "ready",
        "app_age_seconds": app_age,
        "idle_age_seconds": idle_age,
        "heartbeat_age_seconds": heartbeat_age,
        "heartbeat_stale": stale,
        "last_job_ended_age_seconds": leftover,
        "orphan": orphan_value,
        "cpu_idle": present and not job_active,
        "gpu_advisory": gpu_advisory(pinned=pinned or orphan or (when == "before")),
    }

if command == "prepare":
    cleared = ["inbox/shutdown"] if mode == "prepare-cleared" else []
    print(json.dumps({"cleared": cleared}, sort_keys=True), flush=True)
    raise SystemExit(0)
if command == "heartbeat":
    print("heartbeat: ok", flush=True)
    raise SystemExit(0)
if command == "idle-gpu":
    when = args[args.index("--when") + 1]
    if mode == "invalid":
        print("not-a-report", flush=True)
        raise SystemExit(1)
    report = idle_report(
        when,
        orphan=mode == "orphan" and when == "before",
        job_active=mode == "job-active" and when == "before",
        after_fail=mode == "after-fail" and when == "after",
        pinned=mode == "gpu-idle",
        start_unknown=mode == "start-time-unknown" and when == "before",
    )
    print(json.dumps(report, sort_keys=True), flush=True)
    raise SystemExit(0 if report["ok"] else 1)
if command == "teardown":
    report = idle_report("after", after_fail=mode == "teardown-fail")
    report["terminated"] = mode == "teardown-fail"
    print(json.dumps(report, sort_keys=True), flush=True)
    raise SystemExit(0 if report["ok"] else 1)
raise SystemExit(2)
"""


@pytest.fixture(autouse=True)
def no_live_portal(monkeypatch, tmp_path_factory):
    def boom(*_a, **_k):
        raise AssertionError("Device Portal must be mocked; no live console calls")

    monkeypatch.delenv(TOOL_ENV, raising=False)
    missing = tmp_path_factory.mktemp("noconfig") / "xbox.env"
    monkeypatch.setattr("floppylm_xbox.console_lifecycle.env_file", lambda: missing)
    monkeypatch.setattr(portal, "env_file", lambda: missing)
    monkeypatch.setattr(portal.Portal, "request", boom)
    monkeypatch.setattr(portal.Portal, "configured", classmethod(lambda *_a, **_k: boom()))


@pytest.fixture
def campaign_module(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "experiments"))
    spec = importlib.util.spec_from_file_location(
        "campaign_lifecycle_test", ROOT / "experiments/e0_campaign.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def teardown_module():
    spec = importlib.util.spec_from_file_location(
        "e0_console_teardown", ROOT / "scripts/e0_console_teardown.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_tool(tmp_path: Path) -> Path:
    path = tmp_path / "e0_console_lifecycle.py"
    path.write_text(MOCK_TOOL)
    return path


def tool_log(tmp_path: Path) -> Path:
    log = tmp_path / "lifecycle.log"
    log.write_text("")
    return log


def inputs(tmp_path: Path):
    proof = tmp_path / "acceptance.json"
    proof.write_text(json.dumps({"ok": True, "package": "pkg", "commit": "source"}))
    benchmark = tmp_path / "benchmark.json"
    benchmark.write_text(json.dumps({"package": "pkg", "commit": "source"}))
    return proof, benchmark


def logged_commands(log: Path) -> list[list[str]]:
    return [json.loads(line)["argv"] for line in log.read_text().splitlines() if line]


def argv_command(argv: list[str]) -> str:
    i = 0
    while i < len(argv) and argv[i] in GLOBAL_FLAGS:
        i += 2
    return argv[i]


def assert_no_retired_flags(argv: list[str]) -> None:
    for flag in RETIRED_FLAGS:
        assert flag not in argv


def test_cli_stays_thin_and_omits_unset_detection_flags(tmp_path):
    tool = write_tool(tmp_path)
    assert tool_command(tool, "heartbeat") == [sys.executable, str(tool), "heartbeat"]
    before = tool_command(tool, "idle-gpu", "--when", "before", package="pkg")
    assert before == [
        sys.executable,
        str(tool),
        "--package",
        "pkg",
        "idle-gpu",
        "--when",
        "before",
    ]
    assert_no_retired_flags(before)
    assert tool_command(tool, "prepare")[-1] == "prepare"
    assert tool_command(tool, "teardown")[-1] == "teardown"
    assert tool_command(tool, "idle-gpu", "--when", "after")[-2:] == ["--when", "after"]


def test_config_defaults_and_overrides(tmp_path, monkeypatch):
    for key in (
        "XGPU_HEARTBEAT_INTERVAL_SECONDS",
        "XGPU_GPU_ENGINES",
        "XGPU_GPU_ENGINE_EXCLUDE",
        "XGPU_PROCESS_IMAGES",
        "XGPU_TEARDOWN_WAIT_SECONDS",
        "XGPU_IDLE_CPU_PERCENT",
        "XGPU_E0_HOST_HEARTBEAT_SECONDS",
        "XGPU_E0_GPU_ENGINE",
        "XGPU_E0_APP_IMAGE",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("XGPU_E0_HOST_HEARTBEAT_SECONDS", "99")
    monkeypatch.setenv("XGPU_E0_APP_IMAGE", "Old.exe")
    monkeypatch.setenv("XGPU_E0_GPU_ENGINE", "5")
    defaults = load_lifecycle_config()
    assert defaults.heartbeat_interval_seconds is None
    assert defaults.process_images is None
    assert defaults.gpu_engines is None
    assert heartbeat_seconds() == TOOL_HEARTBEAT_INTERVAL_DEFAULT
    assert defaults.refuse_orphan is DEFAULT_REFUSE_ORPHAN
    assert defaults.on_tool_unreachable == DEFAULT_ON_TOOL_UNREACHABLE
    assert defaults.gpu_engines is None
    assert defaults.gpu_engine_exclude is None
    assert defaults.process_images is None
    assert defaults.idle_cpu_percent is None
    assert defaults.teardown_wait_seconds is None
    assert defaults.idle_exit_seconds is None
    assert defaults.terminate_by is None

    monkeypatch.setenv("XGPU_HEARTBEAT_INTERVAL_SECONDS", "12")
    monkeypatch.setenv("XGPU_E0_REFUSE_ORPHAN", "0")
    monkeypatch.setenv("XGPU_GPU_ENGINES", "3,5")
    monkeypatch.setenv("XGPU_GPU_ENGINE_EXCLUDE", "5")
    monkeypatch.setenv("XGPU_PROCESS_IMAGES", "Trainer.exe")
    monkeypatch.setenv("XGPU_TEARDOWN_WAIT_SECONDS", "9")
    monkeypatch.setenv("XGPU_GPU_THRESHOLD_PERCENT", "80")
    monkeypatch.setenv("XGPU_IDLE_CPU_PERCENT", "2")
    monkeypatch.setenv("XGPU_IDLE_EXIT_SECONDS", "600")
    monkeypatch.setenv("XGPU_PACKAGE_FAMILY", "Fam")
    monkeypatch.setenv("XGPU_TERMINATE_BY", "package,pid")
    monkeypatch.setenv("XGPU_PORTAL_TLS_VERIFY", "pin")
    env_cfg = load_lifecycle_config()
    assert env_cfg.heartbeat_interval_seconds == 12
    assert env_cfg.refuse_orphan is False
    assert env_cfg.gpu_engines == ("3", "5")
    assert env_cfg.gpu_engine_exclude == ("5",)
    assert env_cfg.process_images == ("Trainer.exe",)
    assert env_cfg.teardown_wait_seconds == 9
    assert env_cfg.idle_cpu_percent == 2
    assert env_cfg.idle_exit_seconds == 600
    assert env_cfg.package_family == "Fam"
    assert env_cfg.terminate_by == ("package", "pid")
    assert env_cfg.tls_verify == "pin"

    file_cfg = tmp_path / "lifecycle.json"
    file_cfg.write_text(
        json.dumps(
            {
                "heartbeat_interval_seconds": 40,
                "gpu_engines": ["7"],
                "refuse_orphan": True,
                "package": "from-file",
            }
        )
    )
    monkeypatch.setenv(CONFIG_FILE_ENV, str(file_cfg))
    from_file = load_lifecycle_config()
    assert from_file.heartbeat_interval_seconds == 40
    assert from_file.gpu_engines == ("7",)
    assert from_file.refuse_orphan is True
    assert from_file.package == "from-file"

    root = tmp_path / "campaign"
    root.mkdir()
    (root / "campaign.json").write_text(
        json.dumps(
            {
                "schema": "floppylm.e0.campaign.v1",
                "console_lifecycle": {
                    "config": {
                        "heartbeat_interval_seconds": 88,
                        "gpu_engines": ["2"],
                        "process_images": ["Host.exe"],
                    }
                },
            }
        )
    )
    from_campaign = load_lifecycle_config(campaign_root=root)
    assert from_campaign.heartbeat_interval_seconds == 88
    assert from_campaign.gpu_engines == ("2",)
    assert from_campaign.process_images == ("Host.exe",)
    tool = write_tool(tmp_path)
    cli = load_lifecycle_config(
        campaign_root=root,
        overrides={
            "heartbeat_interval_seconds": 3,
            "gpu_engines": ("9",),
            "gpu_engine_exclude": ("5",),
            "tool": tool,
        },
    )
    assert cli.heartbeat_interval_seconds == 3
    assert cli.gpu_engines == ("9",)
    assert cli.gpu_engine_exclude == ("5",)

    forwarded = tool_command(cli, "idle-gpu", "--when", "before")
    assert forwarded[forwarded.index("--gpu-engine") + 1] == "9"
    assert forwarded[forwarded.index("--gpu-engine-exclude") + 1] == "5"
    assert forwarded[forwarded.index("--process-image") + 1] == "Host.exe"
    assert forwarded[forwarded.index("--heartbeat-interval-seconds") + 1] == "3"
    assert_no_retired_flags(forwarded)
    command_at = forwarded.index("idle-gpu")
    assert forwarded[command_at - 2] != "idle-gpu"
    assert "idle-gpu" in forwarded[command_at:]
    torn = tool_command(
        load_lifecycle_config(overrides={"tool": tool, "teardown_wait_seconds": 15}),
        "teardown",
    )
    assert "--teardown-wait-seconds" in torn
    assert torn[torn.index("--teardown-wait-seconds") + 1] == "15"
    assert torn[-1] == "teardown"
    assert_no_retired_flags(torn)


def test_tool_path_comes_from_env_or_flag(tmp_path, monkeypatch):
    tool = write_tool(tmp_path)
    monkeypatch.delenv(TOOL_ENV, raising=False)
    assert resolve_tool() is None
    monkeypatch.setenv(TOOL_ENV, str(tool))
    assert resolve_tool() == tool
    other = tmp_path / "other.py"
    other.write_text("print(0)\n")
    assert resolve_tool(other) == other


def test_lifecycle_environ_maps_xbox_settings_without_argv_secrets(tmp_path, monkeypatch):
    monkeypatch.delenv("UWP_DEVICE_URL", raising=False)
    monkeypatch.delenv("XGPU_PORTAL_URL", raising=False)
    env = lifecycle_environ(
        {
            "XBOX_IP": "192.0.2.10",
            "XBOX_PORT": "11443",
            "XBOX_USER": "portal-user",
            "XBOX_PASS": "secret",
            "XBOX_CERT_SHA256": "ab" * 32,
            "XGPU_E0_PACKAGE": "pkg",
        }
    )
    assert env["XGPU_PORTAL_URL"] == "https://192.0.2.10:11443"
    assert env["XGPU_PORTAL_USER"] == "portal-user"
    assert env["XGPU_PORTAL_PASSWORD"] == "secret"
    assert env["XGPU_PORTAL_TLS_PIN"] == "ab" * 32
    assert env["UWP_DEVICE_URL"] == "https://192.0.2.10:11443"
    tool = write_tool(tmp_path)
    log = tool_log(tmp_path)
    monkeypatch.setenv("LIFECYCLE_LOG", str(log))
    monkeypatch.setenv("LIFECYCLE_MODE", "ok")
    monkeypatch.setenv("XBOX_PASS", "secret")
    result = heartbeat(tool=tool, package="pkg")
    assert result["ok"]
    assert "--instance-id" not in result["argv"]
    dumped = json.dumps(result, default=str)
    assert "secret" not in dumped
    assert "--password" not in dumped
    assert_no_retired_flags(result["argv"])
    recorded = json.loads(log.read_text().splitlines()[0])
    assert recorded["has_password"] is True
    assert "secret" not in log.read_text()


def test_run_tool_rejects_password_cli_flags(tmp_path, monkeypatch):
    tool = write_tool(tmp_path)
    monkeypatch.setattr(
        "floppylm_xbox.console_lifecycle.tool_command",
        lambda *_a, **_k: [sys.executable, str(tool), "--password", "secret", "heartbeat"],
    )
    with pytest.raises(RuntimeError, match="password must not be a CLI flag"):
        run_tool("heartbeat", tool=tool)


def test_idle_gpu_before_detects_state_orphan(tmp_path, monkeypatch):
    tool = write_tool(tmp_path)
    log = tool_log(tmp_path)
    monkeypatch.setenv("LIFECYCLE_LOG", str(log))
    monkeypatch.setenv("LIFECYCLE_MODE", "orphan")
    result = idle_gpu("before", tool=tool, package="pkg")
    assert result["reachable"]
    assert not result["ok"]
    assert is_orphan(result)
    assert prepare_verdict(result) == "orphan"
    report = result["report"]
    assert report["reason"] == "orphan_stale_idle"
    assert report["orphan"] is True
    assert report["process_present"] is True
    assert report["job_active"] is False
    assert report["heartbeat_stale"] is True
    assert report["last_job_ended_age_seconds"] == 4000.0
    assert report["app_age_seconds"] == 4000.0
    assert report["idle_age_seconds"] == 4000.0
    assert report["claimed_live"] == []
    assert report["gpu_advisory"]["decisive"] is False


def test_gpu_advisory_is_not_an_orphan_verdict():
    ready = {
        "reachable": True,
        "ok": True,
        "report": {
            "when": "before",
            "ok": True,
            "reason": "ok",
            "orphan": False,
            "process_present": True,
            "job_active": False,
            "queued": False,
            "claimed": False,
            "running": False,
            "ready": True,
            "worker_state": "ready",
            "heartbeat_age_seconds": None,
            "heartbeat_stale": True,
            "last_job_ended_age_seconds": None,
            "cpu_idle": True,
            "gpu_advisory": {
                "decisive": False,
                "note": GPU_ADVISORY_NOTE,
                "engine_pinned": True,
                "pinned": [{"adapter": 0, "engine": 5, "percent": 100.0}],
                "excluded": [5],
                "adapters": [[0.0, 0.0, 0.0, 0.0, 0.0, 100.0, 0.0]],
            },
        },
    }
    assert is_valid_idle_report(ready)
    assert not is_orphan(ready)
    assert prepare_verdict(ready) == "ready"
    orphan = {
        "reachable": True,
        "ok": False,
        "report": {
            "when": "before",
            "ok": False,
            "reason": "orphan_stale_idle",
            "orphan": True,
            "process_present": True,
            "job_active": False,
            "queued": False,
            "claimed": False,
            "running": False,
            "ready": True,
            "worker_state": "ready",
            "heartbeat_age_seconds": 4000.0,
            "heartbeat_stale": True,
            "last_job_ended_age_seconds": 4000.0,
            "gpu_advisory": {"decisive": False, "engine_pinned": True, "pinned": []},
        },
    }
    assert is_orphan(orphan)
    assert prepare_verdict(orphan) == "orphan"
    busy = {
        "reachable": True,
        "ok": False,
        "report": {
            "when": "before",
            "ok": False,
            "reason": "job_active",
            "orphan": False,
            "process_present": True,
            "job_active": True,
            "running": True,
            "ready": False,
            "gpu_advisory": {"decisive": False, "engine_pinned": False},
        },
    }
    assert not is_orphan(busy)
    assert prepare_verdict(busy) == "job_active"


def test_prepare_reports_cleared_markers(tmp_path, monkeypatch):
    tool = write_tool(tmp_path)
    log = tool_log(tmp_path)
    monkeypatch.setenv("LIFECYCLE_LOG", str(log))
    monkeypatch.setenv("LIFECYCLE_MODE", "prepare-cleared")
    result = prepare(tool=tool, package="pkg")
    assert result["ok"]
    assert is_valid_prepare_report(result)
    assert result["report"]["cleared"] == ["inbox/shutdown"]
    assert result["argv"][-1] == "prepare"


def test_unreachable_tool_is_logged_not_raised(tmp_path):
    missing = tmp_path / "absent.py"
    result = idle_gpu("before", tool=missing)
    assert not result["reachable"]
    assert not result["ok"]
    assert "not found" in result["error"]
    result = run_tool("teardown")
    assert result["error"].startswith(TOOL_ENV)


def test_stop_console_runs_teardown_then_idle_gpu_after(tmp_path, monkeypatch):
    tool = write_tool(tmp_path)
    log = tool_log(tmp_path)
    monkeypatch.setenv("LIFECYCLE_LOG", str(log))
    monkeypatch.setenv("LIFECYCLE_MODE", "ok")
    result = stop_console(tool=tool, package="pkg")
    assert result["ok"]
    commands = [argv_command(argv) for argv in logged_commands(log)]
    assert commands == ["teardown", "idle-gpu"]
    assert logged_commands(log)[1][-2:] == ["--when", "after"]


def test_record_survives_missing_summary(tmp_path):
    root = tmp_path / "campaign"
    root.mkdir()
    (root / "campaign.json").write_text(json.dumps({"schema": "floppylm.e0.campaign.v1"}))
    record_console_lifecycle(root, {"ok": True, "teardown": {"ok": True}})
    saved = json.loads((root / "campaign.json").read_text())
    assert saved["console_lifecycle"]["ok"] is True
    assert not (root / "summary.json").exists()


def test_campaign_refuses_orphan_unless_flag(
    tmp_path, monkeypatch, campaign_module
):
    tool = write_tool(tmp_path)
    log = tool_log(tmp_path)
    monkeypatch.setenv("LIFECYCLE_LOG", str(log))
    monkeypatch.setenv("LIFECYCLE_MODE", "orphan")
    proof, speed = inputs(tmp_path)
    campaign = campaign_module.Campaign(
        tmp_path / "campaign", proof, speed, lifecycle_tool=tool
    )
    campaign.run = Mock(side_effect=AssertionError("must not start"))
    campaign.report = lambda: None
    with pytest.raises(RuntimeError, match="idle-gpu --when before orphan"):
        campaign.run_managed()
    campaign.run.assert_not_called()
    assert campaign.state["status"] == "stopped"
    assert is_orphan(campaign.state["console_lifecycle"]["idle_gpu_before"])
    assert "teardown" not in campaign.state["console_lifecycle"]
    stored = campaign.state["console_lifecycle"]["config"]
    assert "password" not in stored
    assert "secret" not in json.dumps(stored)

    allowed = campaign_module.Campaign(
        tmp_path / "allowed",
        proof,
        speed,
        lifecycle_tool=tool,
        allow_orphan_gpu=True,
    )
    assert allowed.allow_orphan is True
    assert allowed.allow_orphan_gpu is True
    allowed.run = lambda: allowed.state.update(status="completed")
    allowed.report = lambda: None
    allowed.run_managed()
    assert allowed.state["status"] == "completed"
    assert allowed.state["console_lifecycle"]["teardown"]["reachable"]


def test_unreachable_console_does_not_crash_campaign_record(
    tmp_path, monkeypatch, campaign_module
):
    proof, speed = inputs(tmp_path)
    campaign = campaign_module.Campaign(
        tmp_path / "campaign",
        proof,
        speed,
        lifecycle_tool=tmp_path / "missing-tool.py",
    )
    campaign.run = lambda: campaign.state.update(status="completed")
    campaign.report = lambda: None
    campaign.run_managed()
    assert campaign.state["status"] == "completed"
    before = campaign.state["console_lifecycle"]["idle_gpu_before"]
    assert not before["reachable"]
    assert campaign.state["console_lifecycle"]["teardown"]["reachable"] is False
    held = campaign.state["console_lifecycle"]
    assert held["on_tool_unreachable"] == "continue"
    assert held["config"]["on_tool_unreachable"] == "continue"


@pytest.mark.parametrize("outcome", ["completed", "failed", "cancel"])
def test_teardown_on_terminal_paths(tmp_path, monkeypatch, campaign_module, outcome):
    tool = write_tool(tmp_path)
    log = tool_log(tmp_path)
    monkeypatch.setenv("LIFECYCLE_LOG", str(log))
    monkeypatch.setenv("LIFECYCLE_MODE", "ok")
    proof, speed = inputs(tmp_path)
    campaign = campaign_module.Campaign(
        tmp_path / "campaign",
        proof,
        speed,
        lifecycle_tool=tool,
        heartbeat_interval_seconds=60,
    )
    if outcome == "completed":
        campaign.run = lambda: campaign.state.update(status="completed")
        campaign.report = lambda: None
        campaign.run_managed()
        reason = "completed"
    elif outcome == "failed":
        campaign.run = Mock(side_effect=RuntimeError("trial failed"))
        campaign.report = lambda: None
        with pytest.raises(RuntimeError, match="trial failed"):
            campaign.run_managed()
        reason = "stopped"
    else:
        campaign.run = Mock(side_effect=KeyboardInterrupt("signal 15"))
        campaign.report = lambda: None
        with pytest.raises(KeyboardInterrupt):
            campaign.run_managed()
        reason = "stopped"
    state = json.loads((tmp_path / "campaign" / "campaign.json").read_text())
    assert state["console_lifecycle"]["stop_reason"] == reason
    assert state["console_lifecycle"]["teardown"]["ok"]
    assert state["console_lifecycle"]["idle_gpu_after"]["report"]["when"] == "after"
    commands = [argv_command(row) for row in logged_commands(log)]
    assert commands[0] == "prepare"
    assert commands[1] == "idle-gpu"
    assert "teardown" in commands
    assert commands[-1] == "idle-gpu"
    for argv in logged_commands(log):
        assert_no_retired_flags(argv)


def test_heartbeat_while_campaign_runs(tmp_path, monkeypatch, campaign_module):
    tool = write_tool(tmp_path)
    log = tool_log(tmp_path)
    monkeypatch.setenv("LIFECYCLE_LOG", str(log))
    monkeypatch.setenv("LIFECYCLE_MODE", "ok")
    proof, speed = inputs(tmp_path)
    campaign = campaign_module.Campaign(
        tmp_path / "campaign",
        proof,
        speed,
        lifecycle_tool=tool,
        heartbeat_interval_seconds=0.05,
    )
    campaign.run = lambda: time.sleep(0.16)
    campaign.report = lambda: None
    campaign.state.update(status="completed")
    campaign.run_managed()
    heartbeats = [row for row in logged_commands(log) if argv_command(row) == "heartbeat"]
    assert len(heartbeats) >= 2


def test_report_copies_console_lifecycle(tmp_path, monkeypatch, campaign_module):
    proof, speed = inputs(tmp_path)
    campaign = campaign_module.Campaign(tmp_path / "campaign", proof, speed)
    evidence = tmp_path / "evidence"
    monkeypatch.setattr(campaign_module, "EVIDENCE", evidence)
    campaign.state["console_lifecycle"] = {"ok": True, "stop_reason": "completed"}
    campaign.report()
    summary = json.loads((campaign.root / "summary.json").read_text())
    assert summary["console_lifecycle"]["stop_reason"] == "completed"
    copied = json.loads(
        (evidence / "campaigns" / campaign.state["id"] / "campaign.json").read_text()
    )
    assert copied["console_lifecycle"]["ok"] is True
    campaign.lock.close()


def test_execstop_helper_records_failed_tool(tmp_path, monkeypatch, teardown_module):
    tool = write_tool(tmp_path)
    log = tool_log(tmp_path)
    monkeypatch.setenv("LIFECYCLE_LOG", str(log))
    monkeypatch.setenv("LIFECYCLE_MODE", "teardown-fail")
    root = tmp_path / "campaign"
    root.mkdir()
    (root / "campaign.json").write_text(
        json.dumps({"schema": "floppylm.e0.campaign.v1", "package": "pkg", "status": "completed"})
    )
    (root / "summary.json").write_text(json.dumps({"campaign": "c", "status": "completed"}))
    result = teardown_module.teardown_campaign(root, tool=tool)
    assert result["ok"] is False
    campaign = json.loads((root / "campaign.json").read_text())
    summary = json.loads((root / "summary.json").read_text())
    assert campaign["console_lifecycle"]["source"] == "execstop"
    assert campaign["status"] == "completed"
    assert summary["console_lifecycle"]["teardown"]["reachable"]
    assert summary["status"] == "completed"


def test_execstop_cli_uses_teardown_wait_seconds(tmp_path, teardown_module):
    captured = {}

    def fake(root, **kwargs):
        captured.update(kwargs)
        captured["root"] = root
        return {"ok": True}

    teardown_module.teardown_campaign = fake
    assert (
        teardown_module.main(
            ["--campaign", str(tmp_path), "--teardown-wait-seconds", "15"]
        )
        == 0
    )
    assert captured["teardown_wait_seconds"] == 15
    with pytest.raises(SystemExit):
        teardown_module.main(["--campaign", str(tmp_path), "--wait-seconds", "15"])


def test_idle_ready_gpu_busy_app_is_reusable(tmp_path, monkeypatch, campaign_module):
    tool = write_tool(tmp_path)
    log = tool_log(tmp_path)
    monkeypatch.setenv("LIFECYCLE_LOG", str(log))
    monkeypatch.setenv("LIFECYCLE_MODE", "gpu-idle")
    proof, speed = inputs(tmp_path)
    campaign = campaign_module.Campaign(
        tmp_path / "campaign", proof, speed, lifecycle_tool=tool
    )
    campaign.run = lambda: campaign.state.update(status="completed")
    campaign.report = lambda: None
    campaign.run_managed()
    assert campaign.state["status"] == "completed"
    before = campaign.state["console_lifecycle"]["idle_gpu_before"]
    assert campaign.state["console_lifecycle"]["prepare"]["ok"]
    assert before["report"]["gpu_advisory"]["decisive"] is False
    assert before["report"]["gpu_advisory"]["engine_pinned"] is True
    assert before["report"]["ready"] is True
    assert not is_orphan(before)
    commands = [argv_command(row) for row in logged_commands(log)]
    assert commands[0] == "prepare"
    assert commands[1] == "idle-gpu"


def test_job_active_before_is_refused(tmp_path, monkeypatch, campaign_module):
    tool = write_tool(tmp_path)
    log = tool_log(tmp_path)
    monkeypatch.setenv("LIFECYCLE_LOG", str(log))
    monkeypatch.setenv("LIFECYCLE_MODE", "job-active")
    proof, speed = inputs(tmp_path)
    campaign = campaign_module.Campaign(
        tmp_path / "campaign", proof, speed, lifecycle_tool=tool
    )
    campaign.run = Mock(side_effect=AssertionError("must not start"))
    campaign.report = lambda: None
    with pytest.raises(RuntimeError, match="idle-gpu --when before job_active"):
        campaign.run_managed()
    campaign.run.assert_not_called()
    before = campaign.state["console_lifecycle"]["idle_gpu_before"]
    assert before["report"]["reason"] == "job_active"
    assert not is_orphan(before)
    assert prepare_verdict(before) == "job_active"


@pytest.mark.parametrize("mode", ["crash", "invalid"])
def test_crash_or_invalid_report_is_fail_closed(
    tmp_path, monkeypatch, campaign_module, mode
):
    tool = write_tool(tmp_path)
    log = tool_log(tmp_path)
    monkeypatch.setenv("LIFECYCLE_LOG", str(log))
    monkeypatch.setenv("LIFECYCLE_MODE", mode)
    proof, speed = inputs(tmp_path)
    campaign = campaign_module.Campaign(
        tmp_path / "campaign", proof, speed, lifecycle_tool=tool
    )
    campaign.run = Mock(side_effect=AssertionError("must not start"))
    campaign.report = lambda: None
    expected = (
        "prepare crashed or returned an invalid report"
        if mode == "crash"
        else "idle-gpu --when before invalid"
    )
    with pytest.raises(RuntimeError, match=expected):
        campaign.run_managed()
    campaign.run.assert_not_called()
    assert campaign.state["status"] == "stopped"
    held = campaign.state["console_lifecycle"]
    assert held["prepare"]["reachable"] is True
    if mode == "crash":
        assert not is_valid_prepare_report(held["prepare"])
        assert "idle_gpu_before" not in held
    else:
        assert held["idle_gpu_before"]["reachable"] is True
        assert prepare_verdict(held["idle_gpu_before"]) == "invalid"
    assert "teardown" not in held

    allowed = campaign_module.Campaign(
        tmp_path / f"allowed-{mode}",
        proof,
        speed,
        lifecycle_tool=tool,
        allow_orphan=True,
    )
    allowed.run = lambda: allowed.state.update(status="completed")
    allowed.report = lambda: None
    allowed.run_managed()
    assert allowed.state["status"] == "completed"


def test_integer_settings_are_formatted_as_integers():
    cfg = load_lifecycle_config(
        settings={},
        overrides={
            "idle_exit_seconds": 20,
            "heartbeat_interval_seconds": 30,
            "heartbeat_stale_seconds": 1800,
            "gpu_sample_count": 3,
            "portal_port": 11443,
            "poll_interval_seconds": 1,
        },
    )
    env = lifecycle_environ(settings={}, config=cfg)
    assert env["XGPU_IDLE_EXIT_SECONDS"] == "20"
    assert env["XGPU_HEARTBEAT_INTERVAL_SECONDS"] == "30"
    assert env["XGPU_HEARTBEAT_STALE_SECONDS"] == "1800"
    assert env["XGPU_GPU_SAMPLE_COUNT"] == "3"
    assert env["XGPU_PORTAL_PORT"] == "11443"
    assert env["XGPU_POLL_INTERVAL_SECONDS"] == "1"
    exclude = load_lifecycle_config(
        settings={}, overrides={"gpu_engine_exclude": ("5", "1")}
    )
    assert lifecycle_environ(settings={}, config=exclude)["XGPU_GPU_ENGINE_EXCLUDE"] == "5,1"
    for key in (
        "XGPU_IDLE_EXIT_SECONDS",
        "XGPU_HEARTBEAT_INTERVAL_SECONDS",
        "XGPU_GPU_SAMPLE_COUNT",
        "XGPU_PORTAL_PORT",
    ):
        assert "." not in env[key]
    forwarded = tool_command(
        load_lifecycle_config(
            settings={},
            overrides={"tool": "/tmp/tool.py", "idle_exit_seconds": 20.0},
        ),
        "heartbeat",
    )
    assert forwarded[forwarded.index("--idle-exit-seconds") + 1] == "20"


def test_env_refuse_orphan_override_allows_start(tmp_path, monkeypatch, campaign_module):
    tool = write_tool(tmp_path)
    log = tool_log(tmp_path)
    monkeypatch.setenv("LIFECYCLE_LOG", str(log))
    monkeypatch.setenv("LIFECYCLE_MODE", "orphan")
    monkeypatch.setenv("XGPU_E0_REFUSE_ORPHAN", "0")
    proof, speed = inputs(tmp_path)
    campaign = campaign_module.Campaign(
        tmp_path / "campaign", proof, speed, lifecycle_tool=tool
    )
    campaign.run = lambda: campaign.state.update(status="completed")
    campaign.report = lambda: None
    campaign.run_managed()
    assert campaign.lifecycle.refuse_orphan is False
    assert campaign.state["status"] == "completed"
    assert campaign.state["console_lifecycle"]["config"]["refuse_orphan"] is False


def test_unit_template_uses_environment_files():
    text = (ROOT / "units/floppylm-e0-campaign@.service").read_text()
    assert "ExecStop=" in text
    assert "scripts/e0_console_teardown.py" in text
    assert "FLOPPYLM_E0_OUT" in text
    assert "EnvironmentFile=-%E/floppylm/xbox.env" in text
    assert "EnvironmentFile=-%E/floppylm/e0-lifecycle.env" in text
    assert "e0-console-lifecycle.md" in text
    lowered = text.lower()
    assert "192.168." not in text
    assert "/home/" not in lowered
    assert "gianlucamazza.it" not in lowered
    assert "engine 5" not in lowered
    assert "--engine" not in text


def test_docs_and_example_use_canonical_names():
    docs = (ROOT / "docs/operations/e0-console-lifecycle.md").read_text()
    example = (ROOT / "docs/operations/e0-lifecycle.env.example").read_text()
    text = docs + "\n" + example
    for token in (
        "--idle-exit-seconds",
        "--heartbeat-interval-seconds",
        "--heartbeat-stale-seconds",
        "--poll-interval-seconds",
        "--gpu-threshold-percent",
        "--gpu-sample-count",
        "--gpu-sample-interval-seconds",
        "--gpu-engine",
        "--gpu-engine-exclude",
        "--idle-cpu-percent",
        "--teardown-wait-seconds",
        "--process-image",
        "--package-family",
        "--terminate-by",
        "--portal-url",
        "--portal-port",
        "--tls-verify",
        "--tls-pin",
        "--credentials",
        "XGPU_IDLE_EXIT_SECONDS",
        "XGPU_HEARTBEAT_INTERVAL_SECONDS",
        "XGPU_GPU_ENGINE_EXCLUDE",
        "XGPU_PORTAL_PASSWORD",
        "--allow-orphan",
        "on_tool_unreachable",
        "XGPU_E0_ON_TOOL_UNREACHABLE",
        "app_age_seconds",
        "idle_age_seconds",
        "claimed_live",
        "start_time_unknown",
    ):
        assert token in text
    for token in (
        "--host-heartbeat-seconds",
        "XGPU_E0_HOST_HEARTBEAT_SECONDS",
        "XGPU_E0_APP_IMAGE",
        "XGPU_E0_PID",
        "XGPU_E0_GPU_ADAPTER",
        "XGPU_E0_GPU_ENGINE",
    ):
        assert token not in text
    for token in (
        "XGPU_E0_HOST_HEARTBEAT_SECONDS",
        "XGPU_E0_APP_IMAGE",
        "XGPU_E0_PID",
        "XGPU_E0_GPU_ADAPTER",
        "--wait-seconds",
        "--engine-percent",
        "--cpu-idle-percent",
    ):
        assert token not in example


def test_new_sources_have_no_personal_hosts_or_engine_assumption():
    paths = [
        ROOT / "src/floppylm_xbox/console_lifecycle.py",
        ROOT / "scripts/e0_console_teardown.py",
        ROOT / "units/floppylm-e0-campaign@.service",
        ROOT / "experiments/e0_campaign.py",
        ROOT / "docs/operations/e0-lifecycle.env.example",
    ]
    forbidden = ("10.0.", "172.16.", "192.168.", "/home/", "/Users/", "engine 5", "PINNED_ENGINE")
    for path in paths:
        text = path.read_text()
        for token in forbidden:
            assert token not in text, f"{path} contains {token}"


def test_start_time_unknown_is_warning_not_orphan():
    unknown = {
        "reachable": True,
        "ok": True,
        "report": {
            "when": "before",
            "ok": True,
            "reason": "start_time_unknown",
            "orphan": None,
            "process_present": True,
            "job_active": False,
            "claimed_live": [],
            "app_age_seconds": None,
            "idle_age_seconds": None,
            "gpu_advisory": {"decisive": False},
        },
    }
    assert is_valid_idle_report(unknown)
    assert not is_orphan(unknown)
    assert prepare_verdict(unknown) == "start_time_unknown"
    orphan_null = {
        "reachable": True,
        "ok": True,
        "report": {
            "when": "before",
            "ok": True,
            "reason": "ok",
            "orphan": None,
            "process_present": True,
            "job_active": False,
        },
    }
    assert not is_orphan(orphan_null)
    assert prepare_verdict(orphan_null) == "start_time_unknown"


def test_start_time_unknown_starts_campaign(
    tmp_path, monkeypatch, campaign_module
):
    tool = write_tool(tmp_path)
    log = tool_log(tmp_path)
    monkeypatch.setenv("LIFECYCLE_LOG", str(log))
    monkeypatch.setenv("LIFECYCLE_MODE", "start-time-unknown")
    proof, speed = inputs(tmp_path)
    campaign = campaign_module.Campaign(
        tmp_path / "campaign", proof, speed, lifecycle_tool=tool
    )
    campaign.run = lambda: campaign.state.update(status="completed")
    campaign.report = lambda: None
    campaign.run_managed()
    assert campaign.state["status"] == "completed"
    before = campaign.state["console_lifecycle"]["idle_gpu_before"]
    assert before["report"]["reason"] == "start_time_unknown"
    assert before["report"]["orphan"] is None
    assert before["report"]["app_age_seconds"] is None
    assert before["report"]["idle_age_seconds"] is None
    assert prepare_verdict(before) == "start_time_unknown"
    assert not is_orphan(before)
    assert campaign.state["console_lifecycle"]["warning"] == "start_time_unknown"
    assert campaign.state["console_lifecycle"]["teardown"]["reachable"]


def test_on_tool_unreachable_refuse_stops_campaign(
    tmp_path, monkeypatch, campaign_module
):
    proof, speed = inputs(tmp_path)
    campaign = campaign_module.Campaign(
        tmp_path / "campaign",
        proof,
        speed,
        lifecycle_tool=tmp_path / "missing-tool.py",
        on_tool_unreachable="refuse",
    )
    campaign.run = Mock(side_effect=AssertionError("must not start"))
    campaign.report = lambda: None
    with pytest.raises(RuntimeError, match="unreachable"):
        campaign.run_managed()
    campaign.run.assert_not_called()
    assert campaign.state["status"] == "stopped"
    held = campaign.state["console_lifecycle"]
    assert held["on_tool_unreachable"] == "refuse"
    assert held["config"]["on_tool_unreachable"] == "refuse"
    assert not held["prepare"]["reachable"]
    assert "teardown" not in held


def test_env_on_tool_unreachable_refuse(tmp_path, monkeypatch, campaign_module):
    monkeypatch.setenv("XGPU_E0_ON_TOOL_UNREACHABLE", "refuse")
    proof, speed = inputs(tmp_path)
    campaign = campaign_module.Campaign(
        tmp_path / "campaign",
        proof,
        speed,
        lifecycle_tool=tmp_path / "missing-tool.py",
    )
    assert campaign.lifecycle.on_tool_unreachable == "refuse"
    campaign.run = Mock(side_effect=AssertionError("must not start"))
    campaign.report = lambda: None
    with pytest.raises(RuntimeError, match="unreachable"):
        campaign.run_managed()
    campaign.run.assert_not_called()
    campaign.lock.close()


def test_allow_orphan_constructor_alias(tmp_path, monkeypatch, campaign_module):
    tool = write_tool(tmp_path)
    log = tool_log(tmp_path)
    monkeypatch.setenv("LIFECYCLE_LOG", str(log))
    monkeypatch.setenv("LIFECYCLE_MODE", "orphan")
    proof, speed = inputs(tmp_path)
    campaign = campaign_module.Campaign(
        tmp_path / "campaign",
        proof,
        speed,
        lifecycle_tool=tool,
        allow_orphan=True,
    )
    assert campaign.allow_orphan is True
    assert campaign.allow_orphan_gpu is True
    campaign.run = lambda: campaign.state.update(status="completed")
    campaign.report = lambda: None
    campaign.run_managed()
    assert campaign.state["status"] == "completed"
    assert campaign.state["console_lifecycle"]["config"]["refuse_orphan"] is False


def test_campaign_cli_exposes_renamed_flags():
    import subprocess

    result = subprocess.run(
        [sys.executable, str(ROOT / "experiments/e0_campaign.py"), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "--allow-orphan" in result.stdout
    assert "--allow-orphan-gpu" in result.stdout
    assert "deprecated alias of --allow-orphan" in result.stdout
    assert "--on-tool-unreachable" in result.stdout


def test_on_tool_unreachable_config_and_environ(monkeypatch):
    monkeypatch.delenv("XGPU_E0_ON_TOOL_UNREACHABLE", raising=False)
    defaults = load_lifecycle_config(settings={})
    assert defaults.on_tool_unreachable == "continue"
    assert (
        lifecycle_environ(settings={}, config=defaults)["XGPU_E0_ON_TOOL_UNREACHABLE"]
        == "continue"
    )
    refused = load_lifecycle_config(
        settings={}, overrides={"on_tool_unreachable": "refuse"}
    )
    assert refused.on_tool_unreachable == "refuse"
    assert refused.public_dict()["on_tool_unreachable"] == "refuse"
    invalid = load_lifecycle_config(
        settings={"XGPU_E0_ON_TOOL_UNREACHABLE": "explode"}
    )
    assert invalid.on_tool_unreachable == "continue"
