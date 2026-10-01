"""Measure one representative E0 shape before committing to campaign runtime.

Functional only: the synthetic corpus and short token budget cannot certify quality.
"""

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from floppylm import runlog, shapes
from floppylm.model import GPTConfig, TinyGPT
from floppylm.seed import seed_all
from floppylm.train import TrainSpec, schedule
from floppylm_xbox.jobs import prepare_job
from floppylm_xbox.portal import Portal


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--acceptance", type=Path, required=True)
    parser.add_argument("--steps", type=int, default=4, help="first branch T steps")
    parser.add_argument(
        "--summarize", action="store_true", help="summarize an existing completed job"
    )
    a = parser.parse_args()
    if a.steps < 2:
        parser.error("at least two T steps are needed")
    portal = Portal.configured()
    device = json.loads(portal.get("device.json", ""))
    proof = json.loads(a.acceptance.read_text())
    if not proof["ok"] or proof["package"] != portal.package or proof["commit"] != device["commit"]:
        raise RuntimeError("hardware acceptance does not match device")
    torch.set_num_threads(2)
    seed_all(0)
    cfg = shapes.fill_d_ff(GPTConfig(d=96, n_heads=6, n_layers=3, ctx=256), 11000000 / 16)
    model = TinyGPT(cfg)
    spec = TrainSpec(tokens=a.steps * 32 * cfg.ctx, batch=32)
    job_root = a.out / "job"
    if a.summarize:
        report = json.loads((a.out / "result.json").read_text())
        job = json.loads((job_root / "job.json").read_text())
        if job["config"] != cfg.to_dict() or job["spec"] != asdict(spec):
            raise RuntimeError("existing benchmark recipe differs")
    else:
        a.out.mkdir(parents=True, exist_ok=False)
        corpus = a.out / "synthetic.bin"
        corpus.write_bytes(b"the cat sat on the mat. " * 1000)
        job_id = runlog.new_run_id("benchmark")
        prepare_job(job_root, model, corpus, spec, job_id)
        portal.submit(job_root, purpose="functional")
        report = portal.wait(job_id)
        runlog.write_json(a.out / "result.json", report)
    binding = json.loads((job_root / "submitted.json").read_text())
    if binding["package"] != portal.package or binding["sha256"] != report.get("job_sha256"):
        raise RuntimeError("benchmark hardware job provenance differs")
    if report["state"] != "completed" or not report["hardware_gpu"]:
        raise RuntimeError("benchmark job failed")
    executed = report["trunk_step"] + sum(b["cooldown_steps"] for b in report["branches"])
    tokens = executed * spec.batch * cfg.ctx
    scientific = schedule(TrainSpec(tokens=20 * model.stored_params(), batch=32), cfg.ctx)
    scientific_steps = scientific["trunk_steps"] + sum(scientific["cooldowns"])
    summary = {
        "purpose": "functional",
        "package": portal.package,
        "commit": device["commit"],
        "config": cfg.to_dict(),
        "batch": spec.batch,
        "tokens": tokens,
        "wall_seconds": report["wall_seconds"],
        "tokens_per_second": tokens / report["wall_seconds"],
        "dispatches": report["dispatches"],
        "gpu_seconds": report["gpu_seconds"],
        "transfer_bytes": report["transfer_bytes"],
        "peak_memory_bytes": report["peak_memory_bytes"],
        "estimated_scientific_run_seconds": scientific_steps / executed * report["wall_seconds"],
        "estimate_excludes": (
            "corpus upload and Python serialization/evaluation; short-run extrapolation"
        ),
    }
    runlog.write_json(a.out / "summary.json", summary)
    print(json.dumps(summary, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
