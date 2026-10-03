"""Read-only E0 readiness: stdout evidence, no campaign, test split or Xbox writes."""

from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
from dataclasses import replace
from http.client import HTTPException
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "experiments")]
from e0_v2 import FULL_BUDGET_BITS, TOKENS_PER_PARAM  # noqa: E402
from floppylm import runlog, shapes  # noqa: E402
from floppylm.campaign_protocol import PROTOCOL_ADR, grid_configs, protocol_spec  # noqa: E402
from floppylm.model import GPTConfig  # noqa: E402
from floppylm.train import TrainSpec, schedule  # noqa: E402
from floppylm_xbox.portal import Portal, check_acceptance  # noqa: E402


def read(path):
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError("expected JSON object: " + str(path))
    return value


def legacy_lock_liveness(path):
    """Pre-PID campaigns still held a lifetime flock. Observe without acquiring it."""
    stat = path.stat()  # Missing lock is unknown, never evidence of an idle host.
    identity = (os.major(stat.st_dev), os.minor(stat.st_dev), stat.st_ino)
    for line in Path("/proc/locks").read_text().splitlines():
        for field in line.split():
            parts = field.split(":")
            if len(parts) != 3:
                continue
            try:
                actual = (int(parts[0], 16), int(parts[1], 16), int(parts[2]))
            except ValueError:
                continue
            if actual == identity:
                return "owned_or_waiting"
    return "unowned_legacy_lock"


def cost_projection(protocol, speed):
    """Enumerate possible selected scale/MLP paths, not hypothetical winners."""
    budget = FULL_BUDGET_BITS * protocol["budget_frac"]
    base = GPTConfig(
        d=protocol["neutral_width"],
        n_layers=protocol["neutral_layers"],
        n_heads=protocol["neutral_width"] // shapes.HEAD_DIM,
        ctx=protocol["ctx"],
    )

    def tokens(cfg):
        params = sum(math.prod(shape) for _, shape in cfg.tensor_shapes())
        s = schedule(TrainSpec(tokens=TOKENS_PER_PARAM * params, batch=protocol["batch"]), cfg.ctx)
        return (s["trunk_steps"] + sum(s["cooldowns"])) * s["per_step"]

    neutral_scale = [
        shapes.fill_d_ff(replace(base, scale_policy=p), budget) for p in protocol["scale_order"]
    ]
    paths = []
    for scale in neutral_scale:
        mlps = [shapes.fill_d_ff(replace(scale, mlp=m), budget) for m in protocol["mlp_order"]]
        neutral_tokens = len(protocol["neutral_seeds"]) * sum(map(tokens, neutral_scale + mlps))
        for chosen in mlps:
            count = len(protocol["neutral_seeds"]) * (len(neutral_scale) + len(mlps))
            total_min = total_max = neutral_tokens
            for fmt in ("ternary", "2bit"):
                cfg = shapes.fill_d_ff(replace(chosen, core_fmt=fmt), budget)
                grid = grid_configs(cfg, budget, protocol)
                if not grid:
                    raise ValueError("empty accepted shape grid")
                axes = protocol["ternary_delta"] if fmt == "ternary" else protocol["2bit_wd"]
                tuning = len(protocol["lr"]) * len(axes)
                paired = len(protocol["paired_seeds"])
                count += tuning + len(grid) + paired
                common = tuning * tokens(cfg) + sum(map(tokens, grid))
                total_min += common + paired * min(map(tokens, grid))
                total_max += common + paired * max(map(tokens, grid))
            paths.append(
                {
                    "scale_policy": chosen.scale_policy,
                    "mlp": chosen.mlp,
                    "original_trials": count,
                    "training_seconds_without_repairs": [total_min / speed, total_max / speed],
                }
            )
    return {
        "paths": paths,
        "max_repair_attempts_per_trial": 1,
        "repair_allowance": (
            "Reserve roughly another full training pass if every trial needs S3; "
            "repaired shapes can change token counts."
        ),
        "host_evaluation_seconds": None,
        "limits": (
            "Synthetic single-shape rate extrapolated across shapes; excludes upload, host "
            "evaluation, packing, downtime and final test. Not a deadline or a measured duration."
        ),
    }


