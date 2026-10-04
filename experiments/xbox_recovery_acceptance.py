"""Functional console proof for reconnect, interrupted recovery and completed retrieval."""

from __future__ import annotations

import argparse
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
from floppylm_xbox.jobs import prepare_job, tensors
from floppylm_xbox.portal import Portal


def require_runner_interruption(code: int, summary_status: str) -> None:
    """A native interrupt is recorded and returned. It is not an uncaught failure.

    ``cmd_run`` writes summary status ``interrupted`` and returns 130. Older hosts
    propagated ``RuntimeError`` instead. Both proofs are accepted only when the
    recorded status is interrupted.
    """
    if code != 130 or summary_status != "interrupted":
        raise RuntimeError("runner interruption did not occur")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--acceptance", type=Path, required=True)
    a = parser.parse_args()
    a.out.mkdir(parents=True, exist_ok=False)
    torch.set_num_threads(2)
    portal = Portal.configured()
    device = json.loads(portal.get("device.json", ""))
    accepted = json.loads(a.acceptance.read_text())
    if not accepted["ok"] or any(accepted[k] != device[k] for k in ("commit", "package")):
        raise RuntimeError("recovery proof requires the validated package")
    cfg = GPTConfig(d=32, n_layers=1, n_heads=2, d_ff=48, ctx=8)
    spec = TrainSpec(tokens=128, batch=2, seed=19)
    corpus = a.out / "corpus.bin"
    corpus.write_bytes(b"the cat sat on the mat. " * 100)
    records = []
    prefix = runlog.new_run_id("recovery")
    for label in ("full", "interrupted"):
        seed_all(19)
        model = TinyGPT(cfg)
        root = a.out / label
        job = prepare_job(root, model, corpus, spec, prefix + "-" + label)
        branches = {}

        def on_branch(end, branch, info):
            digest = runlog.sha256_bytes(json.dumps(tensors(branch), sort_keys=True).encode())
            if end in branches and branches[end] != digest:
                raise RuntimeError("completed retrieval changed branch state")
            branches[end] = digest

        if label == "interrupted":
            job["stop_after"] = 9
            runlog.write_json(root / "job.json", job)
            portal.submit(root, purpose="functional")
            report = portal.wait(job["job_id"])
            if report["state"] != "interrupted":
                raise RuntimeError("controlled interruption did not occur")
        portal.train(
            root,
            model,
            spec,
            on_branch,
            purpose="functional",
            acceptance=None,
            recover=label == "interrupted",
        )
        first = dict(branches)
        # Host recovery after completion retrieves existing results without another dispatch.
        portal.train(
            root, model, spec, on_branch, purpose="functional", acceptance=None, recover=True
        )
        if branches != first:
            raise RuntimeError("completed recovery changed evaluated branch set")
        report = json.loads((root / "result.json").read_text())
        portal.retrieve(report["checkpoint"], root / "checkpoint.json")
        records.append(
            {
                "branches": branches,
                "checkpoint": json.loads((root / "checkpoint.json").read_text()),
                "report": report,
            }
        )
    # Exercise the actual runner entrypoints with isolated functional data.
    import e0_v2 as runner

    isolated = a.out.resolve() / "runner"
    isolated.mkdir()
    data = isolated / "data"
    data.mkdir()
    for split in ("train", "val", "test"):
        (data / (split + ".bin")).write_bytes(corpus.read_bytes())
    runner.ROOT, runner.DATA, runner.RAW = isolated, data, isolated / "raw"
    runner.RUNS, runner.EVIDENCE = isolated / "runs", isolated / "evidence"
    original_submit, original_argv = Portal.submit, sys.argv

    def interrupt_submit(client, root, **kwargs):
        job = json.loads((root / "job.json").read_text())
        job["stop_after"] = 5
        runlog.write_json(root / "job.json", job)
        return original_submit(client, root, **kwargs)

    Portal.submit = interrupt_submit
    sys.argv = [
        "e0_v2.py",
        "--run",
        "--smoke",
        "--tokens",
        "2048",
        "--val-bytes",
        "256",
        "--threads",
        "2",
        "--backend",
        "xbox",
        "--run-id",
        prefix + "-runner",
    ]
    try:
        code = None
        try:
            code = runner.main()
        except RuntimeError as error:
            if "did not complete: interrupted" not in str(error):
                raise
            code = 130
        summary = json.loads(
            (runner.EVIDENCE / "runs" / (prefix + "-runner") / "summary.json").read_text()
        )
        require_runner_interruption(code, str(summary.get("status", "")))
    finally:
        Portal.submit = original_submit
        sys.argv = original_argv
    sys.argv = ["e0_v2.py", "--resume", prefix + "-runner"]
    try:
        runner.main()
        before = (runner.EVIDENCE / "runs" / (prefix + "-runner") / "summary.json").read_bytes()
        runner.main()
        after = (runner.EVIDENCE / "runs" / (prefix + "-runner") / "summary.json").read_bytes()
        if before != after:
            raise RuntimeError("completed CLI recovery changed summary")
    finally:
        sys.argv = original_argv
    exact = records[0]["branches"] == records[1]["branches"] and all(
        records[0]["checkpoint"][key] == records[1]["checkpoint"][key]
        for key in ("step", "stream_position", "tensors", "moments")
    )
    result = {
        "purpose": "functional",
        "package": portal.package,
        "commit": device["commit"],
        "ok": exact,
        "reports": [r["report"] for r in records],
        "completed_retrieval_unchanged": True,
        "runner_resume_completed_idempotent": True,
        "interrupted_recovery_exact": exact,
    }
    runlog.write_json(a.out / "recovery.json", result)
    print(json.dumps({k: v for k, v in result.items() if k != "reports"}), flush=True)
    return 0 if exact else 1


if __name__ == "__main__":
    raise SystemExit(main())
