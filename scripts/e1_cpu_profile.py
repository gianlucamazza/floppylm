"""Profile the existing scalar oracle with a hash-verified Xbox benchmark recipe.

Functional host evidence only. Console resident timing and Python artifact timing
have different boundaries; this is not the scientific E1 backend selection.
"""

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main():
    from floppylm import runlog
    from floppylm.model import GPTConfig, TinyGPT
    from floppylm.pack import pack
    from floppylm.train import DataStream, TrainSpec, schedule, train_wsd
    from floppylm.xbox import restore_tensors

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--threads", type=int, default=2)
    args = parser.parse_args()
    if args.repeats < 1 or args.threads < 1:
        parser.error("positive repeat/thread counts required")
    sources = runlog.sources(ROOT)
    diagnostic_hash = runlog.sha256_file(Path(__file__))
    torch.set_num_threads(args.threads)
    job = json.loads((args.job / "job.json").read_text())
    cfg, spec = GPTConfig(**job["config"]), TrainSpec(**job["spec"])
    for key in ("initialization", "data", "indices"):
        descriptor = job[key]
        path = args.job / descriptor["path"]
        if (
            path.stat().st_size != descriptor["bytes"]
            or runlog.sha256_file(path) != descriptor["sha256"]
        ):
            raise RuntimeError("benchmark asset differs: " + key)
    data = np.memmap(args.job / job["data"]["path"], mode="r", dtype=np.uint8)
    indices = np.fromfile(args.job / job["indices"]["path"], dtype="<u8")
    sch = schedule(spec, cfg.ctx)
    stream = DataStream(data, spec.batch, cfg.ctx, spec.seed)
    expected = np.concatenate(
        [
            stream.rng.integers(0, len(data) - cfg.ctx - 1, size=spec.batch)
            for _ in range(sch["ends"][-1])
        ]
    )
    if not np.array_equal(expected, indices):
        raise RuntimeError("ordered sample indices differ from Python oracle")
    initial = json.loads((args.job / job["initialization"]["path"]).read_text())
    if initial["config"] != cfg.to_dict():
        raise RuntimeError("initialization configuration differs")
    args.out.mkdir(parents=True, exist_ok=False)
    attempts = []
    for repeat in range(args.repeats):
        start = time.perf_counter()
        model = TinyGPT(cfg)
        restore_tensors(model, initial["tensors"])
        initialized = time.perf_counter()
        branches = []
        serialization_seconds = 0.0

        def branch(end, trained, metadata):
            nonlocal serialization_seconds
            began = time.perf_counter()
            artifact = pack(trained)
            target = args.out / f"repeat-{repeat}-branch-{end}.flp"
            runlog.write_atomic(target, artifact)
            branches.append(
                {"end_step": end, "bytes": len(artifact), "sha256": runlog.sha256_file(target)}
            )
            serialization_seconds += time.perf_counter() - began

        accounting = train_wsd(model, data, spec, branch, log=lambda _: None)
        elapsed = time.perf_counter() - start
        steps = accounting["trunk_steps"] + sum(
            c["cooldown_steps"] for c in accounting["cooldowns"]
        )
        tokens = steps * spec.batch * cfg.ctx
        attempts.append(
            {
                "repeat": repeat,
                "wall_seconds": elapsed,
                "initialization_seconds": initialized - start,
                "serialization_seconds": serialization_seconds,
                "training_and_forks_seconds": elapsed
                - (initialized - start)
                - serialization_seconds,
                "tokens": tokens,
                "tokens_per_second": tokens / elapsed,
                "accounting": accounting,
                "branches": branches,
            }
        )
        runlog.write_json(args.out / "attempts.json", {"attempts": attempts})
    if any(a["branches"] != attempts[0]["branches"] for a in attempts[1:]):
        raise RuntimeError("CPU repeats do not reproduce exact artifacts")
    if sources["files"] != runlog.sources(ROOT)["files"] or diagnostic_hash != runlog.sha256_file(
        Path(__file__)
    ):
        raise RuntimeError("profile implementation changed during execution")
    summary = {
        "purpose": "functional",
        "backend": "cpu",
        "config": cfg.to_dict(),
        "job_sha256": runlog.sha256_file(args.job / "job.json"),
        "inputs": {key: job[key] for key in ("initialization", "data", "indices")},
        "sources": sources,
        "diagnostic_sha256": diagnostic_hash,
        "environment": runlog.environment(args.threads),
        "attempts": attempts,
        "repeat_artifacts_exact": True,
        "limits": (
            "Scalar CPU profile only; different timing boundaries from resident Xbox. "
            "No E1 selection or quality claim."
        ),
    }
    runlog.write_json(args.out / "summary.json", summary)
    runlog.write_atomic(
        args.out / "notes.md",
        "# Scalar CPU qualification profile\n\n"
        "Functional, hash-bound inputs; exact repeat artifacts.\n"
        "Includes initialization, WSD forks and canonical FLP2 serialization.\n"
        "No validation/test split opened and no console job submitted.\n",
    )
    print(
        json.dumps(
            {
                "tokens_per_second": [a["tokens_per_second"] for a in attempts],
                "repeat_artifacts_exact": True,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