def report(workspace, acceptance, benchmark, data_manifest, *, data_dir=None, portal=None):
    result = {
        "observed_at": runlog.now(),
        "purpose": "preparation",
        "ready": False,
        "local_ok": False,
        "xbox_checked": portal is not None,
        "checks": {},
        "protocol_adr": PROTOCOL_ADR,
        "protocol": protocol_spec(),
    }

    def check(name, operation):
        try:
            result["checks"][name] = {"ok": True, "evidence": operation()}
        except (
            OSError,
            HTTPException,
            RuntimeError,
            ValueError,
            KeyError,
            TypeError,
            subprocess.SubprocessError,
        ) as error:
            result["checks"][name] = {"ok": False, "error": str(error)}

    def sources():
        value = runlog.sources(workspace)
        untracked = subprocess.check_output(
            [
                "git",
                "ls-files",
                "--others",
                "--exclude-standard",
                "--",
                *runlog.SOURCE_DIRS,
                "scripts/e0_preflight.py",
            ],
            cwd=workspace,
            text=True,
        ).splitlines()
        if not value["git"]["commit"] or value["git"]["dirty"] or untracked:
            raise RuntimeError("commit all source changes before readiness")
        value["preflight_sha256"] = runlog.sha256_file(workspace / "scripts/e0_preflight.py")
        return value

    check("sources", sources)
    proof = speed = None

    def provenance():
        nonlocal proof, speed
        proof, speed = read(acceptance), read(benchmark)
        if not isinstance(proof.get("kernels"), dict):
            raise ValueError("acceptance requires a kernel proof object")
        check_acceptance(proof, {"commit": speed["commit"]}, speed["package"])
        rate = speed["tokens_per_second"]
        if (
            speed.get("purpose") != "functional"
            or type(rate) not in (int, float)
            or not math.isfinite(rate)
            or rate <= 0
        ):
            raise ValueError("benchmark must contain a positive finite functional throughput")
        return {
            "package": proof["package"],
            "commit": proof["commit"],
            "acceptance_sha256": runlog.sha256_file(acceptance),
            "benchmark_sha256": runlog.sha256_file(benchmark),
        }

    check("provenance", provenance)

    def corpus():
        # Do not call data.manifest(): it also opens and hashes test.bin.
        reference = read(data_manifest)["data"]["verified"]["prepared"]
        directory = data_dir or workspace / "data/tinystories"
        observed = {}
        for split, minimum in (("train", result["protocol"]["ctx"] + 2), ("val", 1 << 20)):
            path = directory / (split + ".bin")
            actual = {"bytes": path.stat().st_size, "sha256": runlog.sha256_file(path)}
            if actual != reference[split] or actual["bytes"] < minimum:
                raise ValueError(split + " differs from the corpus reference or is too short")
            observed[split] = actual
        return {
            "reference_sha256": runlog.sha256_file(data_manifest),
            "verified": observed,
            "test": "not opened; excluded from preparation",
        }

    check("corpus", corpus)

    def reservations():
        selections = workspace / "docs/evidence/e0-v2/selections"
        paths = sorted(selections.glob("*.reservation.json"))
        paths += sorted((workspace / "runs").glob("*/repair.reservation.json"))
        records = []
        for path in paths:
            value = read(path)
            if not isinstance(value, dict):
                raise ValueError("invalid reservation metadata: " + str(path))
            records.append(
                {
                    "path": str(path.relative_to(workspace)),
                    "sha256": runlog.sha256_file(path),
                    "state": value.get("state"),
                }
            )
            if path.parent == selections and value.get("state") != "completed":
                raise RuntimeError("unresolved final-test reservation: " + path.name)
        return records

    check("reservations", reservations)

    def hosts():
        records = []
        for path in sorted((workspace / "runs").glob("*/campaign.json")):
            value = read(path)
            state = value["status"]
            live = runlog.host_liveness(
                {**value, "state": "running" if state == "stopping" else state},
                path.parent / "worker.lock",
            )
            if state in ("running", "stopping") and value.get("pid") is None:
                live = legacy_lock_liveness(path.parent / "worker.lock")
            records.append(
                {"path": str(path.relative_to(workspace)), "state": state, "liveness": live}
            )
            if state in ("running", "stopping") and live not in (
                "dead",
                "identity_mismatch",
                "unowned_legacy_lock",
            ):
                raise RuntimeError("active or unverified campaign host: " + str(path.parent))
        return records

    check("campaign_hosts", hosts)
    if result["checks"]["provenance"]["ok"]:
        check(
            "cost_projection",
            lambda: cost_projection(result["protocol"], speed["tokens_per_second"]),
        )
    result["local_ok"] = all(c["ok"] for c in result["checks"].values())

    def console():
        if not result["checks"]["provenance"]["ok"]:
            raise RuntimeError("console check requires valid local provenance")
        device = json.loads(portal.get("device.json", ""))
        if not isinstance(device, dict):
            raise ValueError("device.json must contain a JSON object")
        check_acceptance(proof, device, portal.package)
        if (
            device.get("package") != portal.package
            or not device.get("hardware_gpu")
            or device.get("state") != "ready"
        ):
            raise RuntimeError("device is not the accepted ready hardware package")
        processes = portal.request("GET", "/api/resourcemanager/processes", json_result=True)
        if not isinstance(processes, dict):
            raise ValueError("process response must be a JSON object")
        process_list = processes.get("Processes")
        if not isinstance(process_list, list) or any(not isinstance(p, dict) for p in process_list):
            raise ValueError("process response must contain a list of objects")
        worker = portal.live_worker(commit=proof["commit"])
        if worker["state"] != "ready" or worker["active_job"] is not None:
            raise RuntimeError("console worker is busy")
        if not any(
            p.get("PackageFullName") == portal.package and p.get("ProcessId") == worker["pid"]
            for p in process_list
        ):
            raise RuntimeError("live worker PID is absent from the exact package process list")
        pending = [n for n in portal.files() if n.endswith(".ready")]
        if pending:
            raise RuntimeError("pending inbox jobs: " + ", ".join(pending))
        return {
            "package": portal.package,
            "commit": device["commit"],
            "worker": worker,
            "tls_certificate_sha256": portal.cert_sha256,
            "pending_jobs": pending,
        }

    if portal is not None:
        check("xbox", console)
        result["ready"] = result["local_ok"] and result["checks"]["xbox"]["ok"]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--acceptance", type=Path, required=True)
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument(
        "--data-manifest",
        type=Path,
        required=True,
        help="existing run manifest with recorded prepared corpus hashes",
    )
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data/tinystories")
    parser.add_argument("--xbox", action="store_true")
    args = parser.parse_args()
    try:
        portal = Portal.configured() if args.xbox else None
        value = report(
            ROOT,
            args.acceptance,
            args.benchmark,
            args.data_manifest,
            data_dir=args.data_dir,
            portal=portal,
        )
    except (OSError, HTTPException, RuntimeError, ValueError) as error:
        value = {
            "observed_at": runlog.now(),
            "ready": False,
            "local_ok": False,
            "xbox_checked": args.xbox,
            "error": str(error),
        }
    print(json.dumps(value, indent=2, allow_nan=False))
    return 0 if value["ready" if args.xbox else "local_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
