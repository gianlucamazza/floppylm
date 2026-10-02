"""Explicit Xbox runtime restart, then campaign --recover.

ADR 0017 forbids a looping keep-alive sidecar. After a tombstone, Device Portal
still serves stale device.json ready while XgpuE0.exe is gone, and POST
/api/taskmanager/app returns HTTP 400 both while running and while missing.
This command is the missing operator step: start the bound package with
openappx deploy --start only when the process list is empty, wait for a live
idle worker, then exec e0_campaign.py --recover.

A present process with a stale heartbeat is refused. Terminate, then recover.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from floppylm_xbox.portal import (  # noqa: E402
    Portal,
    certificate_fingerprint,
    env_file,
    read_env_file,
)

APP_ID = "App"
PROCESS_NAME = "xgpue0.exe"
START_WAIT_SECONDS = 30.0


def app_processes(portal: Portal) -> list[dict]:
    """Running processes for the bound package. device.json ready is not this."""
    listing = portal.request("GET", "/api/resourcemanager/processes", json_result=True)
    found = []
    for proc in listing.get("Processes", []):
        name = str(proc.get("ImageName") or proc.get("name") or "")
        package = str(proc.get("PackageFullName") or "")
        if package == portal.package or name.lower() == PROCESS_NAME:
            found.append(proc)
    return found


def start_package(portal: Portal, *, run=subprocess.run, which=shutil.which) -> str:
    """Start the bound package once. No-op when the process is already listed."""
    if app_processes(portal):
        return "already_running"
    openappx = which("openappx")
    if not openappx:
        raise RuntimeError("openappx is required to start XgpuE0 after a tombstone")
    settings = {**read_env_file(env_file()), **os.environ}
    password = settings.get("OPENAPPX_DEVICE_PASSWORD") or settings.get("XBOX_PASS")
    if not password:
        raise RuntimeError("missing Device Portal password for openappx")
    pin = certificate_fingerprint(settings.get("XBOX_CERT_SHA256") or portal.cert_sha256)
    if pin != portal.cert_sha256:
        raise RuntimeError("openappx TLS pin does not match Portal pin")
    user = settings.get("UWP_DEVICE_USER") or settings.get("XBOX_USER")
    if not user:
        raise RuntimeError("missing Device Portal user for openappx")
    device = settings.get("UWP_DEVICE_URL") or f"https://{portal.host}:{portal.port}"
    env = os.environ.copy()
    env["OPENAPPX_DEVICE_PASSWORD"] = password
    command = [
        openappx,
        "deploy",
        "--device",
        device,
        "--user",
        user,
        "--pin-sha256",
        pin,
        "--start",
        portal.package,
        "--app-id",
        APP_ID,
    ]
    proc = run(command, env=env, capture_output=True, text=True)
    if proc.returncode:
        detail = ((proc.stdout or "") + " " + (proc.stderr or "")).strip()
        raise RuntimeError(f"openappx --start failed: {detail[:1000]}")
    deadline = time.monotonic() + START_WAIT_SECONDS
    while time.monotonic() < deadline:
        if app_processes(portal):
            return "started"
        time.sleep(1)
    raise TimeoutError("XgpuE0 process did not appear after openappx --start")


def prepare_idle_worker(portal: Portal, *, commit: str | None = None, restart_if_missing: bool):
    """Live idle-capable worker. Restart only when the process list is empty."""
    if app_processes(portal):
        return portal.live_worker(commit=commit)
    if not restart_if_missing:
        raise RuntimeError("XgpuE0 process missing; explicit app restart required")
    start_package(portal)
    return portal.live_worker(commit=commit)


def campaign_command(out: Path, acceptance: Path, benchmark: Path) -> list[str]:
    return [
        sys.executable,
        "-u",
        str(ROOT / "experiments/e0_campaign.py"),
        "--out",
        str(out),
        "--acceptance",
        str(acceptance),
        "--benchmark",
        str(benchmark),
        "--recover",
    ]


def prepare_campaign_runtime(out: Path, acceptance: Path, benchmark: Path, *, portal=None):
    """Verify the bound package, start it if missing, require a live worker."""
    state = json.loads((out / "campaign.json").read_text())
    proof = json.loads(acceptance.read_text())
    speed = json.loads(benchmark.read_text())
    if state.get("package") != proof.get("package") or proof.get("package") != speed.get("package"):
        raise RuntimeError("recovery package mismatch")
    if state.get("commit") != proof.get("commit") or proof.get("commit") != speed.get("commit"):
        raise RuntimeError("recovery source commit mismatch")
    portal = portal or Portal.configured(state["package"])
    if portal.package != state["package"]:
        raise RuntimeError("Portal package differs from campaign")
    device = json.loads(portal.get("device.json", ""))
    if device.get("package") != state["package"] or device.get("commit") != state["commit"]:
        raise RuntimeError("device package/source differs from campaign")
    if not device.get("hardware_gpu"):
        raise RuntimeError("recovery requires hardware GPU")
    missing = not app_processes(portal)
    worker = prepare_idle_worker(portal, commit=state["commit"], restart_if_missing=True)
    if worker["state"] not in ("ready", "running"):
        raise RuntimeError("worker is not ready for recovery")
    if worker["state"] == "ready" and worker.get("active_job") is not None:
        raise RuntimeError("idle worker still publishes an active job")
    return {"device": device, "worker": worker, "process_was_missing": missing}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--acceptance", type=Path, required=True)
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument(
        "--prepare-only",
        action="store_true",
        help="start a missing process and wait for a live worker; do not exec --recover",
    )
    args = parser.parse_args()
    prepare_campaign_runtime(args.out, args.acceptance, args.benchmark)
    if args.prepare_only:
        return 0
    command = campaign_command(args.out, args.acceptance, args.benchmark)
    os.execv(command[0], command)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
