"""Invoke xbox-gpu-training `scripts/e0_console_lifecycle.py` (PR #46).

Device Portal terminate, CSRF echo and idle-GPU detection stay in that tool.
This module only locates it, maps FloppyLM settings onto its environment, and
records the JSON it prints. It never prints credentials and never opens a
Device Portal connection itself.

Every value the runner forwards is resolved by `load_lifecycle_config`:
CLI / constructor overrides, then campaign.json `console_lifecycle.config`,
then `$FLOPPYLM_E0_LIFECYCLE_CONFIG`, then environment variables, then the
documented defaults. Detection thresholds and process identity are omitted
unless set, so the companion tool can use generic engine/adapter detection
and terminate by package or pid. See docs/operations/e0-console-lifecycle.md.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from floppylm import runlog

from .portal import DEFAULT_PORT, env_file, read_env_file

TOOL_ENV = "XGPU_E0_CONSOLE_LIFECYCLE"
CONFIG_FILE_ENV = "FLOPPYLM_E0_LIFECYCLE_CONFIG"
HEARTBEAT_ENV = "XGPU_E0_HOST_HEARTBEAT_SECONDS"
DEFAULT_HEARTBEAT_SECONDS = 300.0
DEFAULT_REFUSE_ORPHAN = True

# Env names for each configurable field. Connection aliases (XBOX_*) are applied
# in lifecycle_environ; these are the canonical lifecycle keys.
ENV_KEYS = {
    "tool": TOOL_ENV,
    "heartbeat_seconds": HEARTBEAT_ENV,
    "teardown_wait_seconds": "XGPU_E0_TEARDOWN_WAIT_SECONDS",
    "refuse_orphan": "XGPU_E0_REFUSE_ORPHAN",
    "package": "XGPU_E0_PACKAGE",
    "image": "XGPU_E0_APP_IMAGE",
    "pid": "XGPU_E0_PID",
    "adapter": "XGPU_E0_GPU_ADAPTER",
    "engine": "XGPU_E0_GPU_ENGINE",
    "engine_percent": "XGPU_E0_GPU_ENGINE_PERCENT",
    "cpu_idle_percent": "XGPU_E0_IDLE_CPU_PERCENT",
    "device_url": "UWP_DEVICE_URL",
}

# Companion CLI flags (xbox-gpu-training#46, configurable). Only emitted when set.
TOOL_FLAGS = {
    "package": "--package",
    "image": "--image",
    "pid": "--pid",
    "adapter": "--adapter",
    "engine": "--engine",
    "engine_percent": "--engine-percent",
    "cpu_idle_percent": "--cpu-idle-percent",
}

POLICY_FIELDS = (
    "heartbeat_seconds",
    "teardown_wait_seconds",
    "refuse_orphan",
    "package",
    "image",
    "pid",
    "adapter",
    "engine",
    "engine_percent",
    "cpu_idle_percent",
)


@dataclass
class LifecycleConfig:
    """Portable settings for the companion lifecycle tool. None = do not pass."""

    tool: Path | None = None
    heartbeat_seconds: float = DEFAULT_HEARTBEAT_SECONDS
    teardown_wait_seconds: float | None = None
    refuse_orphan: bool = DEFAULT_REFUSE_ORPHAN
    package: str | None = None
    image: str | None = None
    pid: str | None = None
    adapter: str | None = None
    engine: str | None = None
    engine_percent: str | None = None
    cpu_idle_percent: str | None = None
    device_url: str | None = None

    def public_dict(self) -> dict:
        """Policy snapshot for campaign.json. No credentials or host secrets."""
        data = {}
        for name in POLICY_FIELDS:
            value = getattr(self, name)
            if value is not None:
                data[name] = value
        if self.tool is not None:
            data["tool"] = str(self.tool)
        return data


def _as_bool(value: Any, default: bool) -> bool:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() not in ("0", "false", "no", "off")


def _as_float(value: Any, default: float | None) -> float | None:
    if value is None or value == "":
        return default
    return float(value)


def _as_optional(value: Any) -> str | None:
    if value is None or value == "":
        return None
    return str(value)


def _as_path(value: Any) -> Path | None:
    if value is None or value == "":
        return None
    return Path(value).expanduser()


def _read_json_object(path: Path) -> dict:
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    nested = data.get("console_lifecycle")
    if isinstance(nested, dict) and isinstance(nested.get("config"), dict):
        return nested["config"]
    if isinstance(data.get("config"), dict):
        return data["config"]
    if data.get("schema") == "floppylm.e0.campaign.v1":
        return {}
    return data


def _layer_from_mapping(raw: dict[str, Any]) -> dict[str, Any]:
    """Accept both field names and env-key names."""
    inverse = {env: field for field, env in ENV_KEYS.items()}
    layer: dict[str, Any] = {}
    for key, value in raw.items():
        field = key if key in ENV_KEYS else inverse.get(key)
        if field is None or value is None:
            continue
        layer[field] = value
    return layer


def load_lifecycle_config(
    *,
    campaign_root: Path | None = None,
    config_path: str | Path | None = None,
    settings: dict[str, str] | None = None,
    overrides: dict[str, Any] | None = None,
) -> LifecycleConfig:
    """Resolve settings. Overrides beat campaign config beat file beat env beat defaults."""
    settings = settings if settings is not None else {**read_env_file(env_file()), **os.environ}
    merged: dict[str, Any] = {
        "heartbeat_seconds": DEFAULT_HEARTBEAT_SECONDS,
        "refuse_orphan": DEFAULT_REFUSE_ORPHAN,
    }
    env_layer = {field: settings[env] for field, env in ENV_KEYS.items() if settings.get(env)}
    if not env_layer.get("device_url") and settings.get("XBOX_IP"):
        port = settings.get("XBOX_PORT") or str(DEFAULT_PORT)
        env_layer["device_url"] = f"https://{settings['XBOX_IP']}:{port}"
    merged.update(env_layer)
    file_path = _as_path(config_path if config_path is not None else settings.get(CONFIG_FILE_ENV))
    if file_path and file_path.is_file():
        merged.update(_layer_from_mapping(_read_json_object(file_path)))
    if campaign_root is not None:
        campaign = Path(campaign_root) / "campaign.json"
        if campaign.is_file():
            merged.update(_layer_from_mapping(_read_json_object(campaign)))
    if overrides:
        merged.update({key: value for key, value in overrides.items() if value is not None})
    return LifecycleConfig(
        tool=_as_path(merged.get("tool")),
        heartbeat_seconds=_as_float(merged.get("heartbeat_seconds"), DEFAULT_HEARTBEAT_SECONDS)
        or DEFAULT_HEARTBEAT_SECONDS,
        teardown_wait_seconds=_as_float(merged.get("teardown_wait_seconds"), None),
        refuse_orphan=_as_bool(merged.get("refuse_orphan"), DEFAULT_REFUSE_ORPHAN),
        package=_as_optional(merged.get("package")),
        image=_as_optional(merged.get("image")),
        pid=_as_optional(merged.get("pid")),
        adapter=_as_optional(merged.get("adapter")),
        engine=_as_optional(merged.get("engine")),
        engine_percent=_as_optional(merged.get("engine_percent")),
        cpu_idle_percent=_as_optional(merged.get("cpu_idle_percent")),
        device_url=_as_optional(merged.get("device_url")),
    )


def resolve_tool(explicit: str | Path | None = None) -> Path | None:
    """Configured tool path, or None when the operator has not pointed at one."""
    if explicit is not None:
        return _as_path(explicit)
    return load_lifecycle_config().tool


def heartbeat_seconds(explicit: float | None = None) -> float:
    if explicit is not None:
        return float(explicit)
    return load_lifecycle_config().heartbeat_seconds


def lifecycle_environ(
    settings: dict[str, str] | None = None, config: LifecycleConfig | None = None
) -> dict[str, str]:
    """Translate FloppyLM / openappx settings into the tool's UWP_* names."""
    settings = settings if settings is not None else {**read_env_file(env_file()), **os.environ}
    config = config or load_lifecycle_config(settings=settings)
    env = os.environ.copy()
    url = config.device_url or settings.get("UWP_DEVICE_URL")
    if not url and settings.get("XBOX_IP"):
        url = f"https://{settings['XBOX_IP']}:{settings.get('XBOX_PORT') or DEFAULT_PORT}"
    if url:
        env["UWP_DEVICE_URL"] = url
    user = settings.get("UWP_DEVICE_USER") or settings.get("XBOX_USER")
    if user:
        env["UWP_DEVICE_USER"] = user
    password = settings.get("OPENAPPX_DEVICE_PASSWORD") or settings.get("XBOX_PASS")
    if password:
        env["OPENAPPX_DEVICE_PASSWORD"] = password
    pin = settings.get("OPENAPPX_DEVICE_PIN") or settings.get("XBOX_CERT_SHA256")
    if pin:
        env["OPENAPPX_DEVICE_PIN"] = pin.replace(":", "").lower()
    for field, env_key in ENV_KEYS.items():
        value = getattr(config, field)
        if field == "tool" or value in (None, ""):
            continue
        if field == "refuse_orphan":
            env[env_key] = "1" if value else "0"
        else:
            env[env_key] = str(value)
    return env


