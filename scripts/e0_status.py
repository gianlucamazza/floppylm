"""Read frozen campaign provenance and optional live Xbox progress without mutating jobs."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from http.client import HTTPException
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from floppylm import runlog  # noqa: E402
from floppylm_xbox.runtime import RuntimeMonitor  # noqa: E402

TRANSPORT_ERRORS = (OSError, HTTPException)


def host_status(value: dict, path: Path) -> str:
    state = value.get("state", value.get("status", "unknown"))
    if state == "stopping":
        state = "running"
    return runlog.host_liveness({**value, "state": state}, path / "worker.lock")


def read(path: Path) -> dict:
    return json.loads(path.read_text())


def report(
    campaign: Path, *, workspace: Path = ROOT, portal=None, monitors=None, observed_at=None
) -> dict:
    state = read(campaign / "campaign.json")
    frozen = state["sources"]["files"]
    actual = runlog.source_files(workspace)
    drift = sorted(
        name for name in frozen.keys() | actual.keys() if frozen.get(name) != actual.get(name)
    )
    result = {
        "campaign": state["id"],
        "state": state["status"],
        "phase": state["phase"],
        "package": state["package"],
        "commit": state["commit"],
        "source_drift": drift,
        "host_liveness": host_status(state, campaign),
        "provenance": {"sources": "drift" if drift else "matching", "device": "unqueried"},
        "issues": ["Frozen source files changed"] if drift else [],
        "trial_counts": {},
    }
    if result["host_liveness"] in (
        "dead",
        "identity_mismatch",
        "lock_abandoned",
        "lock_owner_mismatch",
    ):
        result["issues"].append("Campaign host is not a live lock owner")
    for record in state["trials"].values():
        counts = result["trial_counts"]
        counts[record["status"]] = counts.get(record["status"], 0) + 1
    if "error" in state:
        result["error"] = state["error"]
    if state["status"] == "stopped":
        result["issues"].append("Campaign stopped; inspect the recorded error before recovery")
    pending = [r for r in state["trials"].values() if r["status"] == "reserved"]
    if len(pending) > 1:
        result["issues"].append("Multiple reserved trials; inspect campaign state")
    if portal is not None:
        try:
            device = json.loads(portal.get("device.json", ""))
        except TRANSPORT_ERRORS as error:
            result["provenance"]["device"] = "unknown"
            result["device_transport_error"] = str(error)
            result["issues"].append("Device provenance transport unknown")
        else:
            result["device"] = device
            mismatch = any(device.get(k) != state[k] for k in ("package", "commit"))
            result["provenance"]["device"] = "mismatch" if mismatch else "matching"
            if mismatch:
                result["issues"].append("Device differs from accepted campaign package/source")
    if not pending:
        return result
    record = pending[-1]
    run_id = record["run_id"]
    if "repair_id" in record and (workspace / "runs" / record["repair_id"]).exists():
        run_id = record["repair_id"]
    run = workspace / "runs" / run_id
    trial = {
        "run_id": run_id,
        "reservation_state": record["status"],
        "host_liveness": "unverified",
        "runtime": {"liveness": "unqueried", "progress": "unverified"},
    }
    result["trial"] = trial
    if (run / "status.json").exists():
        trial["host"] = read(run / "status.json")
        trial["host_liveness"] = host_status(trial["host"], run)
        if trial["host_liveness"] in (
            "dead",
            "identity_mismatch",
            "lock_abandoned",
            "lock_owner_mismatch",
        ):
            result["issues"].append("Host trial is not a live lock owner")
        if trial["host"]["state"] in ("failed", "interrupted"):
            result["issues"].append("Host trial requires diagnosis or explicit recovery")
    if (run / "manifest.json").exists():
        trial["schedule"] = read(run / "manifest.json")["schedule"]
    submitted = run / "xbox/submitted.json"
    if not submitted.exists():
        trial["console_state"] = "waiting_for_submission"
        return result
    binding = read(submitted)
    trial["job_sha256"] = binding["sha256"]
    if binding["package"] != state["package"]:
        result["issues"].append("Submitted package differs from campaign")
    if portal is not None:
        try:
            native = portal.status(run_id)
        except FileNotFoundError:
            trial["console_state"] = "waiting_for_worker"
            trial["runtime"]["liveness"] = "unavailable"
        except TRANSPORT_ERRORS as error:
            trial["console_state"] = "unknown"
            trial["runtime"].update(liveness="unknown", transport_error=str(error))
            result["issues"].append("Console report transport unknown")
        else:
            trial["console"] = native
            if native.get("job_sha256") != binding["sha256"]:
                result["issues"].append("Console job hash differs from submitted job")
            if not native.get("hardware_gpu"):
                result["issues"].append("Console report lacks hardware GPU provenance")
            if native["state"] in ("failed", "interrupted"):
                result["issues"].append("Console trial requires diagnosis or explicit recovery")
            if native["state"] == "running":
                try:
                    worker = portal.worker(commit=state["commit"])
                except (FileNotFoundError, RuntimeError) as error:
                    trial["runtime"].update(liveness="unavailable", error=str(error))
                    result["issues"].append("Worker runtime contract unavailable")
                except TRANSPORT_ERRORS as error:
                    trial["runtime"].update(liveness="unknown", transport_error=str(error))
                    result["issues"].append("Worker heartbeat transport unknown")
                else:
                    key = (run_id, binding["sha256"])
                    monitors = {} if monitors is None else monitors
                    monitor = monitors.setdefault(key, RuntimeMonitor(*key))
                    trial["runtime"] = monitor.observe(
                        native, worker, time.monotonic() if observed_at is None else observed_at
                    )
                    result["issues"].extend(trial["runtime"]["issues"])
            else:
                trial["runtime"]["liveness"] = "not_applicable"
    return result


def watch(
    campaign: Path,
    *,
    workspace: Path = ROOT,
    portal=None,
    interval=5.0,
    duration=None,
    observations: Path | None = None,
    clock=time.monotonic,
    sleep=time.sleep,
    emit=print,
) -> int:
    """Observe monotonically timed evidence, durably, without controlling the worker."""
    monitors = {}
    started = clock()
    observations = observations or campaign / "monitor.jsonl"
    observations.parent.mkdir(parents=True, exist_ok=True)
    last_issues = set()
    while True:
        result = report(
            campaign, workspace=workspace, portal=portal, monitors=monitors, observed_at=clock()
        )
        current = set(result["issues"])
        result.update(
            observed_at=runlog.now(),
            elapsed_seconds=clock() - started,
            events=sorted(current - last_issues),
            cleared=sorted(last_issues - current),
        )
        last_issues = current
        with observations.open("a") as file:
            file.write(json.dumps(result, sort_keys=True) + "\n")
            file.flush()
            os.fsync(file.fileno())
        snapshot = observations.with_suffix(".json")
        if snapshot == observations:
            snapshot = observations.with_suffix(".latest.json")
        runlog.write_json(snapshot, result)
        emit(json.dumps(result, sort_keys=True))
        remaining = None if duration is None else duration - (clock() - started)
        if remaining is not None and remaining <= 0:
            return int(bool(result["issues"]))
        sleep(interval if remaining is None else min(interval, remaining))


def positive_seconds(text):
    value = float(text)
    if not 0 < value < float("inf"):
        raise argparse.ArgumentTypeError("seconds must be positive and finite")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, required=True)
    parser.add_argument("--xbox", action="store_true", help="query live device and bound job")
    parser.add_argument(
        "--watch",
        nargs="?",
        type=positive_seconds,
        const=5.0,
        metavar="SECONDS",
        help="observe over time (default interval: 5 seconds)",
    )
    parser.add_argument(
        "--duration", type=positive_seconds, help="stop watch after this many seconds"
    )
    parser.add_argument(
        "--observations", type=Path, help="watch journal (default: campaign/monitor.jsonl)"
    )
    args = parser.parse_args()
    if args.watch is None and (args.duration is not None or args.observations is not None):
        parser.error("--duration and --observations require --watch")
    portal = None
    if args.xbox:
        from floppylm_xbox.portal import Portal

        portal = Portal.configured(read(args.campaign / "campaign.json")["package"])
    if args.watch is not None:
        return watch(
            args.campaign,
            portal=portal,
            interval=args.watch,
            duration=args.duration,
            observations=args.observations,
        )
    result = report(args.campaign, portal=portal)
    print(json.dumps(result, indent=2))
    return int(bool(result["issues"]))


if __name__ == "__main__":
    raise SystemExit(main())
