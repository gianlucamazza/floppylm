"""Invoke xbox-gpu-training `scripts/e0_console_lifecycle.py` (PR #46).

Device Portal terminate, CSRF echo and idle-GPU detection stay in that tool.
This module locates it, forwards the exact CLI/env names from
xbox-gpu-training `docs/e0/lifecycle.md`, and records the JSON it prints.
It never prints credentials, never puts a password on the command line, and
never opens a Device Portal connection itself.

Resolution: CLI / constructor overrides, then campaign.json
`console_lifecycle.config`, then `$FLOPPYLM_E0_LIFECYCLE_CONFIG`, then
environment, then omit (so the tool's documented defaults apply).
See docs/operations/e0-console-lifecycle.md.
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
HEARTBEAT_ENV = "XGPU_HEARTBEAT_INTERVAL_SECONDS"
# Runner thread only, when the interval is unset. Matches #46's documented default.
TOOL_HEARTBEAT_INTERVAL_DEFAULT = 30.0
DEFAULT_REFUSE_ORPHAN = True

# Canonical env names from xbox-gpu-training docs/e0/lifecycle.md.
ENV_KEYS = {
    "tool": TOOL_ENV,
    "idle_exit_seconds": "XGPU_IDLE_EXIT_SECONDS",
    "heartbeat_interval_seconds": HEARTBEAT_ENV,
    "heartbeat_stale_seconds": "XGPU_HEARTBEAT_STALE_SECONDS",
    "poll_interval_seconds": "XGPU_POLL_INTERVAL_SECONDS",
    "gpu_threshold_percent": "XGPU_GPU_THRESHOLD_PERCENT",
    "gpu_sample_count": "XGPU_GPU_SAMPLE_COUNT",
    "gpu_sample_interval_seconds": "XGPU_GPU_SAMPLE_INTERVAL_SECONDS",
    "gpu_engines": "XGPU_GPU_ENGINES",
    "idle_cpu_percent": "XGPU_IDLE_CPU_PERCENT",
    "teardown_wait_seconds": "XGPU_TEARDOWN_WAIT_SECONDS",
    "process_images": "XGPU_PROCESS_IMAGES",
    "package": "XGPU_E0_PACKAGE",
    "package_family": "XGPU_PACKAGE_FAMILY",
    "terminate_by": "XGPU_TERMINATE_BY",
    "portal_url": "XGPU_PORTAL_URL",
    "portal_port": "XGPU_PORTAL_PORT",
    "tls_verify": "XGPU_PORTAL_TLS_VERIFY",
    "tls_pin": "XGPU_PORTAL_TLS_PIN",
    "credentials": "XGPU_PORTAL_CREDENTIALS",
    "refuse_orphan": "XGPU_E0_REFUSE_ORPHAN",
}

ENV_ALIASES = {
    "portal_url": ("UWP_DEVICE_URL",),
    "tls_pin": ("OPENAPPX_DEVICE_PIN", "XBOX_CERT_SHA256"),
}

# Scalar flags forwarded only when set. Password is never a flag.
SCALAR_FLAGS = {
    "idle_exit_seconds": "--idle-exit-seconds",
    "heartbeat_interval_seconds": "--heartbeat-interval-seconds",
    "heartbeat_stale_seconds": "--heartbeat-stale-seconds",
    "poll_interval_seconds": "--poll-interval-seconds",
    "gpu_threshold_percent": "--gpu-threshold-percent",
    "gpu_sample_count": "--gpu-sample-count",
    "gpu_sample_interval_seconds": "--gpu-sample-interval-seconds",
    "idle_cpu_percent": "--idle-cpu-percent",
    "teardown_wait_seconds": "--teardown-wait-seconds",
    "package": "--package",
    "package_family": "--package-family",
    "portal_url": "--portal-url",
    "portal_port": "--portal-port",
    "tls_verify": "--tls-verify",
    "tls_pin": "--tls-pin",
    "credentials": "--credentials",
}

REPEAT_FLAGS = {
    "gpu_engines": "--gpu-engine",
    "process_images": "--process-image",
    "terminate_by": "--terminate-by",
}

TOOL_FLAGS = {**SCALAR_FLAGS, **REPEAT_FLAGS}

LIST_FIELDS = frozenset(REPEAT_FLAGS)
SECRET_FIELDS = frozenset({"password"})
POLICY_FIELDS = (
    "idle_exit_seconds",
    "heartbeat_interval_seconds",
    "heartbeat_stale_seconds",
    "poll_interval_seconds",
    "gpu_threshold_percent",
    "gpu_sample_count",
    "gpu_sample_interval_seconds",
    "gpu_engines",
    "idle_cpu_percent",
    "teardown_wait_seconds",
    "process_images",
    "package",
    "package_family",
    "terminate_by",
    "portal_port",
    "tls_verify",
    "refuse_orphan",
)


@dataclass
class LifecycleConfig:
    """Portable settings for the companion tool. None = do not pass a flag."""

    tool: Path | None = None
    idle_exit_seconds: float | None = None
    heartbeat_interval_seconds: float | None = None
    heartbeat_stale_seconds: float | None = None
    poll_interval_seconds: float | None = None
    gpu_threshold_percent: float | None = None
    gpu_sample_count: float | None = None
    gpu_sample_interval_seconds: float | None = None
    gpu_engines: tuple[str, ...] | None = None
    idle_cpu_percent: float | None = None
    teardown_wait_seconds: float | None = None
    process_images: tuple[str, ...] | None = None
    package: str | None = None
    package_family: str | None = None
    terminate_by: tuple[str, ...] | None = None
    portal_url: str | None = None
    portal_port: float | None = None
    tls_verify: str | None = None
    tls_pin: str | None = None
    credentials: str | None = None
    refuse_orphan: bool = DEFAULT_REFUSE_ORPHAN
    password: str | None = None

    def public_dict(self) -> dict:
        """Policy snapshot for campaign.json. No password or credential secret."""
        data = {}
        for name in POLICY_FIELDS:
            value = getattr(self, name)
            if value is not None:
                data[name] = list(value) if isinstance(value, tuple) else value
        if self.tool is not None:
            data["tool"] = str(self.tool)
        return data


def _as_bool(value: Any, default: bool) -> bool:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() not in ("0", "false", "no", "off")


def _as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def _as_optional(value: Any) -> str | None:
    if value is None or value == "":
        return None
    return str(value)


def _as_path(value: Any) -> Path | None:
    if value is None or value == "":
        return None
    return Path(value).expanduser()


def _as_list(value: Any) -> tuple[str, ...] | None:
    if value is None or value == "":
        return None
    if isinstance(value, (list, tuple)):
        items = tuple(str(item).strip() for item in value if str(item).strip())
        return items or None
    items = tuple(part.strip() for part in str(value).split(",") if part.strip())
    return items or None


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
    """Accept field names and env-key names from docs/e0/lifecycle.md."""
    inverse = {env: field for field, env in ENV_KEYS.items()}
    layer: dict[str, Any] = {}
    for key, value in raw.items():
        if key in SECRET_FIELDS:
            continue
        field = key if key in ENV_KEYS else inverse.get(key)
        if field is None or value is None:
            continue
        layer[field] = value
    return layer


def _env_lookup(settings: dict[str, str], field: str) -> str | None:
    names = (ENV_KEYS[field],) + ENV_ALIASES.get(field, ())
    for name in names:
        if settings.get(name):
            return settings[name]
    return None


def load_lifecycle_config(
    *,
    campaign_root: Path | None = None,
    config_path: str | Path | None = None,
    settings: dict[str, str] | None = None,
    overrides: dict[str, Any] | None = None,
) -> LifecycleConfig:
    """Resolve settings. Overrides beat campaign config beat file beat env. Unset stays None."""
    settings = settings if settings is not None else {**read_env_file(env_file()), **os.environ}
    merged: dict[str, Any] = {"refuse_orphan": DEFAULT_REFUSE_ORPHAN}
    env_layer = {
        field: value
        for field in ENV_KEYS
        if (value := _env_lookup(settings, field)) is not None
    }
    if not env_layer.get("portal_url") and settings.get("XBOX_IP"):
        port = settings.get("XBOX_PORT") or settings.get("XGPU_PORTAL_PORT") or str(DEFAULT_PORT)
        env_layer["portal_url"] = f"https://{settings['XBOX_IP']}:{port}"
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
    password = (
        settings.get("XGPU_PORTAL_PASSWORD")
        or settings.get("OPENAPPX_DEVICE_PASSWORD")
        or settings.get("XBOX_PASS")
        or None
    )
    return LifecycleConfig(
        tool=_as_path(merged.get("tool")),
        idle_exit_seconds=_as_float(merged.get("idle_exit_seconds")),
        heartbeat_interval_seconds=_as_float(merged.get("heartbeat_interval_seconds")),
        heartbeat_stale_seconds=_as_float(merged.get("heartbeat_stale_seconds")),
        poll_interval_seconds=_as_float(merged.get("poll_interval_seconds")),
        gpu_threshold_percent=_as_float(merged.get("gpu_threshold_percent")),
        gpu_sample_count=_as_float(merged.get("gpu_sample_count")),
        gpu_sample_interval_seconds=_as_float(merged.get("gpu_sample_interval_seconds")),
        gpu_engines=_as_list(merged.get("gpu_engines")),
        idle_cpu_percent=_as_float(merged.get("idle_cpu_percent")),
        teardown_wait_seconds=_as_float(merged.get("teardown_wait_seconds")),
        process_images=_as_list(merged.get("process_images")),
        package=_as_optional(merged.get("package")),
        package_family=_as_optional(merged.get("package_family")),
        terminate_by=_as_list(merged.get("terminate_by")),
        portal_url=_as_optional(merged.get("portal_url")),
        portal_port=_as_float(merged.get("portal_port")),
        tls_verify=_as_optional(merged.get("tls_verify")),
        tls_pin=_as_optional(merged.get("tls_pin")),
        credentials=_as_optional(merged.get("credentials")),
        refuse_orphan=_as_bool(merged.get("refuse_orphan"), DEFAULT_REFUSE_ORPHAN),
        password=_as_optional(password),
    )


def resolve_tool(explicit: str | Path | None = None) -> Path | None:
    """Configured tool path, or None when the operator has not pointed at one."""
    if explicit is not None:
        return _as_path(explicit)
    return load_lifecycle_config().tool


def heartbeat_seconds(explicit: float | None = None) -> float:
    if explicit is not None:
        return float(explicit)
    configured = load_lifecycle_config().heartbeat_interval_seconds
    return TOOL_HEARTBEAT_INTERVAL_DEFAULT if configured is None else configured


def lifecycle_environ(
    settings: dict[str, str] | None = None, config: LifecycleConfig | None = None
) -> dict[str, str]:
    """Map FloppyLM / openappx settings onto the tool's XGPU_* names. No password on argv."""
    settings = settings if settings is not None else {**read_env_file(env_file()), **os.environ}
    config = config or load_lifecycle_config(settings=settings)
    env = os.environ.copy()
    url = config.portal_url or settings.get("XGPU_PORTAL_URL") or settings.get("UWP_DEVICE_URL")
    if not url and settings.get("XBOX_IP"):
        port = settings.get("XBOX_PORT") or settings.get("XGPU_PORTAL_PORT") or str(DEFAULT_PORT)
        url = f"https://{settings['XBOX_IP']}:{port}"
    if url:
        env["XGPU_PORTAL_URL"] = url
        env["UWP_DEVICE_URL"] = url
    user = (
        settings.get("XGPU_PORTAL_USER")
        or settings.get("UWP_DEVICE_USER")
        or settings.get("XBOX_USER")
    )
    if user:
        env["XGPU_PORTAL_USER"] = user
        env["UWP_DEVICE_USER"] = user
    password = (
        config.password
        or settings.get("XGPU_PORTAL_PASSWORD")
        or settings.get("OPENAPPX_DEVICE_PASSWORD")
        or settings.get("XBOX_PASS")
    )
    if password:
        env["XGPU_PORTAL_PASSWORD"] = password
        env["OPENAPPX_DEVICE_PASSWORD"] = password
    pin = config.tls_pin or settings.get("XGPU_PORTAL_TLS_PIN") or settings.get(
        "OPENAPPX_DEVICE_PIN"
    ) or settings.get("XBOX_CERT_SHA256")
    if pin:
        env["XGPU_PORTAL_TLS_PIN"] = pin.replace(":", "").lower()
        env["OPENAPPX_DEVICE_PIN"] = env["XGPU_PORTAL_TLS_PIN"]
    for field, env_key in ENV_KEYS.items():
        if field in ("tool", "refuse_orphan"):
            continue
        value = getattr(config, field)
        if value in (None, ""):
            continue
        env[env_key] = ",".join(value) if isinstance(value, tuple) else str(value)
    if config.refuse_orphan is not None:
        env["XGPU_E0_REFUSE_ORPHAN"] = "1" if config.refuse_orphan else "0"
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
    """Exact #46 CLI: `python TOOL [global flags] CMD [cmd flags]`. Password is never a flag."""
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
    for field, flag in SCALAR_FLAGS.items():
        value = getattr(cfg, field)
        if value not in (None, ""):
            argv += [flag, _flag_value(value)]
    for field, flag in REPEAT_FLAGS.items():
        values = getattr(cfg, field)
        if values:
            for item in values:
                argv += [flag, str(item)]
    argv.append(command)
    argv.extend(args)
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
    if any(flag in {"--password", "--pass", "-p"} for flag in argv):
        raise RuntimeError("password must not be a CLI flag")
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