def _flag_value(value: Any) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def tool_command(
    tool: Path | LifecycleConfig,
    command: str,
    *args: str,
    package: str = "",
    config: LifecycleConfig | None = None,
) -> list[str]:
    """Configurable PR #46 CLI: `python TOOL [identity flags] CMD [cmd flags]`."""
    cfg = config
    if isinstance(tool, LifecycleConfig):
        cfg = tool
        path = tool.tool
    else:
        path = Path(tool)
        cfg = cfg or replace(load_lifecycle_config(), tool=path, package=package or None)
    if package:
        cfg = replace(cfg, package=package)
    if path is None:
        raise ValueError("lifecycle tool path is not configured")
    argv = [sys.executable, str(path)]
    for field, flag in TOOL_FLAGS.items():
        value = getattr(cfg, field)
        if value not in (None, ""):
            argv += [flag, _flag_value(value)]
    argv.append(command)
    argv.extend(args)
    if command == "teardown" and cfg.teardown_wait_seconds is not None:
        argv += ["--wait-seconds", _flag_value(cfg.teardown_wait_seconds)]
    return argv


def run_tool(
    command: str,
    *args: str,
    tool: str | Path | None = None,
    package: str = "",
    config: LifecycleConfig | None = None,
    timeout: float | None = None,
    run=subprocess.run,
) -> dict:
    """Run one subcommand. Unreachable tool/console is an `ok=False` dict, not a raise."""
    result: dict = {"command": command, "args": list(args), "ok": False, "reachable": False}
    cfg = config or load_lifecycle_config(overrides={"tool": tool, "package": package or None})
    if tool is not None:
        cfg = replace(cfg, tool=_as_path(tool))
    if package:
        cfg = replace(cfg, package=package)
    if cfg.tool is None:
        result["error"] = f"{TOOL_ENV} is unset and no --lifecycle-tool was given"
        return result
    result["tool"] = str(cfg.tool)
    if not cfg.tool.is_file():
        result["error"] = f"lifecycle tool not found: {cfg.tool}"
        return result
    argv = tool_command(cfg, command, *args)
    result["argv"] = argv
    try:
        proc = run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=lifecycle_environ(config=cfg),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        result["error"] = repr(exc)
        return result
    result["reachable"] = True
    result["returncode"] = proc.returncode
    stdout = (proc.stdout or "").strip()
    stderr = (proc.stderr or "").strip()
    if stdout:
        result["stdout"] = stdout
        try:
            result["report"] = json.loads(stdout)
        except json.JSONDecodeError:
            pass
    if stderr:
        result["stderr"] = stderr
    if command == "heartbeat":
        result["ok"] = proc.returncode == 0 and stdout == "heartbeat: ok"
    elif "report" in result:
        result["ok"] = bool(result["report"].get("ok"))
    else:
        result["ok"] = proc.returncode == 0
        if not result["ok"]:
            result["error"] = stderr or stdout or f"exit {proc.returncode}"
    return result


