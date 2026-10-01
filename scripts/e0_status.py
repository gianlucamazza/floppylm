"""Read frozen campaign provenance and optional live Xbox progress without mutating jobs."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: Path) -> dict:
    return json.loads(path.read_text())


def report(campaign: Path, *, workspace: Path = ROOT, portal=None) -> dict:
    state = read(campaign / "campaign.json")
    frozen = state["sources"]["files"]
    files = sorted((workspace / "src/floppylm").glob("*.py")) + sorted(
        (workspace / "experiments").glob("*.py")
    )
    actual = {
        str(p.relative_to(workspace)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files
    }
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
        "issues": ["Frozen source files changed"] if drift else [],
        "trial_counts": {},
    }
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
        device = json.loads(portal.get("device.json", ""))
        result["device"] = device
        if any(device.get(k) != state[k] for k in ("package", "commit")):
            result["issues"].append("Device differs from accepted campaign package/source")
    if not pending:
        return result
    record = pending[-1]
    run_id = record["run_id"]
    if "repair_id" in record and (workspace / "runs" / record["repair_id"]).exists():
        run_id = record["repair_id"]
    run = workspace / "runs" / run_id
    trial = {"run_id": run_id, "reservation_state": record["status"]}
    result["trial"] = trial
    if (run / "status.json").exists():
        trial["host"] = read(run / "status.json")
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
        else:
            trial["console"] = native
            if native.get("job_sha256") != binding["sha256"]:
                result["issues"].append("Console job hash differs from submitted job")
            if not native.get("hardware_gpu"):
                result["issues"].append("Console report lacks hardware GPU provenance")
            if native["state"] in ("failed", "interrupted"):
                result["issues"].append("Console trial requires diagnosis or explicit recovery")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, required=True)
    parser.add_argument("--xbox", action="store_true", help="query live device and bound job")
    args = parser.parse_args()
    portal = None
    if args.xbox:
        sys.path.insert(0, str(ROOT / "src"))
        from floppylm.xbox_portal import Portal

        portal = Portal.configured(read(args.campaign / "campaign.json")["package"])
    result = report(args.campaign, portal=portal)
    print(json.dumps(result, indent=2))
    return int(bool(result["issues"]))


if __name__ == "__main__":
    raise SystemExit(main())
