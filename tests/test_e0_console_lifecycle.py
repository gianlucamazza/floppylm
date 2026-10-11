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
    DEFAULT_REFUSE_ORPHAN,
    TOOL_ENV,
    TOOL_FLAGS,
    TOOL_HEARTBEAT_INTERVAL_DEFAULT,
    heartbeat,
    heartbeat_seconds,
    idle_gpu,
    is_orphan,
    lifecycle_environ,
    load_lifecycle_config,
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

MOCK_TOOL = r"""
import json, os, sys
from pathlib import Path

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
    "--idle-cpu-percent", "--teardown-wait-seconds",
    "--process-image", "--package", "--package-family",
    "--terminate-by", "--portal-url", "--portal-port",
    "--tls-verify", "--tls-pin", "--credentials",
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
if command == "heartbeat":
    print("heartbeat: ok", flush=True)
    raise SystemExit(0)
if command == "idle-gpu":
    when = args[args.index("--when") + 1]
    orphan = mode == "orphan" and when == "before"
    after_fail = mode == "after-fail" and when == "after"
    report = {
        "when": when,
        "ok": not (orphan or after_fail),
        "reason": "orphan_gpu_signature" if orphan else "ok",
        "orphan": orphan,
        "process_present": orphan or after_fail,
        "cpu_idle": orphan,
        "engine_pinned": orphan,
        "engines": [0, 0, 0, 0, 0, 100.0 if orphan else 0.0, 0],
    }
    print(json.dumps(report, sort_keys=True), flush=True)
    raise SystemExit(0 if report["ok"] else 1)
if command == "teardown":
    report = {
        "when": "after",
        "ok": mode != "teardown-fail",
        "reason": "ok" if mode != "teardown-fail" else "process_still_running",
        "orphan": False,
        "process_present": mode == "teardown-fail",
        "terminated": True,
        "engines": [0, 0, 0, 0, 0, 0.0, 0],
    }
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
    assert tool_command(tool, "teardown")[-1] == "teardown"
    assert tool_command(tool, "idle-gpu", "--when", "after")[-2:] == ["--when", "after"]


def test_config_defaults_and_overrides(tmp_path, monkeypatch):
    for key in (
        "XGPU_HEARTBEAT_INTERVAL_SECONDS",
        "XGPU_GPU_ENGINES",
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
    assert defaults.gpu_engines is None
    assert defaults.process_images is None
    assert defaults.idle_cpu_percent is None
    assert defaults.teardown_wait_seconds is None
    assert defaults.idle_exit_seconds is None
    assert defaults.terminate_by is None

    monkeypatch.setenv("XGPU_HEARTBEAT_INTERVAL_SECONDS", "12")
    monkeypatch.setenv("XGPU_E0_REFUSE_ORPHAN", "0")
    monkeypatch.setenv("XGPU_GPU_ENGINES", "3,5")
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
            "tool": tool,
        },
    )
    assert cli.heartbeat_interval_seconds == 3
    assert cli.gpu_engines == ("9",)

    forwarded = tool_command(cli, "idle-gpu", "--when", "before")
    assert forwarded[forwarded.index("--gpu-engine") + 1] == "9"
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


def test_idle_gpu_before_detects_orphan_signature(tmp_path, monkeypatch):
    tool = write_tool(tmp_path)
    log = tool_log(tmp_path)
    monkeypatch.setenv("LIFECYCLE_LOG", str(log))
    monkeypatch.setenv("LIFECYCLE_MODE", "orphan")
    result = idle_gpu("before", tool=tool, package="pkg")
    assert result["reachable"]
    assert not result["ok"]
    assert is_orphan(result)
    assert result["report"]["reason"] == "orphan_gpu_signature"


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
    with pytest.raises(RuntimeError, match="orphan GPU signature"):
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
    assert commands[0] == "idle-gpu"
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
        "XGPU_PORTAL_PASSWORD",
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