def idle_gpu(when: str, **kwargs) -> dict:
    if when not in ("before", "after"):
        raise ValueError("when must be before or after")
    return run_tool("idle-gpu", "--when", when, **kwargs)


def heartbeat(**kwargs) -> dict:
    return run_tool("heartbeat", **kwargs)


def teardown(*, wait_seconds: float | None = None, **kwargs) -> dict:
    config = kwargs.pop("config", None)
    if wait_seconds is not None:
        config = replace(
            config or load_lifecycle_config(), teardown_wait_seconds=wait_seconds
        )
    return run_tool("teardown", config=config, **kwargs)


def is_orphan(result: dict) -> bool:
    report = result.get("report") or {}
    return bool(report.get("orphan") or report.get("reason") == "orphan_gpu_signature")


def stop_console(
    *,
    tool: str | Path | None = None,
    package: str = "",
    wait_seconds: float | None = None,
    config: LifecycleConfig | None = None,
    run=subprocess.run,
) -> dict:
    """`teardown` then `idle-gpu --when after`. Never raises."""
    cfg = config or load_lifecycle_config(overrides={"tool": tool, "package": package or None})
    if tool is not None:
        cfg = replace(cfg, tool=_as_path(tool))
    if package:
        cfg = replace(cfg, package=package)
    if wait_seconds is not None:
        cfg = replace(cfg, teardown_wait_seconds=wait_seconds)
    torn = teardown(config=cfg, run=run)
    after = idle_gpu("after", config=cfg, run=run)
    return {
        "teardown": torn,
        "idle_gpu_after": after,
        "ok": bool(torn.get("ok") and after.get("ok")),
    }


def record_console_lifecycle(root: Path, update: dict) -> None:
    """Merge into campaign.json and summary.json. Never raises."""
    try:
        stamp = runlog.now()
        for name in ("campaign.json", "summary.json"):
            path = Path(root) / name
            if not path.is_file():
                continue
            data = json.loads(path.read_text())
            current = data.get("console_lifecycle")
            if not isinstance(current, dict):
                current = {}
            current.update(update)
            current["updated"] = stamp
            data["console_lifecycle"] = current
            runlog.write_json(path, data)
    except Exception as exc:
        print(f"console lifecycle record failed: {exc}", flush=True)
