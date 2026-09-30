"""Hardware acceptance: held-out oracle, identical-input optimizer and exact resume.

No scientific jobs are submitted by this command. Evidence binds the running package,
source commit, fixture inputs and actual console outputs.
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from floppylm import runlog
from floppylm.model import GPTConfig, TinyGPT
from floppylm.seed import seed_all
from floppylm.train import TrainSpec
from floppylm.xbox import check_fixture, fixture, prepare_job, verify_optimizer
from floppylm.xbox_portal import Portal


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    a = parser.parse_args()
    a.out.mkdir(parents=True, exist_ok=False)
    torch.set_num_threads(2)
    portal = Portal.configured()
    device = json.loads(portal.get("device.json", ""))
    runlog.write_json(a.out / "device.json", device)
    if device.get("state") != "ready" or not device.get("hardware_gpu"):
        raise RuntimeError("Xbox hardware app is not ready")
    proof = {
        "schema": "floppylm.xbox.acceptance.v1",
        "purpose": "functional",
        "package": portal.package,
        "commit": device["commit"],
        "device": device,
        "created": runlog.now(),
        "ok": False,
        "fixtures": [],
    }
    runlog.write_json(a.out / "acceptance.json", proof)
    prefix = runlog.new_run_id("gate")
    for index, (fmt, scale, mlp, qk) in enumerate(
        itertools.product(
            ("ternary", "2bit"),
            ("row16", "row8log", "tensor16"),
            ("gelu", "relu2", "swiglu"),
            (False, True),
        )
    ):
        cfg = GPTConfig(
            d=32,
            n_layers=1,
            n_heads=2,
            d_ff=48,
            ctx=8,
            core_fmt=fmt,
            scale_policy=scale,
            mlp=mlp,
            qk_norm=qk,
        )
        seed_all(19)
        initial, expected = fixture(TinyGPT(cfg))
        initial["schema"] = "floppylm.e0.fixture.v1"
        directory = a.out / f"fixture-{index:02d}"
        directory.mkdir()
        runlog.write_json(directory / "fixture.json", initial)
        runlog.write_json(directory / "expected.json", expected)
        actual = portal.fixture(initial, f"{prefix}-{index}")
        runlog.write_json(directory / "actual.json", actual)
        result = check_fixture(actual, expected, cfg, directory)
        proof["fixtures"].append(
            {
                "path": directory.name,
                "ok": result["ok"],
                "actual_sha256": runlog.sha256_file(directory / "actual.json"),
            }
        )
        runlog.write_json(a.out / "acceptance.json", proof)
        print(json.dumps({"fixture": index, "ok": result["ok"]}), flush=True)
        if not result["ok"]:
            raise RuntimeError("GPU numerical gate failed; evidence retained")
    proof["optimizer"] = verify_optimizer(
        None,
        a.out / "optimizer",
        cfg,
        executor=lambda data: portal.fixture(data, prefix + "-optimizer"),
    )
    if not proof["optimizer"]["ok"]:
        runlog.write_json(a.out / "acceptance.json", proof)
        raise RuntimeError("identical-input optimizer gate failed")
    runlog.write_json(a.out / "acceptance.json", proof)
    seed_all(19)
    cfg = GPTConfig(d=32, n_layers=1, n_heads=2, d_ff=48, ctx=8)
    model = TinyGPT(cfg)
    corpus = a.out / "corpus.bin"
    corpus.write_bytes(b"the cat sat on the mat. " * 100)
    spec = TrainSpec(tokens=128, batch=2, seed=19)
    reports = []
    for label in ("full", "resumed"):
        directory = a.out / label
        job = prepare_job(directory, model, corpus, spec, prefix + "-" + label)
        if label == "resumed":
            job["stop_after"] = 9
            runlog.write_json(directory / "job.json", job)
        portal.submit(directory, purpose="functional")
        result = portal.wait(job["job_id"])
        if label == "resumed":
            if result["state"] != "interrupted":
                raise RuntimeError("controlled interruption failed")
            portal.retrieve(result["checkpoint"], directory / "interrupted-checkpoint.json")
            resume_sha = portal.resume(directory, result["checkpoint"])
            result = portal.wait(job["job_id"], expected_sha=resume_sha)
        runlog.write_json(directory / "result.json", result)
        if (
            result["state"] != "completed"
            or not result["hardware_gpu"]
            or result["dispatches"] <= 0
        ):
            raise RuntimeError("hardware resume trial failed")
        portal.retrieve(result["checkpoint"], directory / "checkpoint.json")
        for branch in result["branches"]:
            portal.retrieve(branch["artifact"], directory / f"branch-{branch['end_step']}.json")
        reports.append(result)
    checkpoints = [
        json.loads((a.out / label / "checkpoint.json").read_text()) for label in ("full", "resumed")
    ]
    exact = all(
        checkpoints[0][key] == checkpoints[1][key]
        for key in ("step", "stream_position", "tensors", "moments")
    )
    for end in (8, 16, 32):
        exact &= (a.out / "full" / f"branch-{end}.json").read_bytes() == (
            a.out / "resumed" / f"branch-{end}.json"
        ).read_bytes()
    proof["resume"] = {"ok": exact, "reports": reports}
    proof["ok"] = exact and all(
        r.get("peak_memory_bytes", 0) > 0 and r["peak_memory_bytes"] <= 1 << 30 for r in reports
    )
    runlog.write_json(a.out / "acceptance.json", proof)
    return 0 if proof["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
