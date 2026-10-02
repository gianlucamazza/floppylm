"""Functional negative probes for job identity and DX12 worker reuse after rejection."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from floppylm import runlog
from floppylm_xbox.portal import Portal


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--expect-broken", action="store_true")
    a = parser.parse_args()
    a.out.mkdir(parents=True, exist_ok=False)
    p = Portal.configured()
    device = json.loads(p.get("device.json", ""))
    prefix = runlog.new_run_id("worker")
    base = {"schema": "floppylm.e0.kernels.v1", "cases": []}
    probes = {}
    for label, fixture in (
        ("identity", {**base, "job_id": prefix + "-wrong"}),
        (
            "oversized",
            {
                **base,
                "cases": [
                    {
                        "id": "oversized",
                        "command": {"op": 0, "count": 4194241},
                        "inputs": [[0.0], [0.0], [], [], []],
                    }
                ],
            },
        ),
        (
            "reuse",
            {
                **base,
                "cases": [
                    {
                        "id": "reuse",
                        "command": {"op": 0, "count": 1},
                        "inputs": [[1.0], [2.0], [], [], []],
                    }
                ],
            },
        ),
    ):
        runlog.write_json(a.out / (label + "-fixture.json"), fixture)
        try:
            result = p.fixture(fixture, prefix + "-" + label)
            runlog.write_json(a.out / (label + "-actual.json"), result)
            probes[label] = {"accepted": True, "result": result}
        except RuntimeError as error:
            probes[label] = {"accepted": False, "error": str(error)}
        runlog.write_json(a.out / "probes.json", probes)
    identity_error = probes["identity"].get("error", "")
    fixed = (
        not probes["identity"]["accepted"]
        and (
            "job_id must match" in identity_error
            or "claim_job_id_mismatch" in identity_error
        )
        and not probes["oversized"]["accepted"]
        and (
            "dispatch dimension" in probes["oversized"]["error"]
            or "invalid E0 command dimensions/buffers"
            in probes["oversized"]["error"]
        )
        and probes["reuse"]["accepted"]
        and probes["reuse"]["result"]["hardware_gpu"]
        and probes["reuse"]["result"]["cases"][0]["values"] == [3.0]
        and probes["reuse"]["result"]["dispatches"] > 0
    )
    broken = probes["identity"]["accepted"] and not probes["reuse"]["accepted"]
    report = {
        "purpose": "functional",
        "package": p.package,
        "commit": device["commit"],
        "fixed": fixed,
        "baseline_broken": broken,
        "probes": probes,
    }
    runlog.write_json(a.out / "worker.json", report)
    print(json.dumps({"fixed": fixed, "baseline_broken": broken}), flush=True)
    return 0 if (broken if a.expect_broken else fixed) else 1


if __name__ == "__main__":
    raise SystemExit(main())
