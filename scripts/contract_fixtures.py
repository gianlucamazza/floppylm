"""Regenerate golden instances of the floppylm.*.v1 contracts in tests/fixtures/contracts/.

Valid instances come from the real producers: floppylm's Python code for jobs and fixtures,
the native backend in --reference mode for reports, results, weights and checkpoints (a tiny
job run on the host CPU), and measured native evidence. Invalid ones each break exactly one
rule. Consumers such as xbox-gpu-training test against these files at a pinned floppylm commit.

    python scripts/contract_fixtures.py --binary <xbox-gpu-training build>/xgpu_e0_train
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from floppylm import codec, model, train  # noqa: E402
from floppylm.model import GPTConfig, TinyGPT  # noqa: E402
from floppylm.seed import seed_all  # noqa: E402
from floppylm.train import TrainSpec  # noqa: E402
from floppylm_xbox.jobs import fixture, optimizer_fixture, prepare_job, tensors  # noqa: E402
from floppylm_xbox.kernels import fixtures as kernel_fixtures  # noqa: E402

OUT = ROOT / "tests/fixtures/contracts"
CONSTANTS = ROOT / "schemas/values/floppylm.e0.constants.v1.json"
EVIDENCE = ROOT / "docs/evidence"
# Smallest config the native backend accepts (byte vocabulary, 4-bit embedding).
TINY = GPTConfig(d=8, n_layers=1, n_heads=2, d_ff=8, ctx=8)
TINY_SPEC = TrainSpec(tokens=64, batch=2)


def read(path: Path) -> dict:
    return json.loads(path.read_text())


def native_instances(binary: Path) -> dict[str, dict]:
    """Python-produced fixtures and their native --reference reports for TINY."""
    out = {}
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        def run(*args: str) -> None:
            subprocess.run([str(binary), *args, "--reference"], check=True, capture_output=True)

        corpus = root / "corpus.bin"
        corpus.write_bytes(bytes(range(256)) * 4)
        for job_id, stop in (("tiny", None), ("tiny-stopped", "2")):
            seed_all(0)
            job = prepare_job(root / job_id, TinyGPT(TINY), corpus, TINY_SPEC, job_id)
            run("--job", str(root / job_id / "job.json"), *(("--stop-after", stop) if stop else ()))
            out[job_id] = job
            out[job_id + "/status"] = read(root / job_id / "results" / job_id / "status.json")
            out[job_id + "/checkpoint"] = read(
                root / job_id / "results" / job_id / "checkpoint.json"
            )
        out["initial"] = read(root / "tiny/initial.json")
        branch = out["tiny/status"]["branches"][0]["artifact"]["path"]
        out["weights"] = read(root / "tiny" / branch)

        seed_all(19)
        out["fixture"], _ = fixture(TinyGPT(TINY))
        (root / "fixture.json").write_text(json.dumps(out["fixture"]))
        run("--fixture", str(root / "fixture.json"), "--out", str(root / "fixture-report.json"))
        out["fixture-report"] = read(root / "fixture-report.json")

        out["optimizer"], _ = optimizer_fixture(TINY)
        (root / "optimizer.json").write_text(json.dumps(out["optimizer"]))
        run("--optimizer-fixture", str(root / "optimizer.json"), "--out", str(root / "opt.json"))
        out["optimizer-report"] = read(root / "opt.json")

        kernels, _ = kernel_fixtures()
        smallest = {}
        for case in kernels["cases"]:  # one case per operation keeps the golden small
            op = case["command"]["op"]
            if op not in smallest or len(json.dumps(case)) < len(json.dumps(smallest[op])):
                smallest[op] = case
        out["kernels"] = {**kernels, "cases": [smallest[op] for op in sorted(smallest)]}
        (root / "kernels.json").write_text(json.dumps(out["kernels"]))
        run("--kernel-fixture", str(root / "kernels.json"), "--out", str(root / "k-out.json"))
        out["kernels-result"] = read(root / "k-out.json")
    return out


def tensor_layout() -> list[dict]:
    """Stored tensor order and shapes, read from TinyGPT with distinguishable sizes."""
    sizes = {"vocab": 200, "d": 12, "n_heads": 2, "d_ff": 20}
    symbol = {200: "vocab", 12: "d", 36: "3*d", 20: "d_ff", 40: "2*d_ff", 1: "1"}
    per_mlp = {
        mlp: tensors(TinyGPT(GPTConfig(**sizes, n_layers=1, ctx=8, mlp=mlp))) for mlp in model.MLPS
    }
    layout = []
    for entries in zip(*per_mlp.values(), strict=True):
        rows = {mlp: symbol[e["rows"]] for mlp, e in zip(per_mlp, entries, strict=True)}
        first = entries[0]
        name = first["name"].replace("blocks.0.", "blocks.{i}.")
        layout.append(
            {
                "name": name,
                "rows": rows[model.MLPS[0]] if len(set(rows.values())) == 1 else rows,
                "cols": symbol[first["cols"]],
                "norm": first["norm"],
                "per_block": name != first["name"],
            }
        )
    return layout


def constants() -> dict:
    """Semantic constants every implementation of the E0 model must share."""
    spec = TrainSpec(tokens=1)
    return {
        "schema": "floppylm.e0.constants.v1",
        "codec": {
            "formats": list(model.FORMATS),
            "scale_policies": list(codec.SCALE_POLICIES),
            "fp16_min": codec.FP16_MIN,
            "fp16_max": codec.FP16_MAX,
            "log_steps_per_octave": codec.LOG_STEPS_PER_OCTAVE,
            "mult_2bit": codec.MULT_2BIT,
            "mult_4bit": codec.MULT_4BIT,
        },
        "model": {
            "mlps": list(model.MLPS),
            "rope_theta": model.ROPE_THETA,
            "rmsnorm_eps": model.RMSNORM_EPS,
            "gelu_approximate": model.GELU_APPROXIMATE,
            "tensor_layout": tensor_layout(),
        },
        "optimizer": {
            "adamw_betas": list(train.ADAMW_BETAS),
            "adamw_eps": train.ADAMW_EPS,
            "grad_clip": train.GRAD_CLIP,
            # torch.nn.utils.clip_grad_norm_ scales by grad_clip / (norm + 1e-6); asserted in tests.
            "grad_clip_eps": 1e-6,
        },
        "schedule": {
            "branches": spec.branches,
            "warmup_frac": spec.warmup_frac,
            "cooldown_frac": spec.cooldown_frac,
        },
    }


def shrink(value, keep: int = 3):
    """Copy with every list of numbers cut to `keep` items; structure keeps its length."""
    if isinstance(value, dict):
        return {k: shrink(v, keep) for k, v in value.items()}
    if isinstance(value, list):
        numeric = value and all(
            isinstance(v, int | float) and not isinstance(v, bool) for v in value
        )
        return value[:keep] if numeric else [shrink(v, keep) for v in value]
    return copy.deepcopy(value)


def validator(schema: str):
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource

    schemas = [read(p) for p in sorted((ROOT / "schemas").glob("*.json"))]
    registry = Registry().with_resources((s["$id"], Resource.from_contents(s)) for s in schemas)
    return Draft202012Validator(read(ROOT / "schemas" / f"{schema}.json"), registry=registry)


def instances(binary: Path) -> dict[str, dict]:
    native = native_instances(binary)
    # The exact scientific job sent to the console for a byte repair, with chunk lists.
    submitted = read(EVIDENCE / "e0-v2/runs/e0-20261001T090514Z-4236fd-000-repair/submitted.json")[
        "job"
    ]
    e01 = EVIDENCE / "xbox-e0-20261001-e01"
    recovery = read(e01 / "recovery.json")["reports"]
    interrupted = read(e01 / "lifecycle.json")["checkpoint_interruption"]
    failed = read(EVIDENCE / "xbox-e0-20261001/baseline-publish-failure.json")
    running = read(EVIDENCE / "xbox-e0-20261001/campaign-launch.json")["status"]
    device = read(e01 / "acceptance.json")["device"]

    # Produced by the same WorkerRuntime / claim code used by the console app.
    runtime_binary = binary.parent / "xgpu_e0_runtime_lifecycle_test"
    native_source = next(
        parent for parent in binary.parents if (parent / "contracts/floppylm/PIN.json").is_file()
    )
    with tempfile.TemporaryDirectory() as temp:
        subprocess.run(
            [
                str(runtime_binary),
                str(native_source),
                temp,
            ],
            check=True,
            capture_output=True,
        )
        worker = read(Path(temp) / "worker.json")
        claim = read(Path(temp) / "claim.json")

    valid = {
        "floppylm.worker.v1/native": worker,
        "floppylm.claim.v1/native": claim,
        "floppylm.e0.job.v1/prepared": native["tiny"],
        "floppylm.e0.job.v1/submitted": submitted,
        "floppylm.e0.job.v1/stop-after": read(e01 / "resume-job-submitted.json")["job"],
        "floppylm.e0.initialization.v1/tiny": native["initial"],
        "floppylm.e0.weights.v1/tiny": native["weights"],
        "floppylm.e0.result.v1/native-completed": native["tiny/status"],
        "floppylm.e0.result.v1/native-interrupted": native["tiny-stopped/status"],
        # Optional chart trail: bounded trunk samples, added before any producer emits them.
        "floppylm.e0.result.v1/loss-series": {
            **native["tiny-stopped/status"],
            "loss_series": [
                {"step": 1, "loss": 6.9},
                {"step": 2, "loss": native["tiny-stopped/status"]["last_loss"]},
            ],
        },
        "floppylm.checkpoint.v1/completed": native["tiny/checkpoint"],
        "floppylm.checkpoint.v1/interrupted": native["tiny-stopped/checkpoint"],
        "floppylm.e0.fixture.v1/tiny": native["fixture"],
        "floppylm.e0.fixture.report.v1/tiny": native["fixture-report"],
        "floppylm.e0.optimizer.v1/tiny": native["optimizer"],
        "floppylm.e0.optimizer.report.v1/tiny": native["optimizer-report"],
        "floppylm.e0.kernels.v1/one-per-op": native["kernels"],
        "floppylm.e0.kernels.result.v1/one-per-op": native["kernels-result"],
        "floppylm.xbox.acceptance.v1/package-0.1.0.28": read(e01 / "acceptance.json"),
        "floppylm.e0.constants.v1/published": read(CONSTANTS),
        "floppylm.e0.result.v1/running": running,
        "floppylm.e0.result.v1/interrupted": interrupted,
        "floppylm.e0.result.v1/completed": recovery[0],
        "floppylm.e0.result.v1/resumed": recovery[1],
        "floppylm.e0.result.v1/failed": failed,
        # A status written during a cooldown cannot be captured from a finished run: the
        # running campaign status with the schedule and phase run_job publishes for that point.
        "floppylm.e0.result.v1/cooldown-phase": {
            **running,
            "schedule": {
                "T": 879,
                "warmup": 17,
                "tokens_per_step": 8192,
                "ends": [879, 1758, 3516],
                "cooldown_starts": [792, 1583, 3165],
            },
            "phase": "cooldown",
            "cooldown_end": 879,
            "cooldown_step": 800,
        },
        # Written by the console app when a job fails before run_job starts.
        "floppylm.e0.result.v1/early-failure": {
            "job_id": "tiny",
            "state": "failed",
            "error": "job_id must match job file name",
        },
        "floppylm.device.v1/ready": device,
        # Written by the console app when the GPU worker fails to start.
        "floppylm.device.v1/failed": {
            "state": "failed",
            "error": "no hardware adapter",
            "hardware_gpu": False,
            "commit": device["commit"],
        },
    }

    valid["floppylm.e0.job.v1/watchdog-probe"] = {
        **native["tiny"],
        "purpose": "functional",
        "runtime_fault_probe": {"kind": "published_fence_stall", "after_checkpoint_step": 1},
    }

    def broken(name: str, edit) -> dict:
        """A reduced copy of a valid golden that breaks exactly one rule."""
        base = shrink(valid[name])
        schema = name.split("/")[0]
        if not validator(schema).is_valid(base):
            raise RuntimeError(f"reduced base of {name} is not valid")
        edit(base)
        return base

    invalid = {
        "floppylm.worker.v1/no-identity": broken(
            "floppylm.worker.v1/native", lambda w: w.pop("worker_id")
        ),
        "floppylm.claim.v1/bad-sha": broken(
            "floppylm.claim.v1/native", lambda c: c.update(job_sha256="bad")
        ),
        "floppylm.e0.job.v1/two-branches": broken(
            "floppylm.e0.job.v1/prepared", lambda j: j["spec"].update(branches=2)
        ),
        "floppylm.e0.job.v1/unknown-key": broken(
            "floppylm.e0.job.v1/prepared", lambda j: j.update(tokenizer="bpe")
        ),
        "floppylm.e0.job.v1/bad-sha": broken(
            "floppylm.e0.job.v1/prepared", lambda j: j["data"].update(sha256="xyz")
        ),
        "floppylm.e0.job.v1/chunk-not-content-addressed": broken(
            "floppylm.e0.job.v1/submitted",
            lambda j: j["initialization"]["chunks"][0].update(path="part-0.bin"),
        ),
        "floppylm.e0.job.v1/bad-scale-policy": broken(
            "floppylm.e0.job.v1/prepared", lambda j: j["config"].update(scale_policy="row4")
        ),
        "floppylm.e0.weights.v1/wrong-schema": broken(
            "floppylm.e0.weights.v1/tiny", lambda w: w.update(schema="floppylm.e0.weights.v2")
        ),
        "floppylm.e0.weights.v1/empty-tensors": broken(
            "floppylm.e0.weights.v1/tiny", lambda w: w.update(tensors=[])
        ),
        "floppylm.e0.result.v1/completed-two-branches": broken(
            "floppylm.e0.result.v1/completed", lambda r: r["branches"].pop()
        ),
        "floppylm.e0.result.v1/failed-without-error": broken(
            "floppylm.e0.result.v1/interrupted", lambda r: r.update(state="failed")
        ),
        "floppylm.e0.result.v1/cooldown-without-step": broken(
            "floppylm.e0.result.v1/cooldown-phase", lambda r: r.pop("cooldown_step")
        ),
        "floppylm.e0.result.v1/trunk-with-cooldown-end": broken(
            "floppylm.e0.result.v1/cooldown-phase", lambda r: r.update(phase="trunk")
        ),
        "floppylm.e0.result.v1/short-schedule": broken(
            "floppylm.e0.result.v1/cooldown-phase", lambda r: r["schedule"]["ends"].pop()
        ),
        "floppylm.e0.result.v1/unknown-key": broken(
            "floppylm.e0.result.v1/completed", lambda r: r.update(val_bpb=1.0)
        ),
        "floppylm.e0.result.v1/loss-series-missing-step": broken(
            "floppylm.e0.result.v1/loss-series",
            lambda r: r["loss_series"][0].pop("step"),
        ),
        "floppylm.e0.result.v1/loss-series-empty": broken(
            "floppylm.e0.result.v1/loss-series",
            lambda r: r.update(loss_series=[]),
        ),
        "floppylm.checkpoint.v1/stream-not-integer": broken(
            "floppylm.checkpoint.v1/interrupted", lambda c: c.update(stream_position=1.5)
        ),
        "floppylm.checkpoint.v1/negative-second-moment": broken(
            "floppylm.checkpoint.v1/interrupted",
            lambda c: c["moments"][0]["second"].__setitem__(0, -1.0),
        ),
        "floppylm.e0.fixture.v1/no-targets": broken(
            "floppylm.e0.fixture.v1/tiny", lambda f: f.pop("targets")
        ),
        "floppylm.e0.fixture.report.v1/no-quantization": broken(
            "floppylm.e0.fixture.report.v1/tiny", lambda r: r.pop("quantization")
        ),
        "floppylm.e0.optimizer.v1/step-zero": broken(
            "floppylm.e0.optimizer.v1/tiny", lambda o: o["steps"][0].update(step=0)
        ),
        "floppylm.e0.optimizer.report.v1/no-moments": broken(
            "floppylm.e0.optimizer.report.v1/tiny", lambda r: r["steps"][0].pop("moments")
        ),
        "floppylm.e0.kernels.v1/unknown-op": broken(
            "floppylm.e0.kernels.v1/one-per-op", lambda k: k["cases"][0]["command"].update(op=14)
        ),
        "floppylm.e0.kernels.v1/four-buffers": broken(
            "floppylm.e0.kernels.v1/one-per-op", lambda k: k["cases"][0]["inputs"].pop()
        ),
        "floppylm.e0.kernels.result.v1/no-dispatches": broken(
            "floppylm.e0.kernels.result.v1/one-per-op", lambda k: k["cases"][0].pop("dispatches")
        ),
        "floppylm.xbox.acceptance.v1/passed-without-resume": broken(
            "floppylm.xbox.acceptance.v1/package-0.1.0.28", lambda a: a.pop("resume")
        ),
        "floppylm.e0.constants.v1/no-tensor-layout": broken(
            "floppylm.e0.constants.v1/published", lambda c: c["model"].pop("tensor_layout")
        ),
        "floppylm.device.v1/capabilities-without-delta": broken(
            "floppylm.device.v1/ready",
            lambda d: d.update(capabilities={k: ["4bit"] for k in ("emb_fmt", "core_fmt")}),
        ),
        "floppylm.device.v1/ready-without-package": broken(
            "floppylm.device.v1/ready", lambda d: d.pop("package")
        ),
        "floppylm.device.v1/failed-with-gpu": broken(
            "floppylm.device.v1/failed", lambda d: d.update(hardware_gpu=True)
        ),
    }
    for case, edit in {
        "scientific": lambda j: j.update(purpose="scientific"),
        "missing-purpose": lambda j: j.pop("purpose"),
        "resume": lambda j: j.update(resume=j["initialization"]),
        "stop-after": lambda j: j.update(stop_after=1),
        "zero": lambda j: j["runtime_fault_probe"].update(after_checkpoint_step=0),
        "unknown-kind": lambda j: j["runtime_fault_probe"].update(kind="other"),
    }.items():
        invalid["floppylm.e0.job.v1/watchdog-" + case] = broken(
            "floppylm.e0.job.v1/watchdog-probe", edit
        )
    return {
        **{"valid/" + k: v for k, v in valid.items()},
        **{"invalid/" + k: v for k, v in invalid.items()},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--binary",
        type=Path,
        default=Path(
            os.environ.get(
                "XGPU_E0_BINARY", ROOT.parents[1] / "tooling/xbox-gpu-training/build/xgpu_e0_train"
            )
        ),
        help="native xgpu_e0_train (reference mode runs on the host CPU)",
    )
    args = parser.parse_args()
    if not args.binary.is_file():
        parser.error(f"native binary not found: {args.binary}")
    CONSTANTS.parent.mkdir(parents=True, exist_ok=True)
    CONSTANTS.write_text(json.dumps(constants(), indent=1) + "\n")
    shutil.rmtree(OUT, ignore_errors=True)
    for name, instance in instances(args.binary.resolve()).items():
        kind, schema, case = name.split("/")
        path = OUT / kind / f"{schema}--{case}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        # Generated files: compact, one line, stable key order.
        path.write_text(json.dumps(instance, sort_keys=True, separators=(",", ":")) + "\n")
    print(f"wrote {len(list(OUT.rglob('*.json')))} fixtures to {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
