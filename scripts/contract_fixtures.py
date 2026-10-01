"""Regenerate golden instances of the floppylm.*.v1 contracts in tests/fixtures/contracts/.

Valid instances come from the real producers (prepare_job on a tiny synthetic job) and
from measured native evidence; invalid ones each break exactly one rule. Consumers such
as xbox-gpu-training test against these files at a pinned floppylm commit.
"""

from __future__ import annotations

import copy
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from floppylm.model import GPTConfig, TinyGPT  # noqa: E402
from floppylm.seed import seed_all  # noqa: E402
from floppylm.train import TrainSpec  # noqa: E402
from floppylm.xbox import prepare_job  # noqa: E402

OUT = ROOT / "tests/fixtures/contracts"
EVIDENCE = ROOT / "docs/evidence"
TINY = GPTConfig(vocab=16, d=8, n_layers=1, n_heads=2, d_ff=8, ctx=8)


def read(path: Path) -> dict:
    return json.loads(path.read_text())


def tiny_job() -> tuple[dict, dict]:
    seed_all(0)
    model = TinyGPT(TINY)
    with tempfile.TemporaryDirectory() as tmp:
        corpus = Path(tmp) / "corpus.bin"
        corpus.write_bytes(bytes(range(16)) * 64)
        job = prepare_job(Path(tmp) / "job", model, corpus, TrainSpec(tokens=64, batch=2), "tiny")
        initial = read(Path(tmp) / "job/initial.json")
    return job, initial


def instances() -> dict[str, dict]:
    job, initial = tiny_job()
    submitted = {
        **job,
        "purpose": "scientific",
        "acceptance_sha256": "0" * 64,
        "stop_after": 9,
        "resume": {"path": "results/tiny/checkpoint.json", "bytes": 1, "sha256": "1" * 64},
    }
    e01 = EVIDENCE / "xbox-e0-20261001-e01"
    recovery = read(e01 / "recovery.json")["reports"]
    interrupted = read(e01 / "lifecycle.json")["checkpoint_interruption"]
    failed = read(EVIDENCE / "xbox-e0-20261001/baseline-publish-failure.json")
    running = read(EVIDENCE / "xbox-e0-20261001/campaign-launch.json")["status"]
    device = read(e01 / "acceptance.json")["device"]

    valid = {
        "floppylm.e0.job.v1/prepared": job,
        "floppylm.e0.job.v1/submitted": submitted,
        "floppylm.e0.initialization.v1/tiny": initial,
        "floppylm.e0.weights.v1/tiny": {"schema": "floppylm.e0.weights.v1", **initial},
        "floppylm.e0.result.v1/running": running,
        "floppylm.e0.result.v1/interrupted": interrupted,
        "floppylm.e0.result.v1/completed": recovery[0],
        "floppylm.e0.result.v1/resumed": recovery[1],
        "floppylm.e0.result.v1/failed": failed,
        "floppylm.e0.result.v1/early-failure": {
            "job_id": "tiny",
            "state": "failed",
            "error": "job_id must match job file name",
        },
        "floppylm.device.v1/ready": device,
        "floppylm.device.v1/failed": {
            "state": "failed",
            "error": "no hardware adapter",
            "hardware_gpu": False,
            "commit": device["commit"],
        },
    }

    def broken(name: str, edit) -> dict:
        instance = copy.deepcopy(valid[name])
        edit(instance)
        return instance

    invalid = {
        "floppylm.e0.job.v1/two-branches": broken(
            "floppylm.e0.job.v1/prepared", lambda j: j["spec"].update(branches=2)
        ),
        "floppylm.e0.job.v1/unknown-key": broken(
            "floppylm.e0.job.v1/prepared", lambda j: j.update(tokenizer="bpe")
        ),
        "floppylm.e0.job.v1/bad-sha": broken(
            "floppylm.e0.job.v1/prepared", lambda j: j["data"].update(sha256="xyz")
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
        "floppylm.e0.result.v1/unknown-key": broken(
            "floppylm.e0.result.v1/completed", lambda r: r.update(val_bpb=1.0)
        ),
        "floppylm.device.v1/ready-without-package": broken(
            "floppylm.device.v1/ready", lambda d: d.pop("package")
        ),
        "floppylm.device.v1/failed-with-gpu": broken(
            "floppylm.device.v1/failed", lambda d: d.update(hardware_gpu=True)
        ),
    }
    return {
        **{"valid/" + k: v for k, v in valid.items()},
        **{"invalid/" + k: v for k, v in invalid.items()},
    }


def main() -> int:
    shutil.rmtree(OUT, ignore_errors=True)
    for name, instance in instances().items():
        kind, schema, case = name.split("/")
        path = OUT / kind / f"{schema}--{case}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(instance, indent=1, sort_keys=True) + "\n")
    print(f"wrote {len(list(OUT.rglob('*.json')))} fixtures to {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
