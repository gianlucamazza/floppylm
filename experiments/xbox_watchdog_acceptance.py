"""Functional real-deadline watchdog, process-exit and exact-recovery acceptance.

Run only on an idle accepted package. This command explicitly restarts the app
once after observing watchdog exit; it never starts a scientific campaign.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from e0_recover import app_processes, start_package

from floppylm import runlog
from floppylm.model import GPTConfig, TinyGPT
from floppylm.seed import seed_all
from floppylm.train import TrainSpec
from floppylm_xbox.jobs import prepare_job
from floppylm_xbox.portal import Portal, check_acceptance


def protected_job_ids():
    """Use committed scientific provenance, not filename guesses, to select bindings."""
    evidence = ROOT / "docs/evidence/e0-v2"
    ids = set()
    for path in (evidence / "campaigns").glob("*/campaign.json"):
        state = json.loads(path.read_text())
        for record in state["trials"].values():
            ids.add(record["run_id"])
            if record.get("repair_id"):
                ids.add(record["repair_id"])
    for path in (evidence / "runs").glob("*/summary.json"):
        summary = json.loads(path.read_text())
        if summary.get("backend_name") == "xbox" and not summary.get("smoke", True):
            ids.add(summary["run_id"])
    return ids


def protected_snapshot(portal, names=None, *, job_ids=None):
    """Bind pre-existing inputs and scientific result descriptors; do not rewrite them."""
    inventory = portal.files()
    job_ids = protected_job_ids() if job_ids is None else job_ids
    if names is None:
        if any(name.endswith(".ready") for name in inventory):
            raise RuntimeError("pending inbox work; watchdog qualification refused")
        names = sorted(inventory)
    records = {}
    for name in names:
        if name not in inventory:
            raise RuntimeError("protected inbox file disappeared: " + name)
        item = {"bytes": inventory[name]}
        if name.endswith(".job.json") and name.removesuffix(".job.json") in job_ids:
            payload = portal.get(name)
            item["sha256"] = runlog.sha256_bytes(payload)
            if name.endswith(".job.json"):
                job = json.loads(payload)
                if job.get("purpose") == "scientific":
                    try:
                        status = portal.status(job["job_id"])
                    except FileNotFoundError:
                        status = None
                    if status and status.get("state") == "running":
                        raise RuntimeError("scientific running record requires diagnosis first")
                    item["scientific_status"] = status
        records[name] = item
    return records


def observe_exit(
    portal,
    job_id,
    job_sha,
    commit,
    out,
    *,
    clock=time.monotonic,
    sleep=time.sleep,
    processes=app_processes,
):
    """Observe the real 600-second watchdog without signalling the worker."""
    started = clock()
    samples = []
    owner = None
    while clock() - started < 780:
        if not processes(portal):
            break
        try:
            worker = portal.worker(commit=commit)
        except RuntimeError:
            # LocalState may vanish between the process listing and the read.
            if not processes(portal):
                break
            raise
        if worker.get("active_job") != {"job_id": job_id, "job_sha256": job_sha}:
            raise RuntimeError("watchdog observation lost the exact job owner")
        owner = owner or worker["worker_id"]
        if worker["worker_id"] != owner:
            raise RuntimeError("worker changed before an explicit restart")
        sample = {"elapsed_seconds": clock() - started, "worker": worker}
        samples.append(sample)
        Portal._runtime_event(out, {"event": "watchdog_sample", **sample}, lambda _: None)
        sleep(2)
    else:
        raise TimeoutError("watchdog did not exit within qualification observation window")
    elapsed = clock() - started
    if len(samples) < 2 or elapsed < 590:
        raise RuntimeError("premature exit does not prove the real watchdog deadline")
    if samples[-1]["worker"]["heartbeat_seq"] <= samples[0]["worker"]["heartbeat_seq"]:
        raise RuntimeError("heartbeat did not advance independently of frozen work")
    if len({s["worker"]["progress"]["completed_fence"] for s in samples[-2:]}) != 1:
        raise RuntimeError("final samples did not observe a frozen published fence")
    return {
        "worker_id": owner,
        "elapsed_seconds": elapsed,
        "samples": len(samples),
        "process_exited": True,
        "heartbeat_advanced": True,
    }


def verify_fault(status, job_sha):
    fault = status.get("runtime_fault", {})
    if (
        status.get("state") != "interrupted"
        or status.get("job_sha256") != job_sha
        or fault.get("kind") != "progress_stall"
        or fault.get("error") != "published progress frozen without an in-flight GPU request"
        or fault.get("requested_fence") != 0
        or fault.get("elapsed_ms", 0) < 600000
        or not status.get("checkpoint")
    ):
        raise RuntimeError("missing bound published-fence fault/checkpoint evidence")


def compare_results(control, resumed, left, right):
    return (
        all(left[k] == right[k] for k in ("step", "stream_position", "tensors", "moments"))
        and len(control["branches"]) == len(resumed["branches"]) == 3
        and [b["artifact"]["sha256"] for b in control["branches"]]
        == [b["artifact"]["sha256"] for b in resumed["branches"]]
    )


def qualify(portal, out, accepted):
    device = json.loads(portal.get("device.json", ""))
    check_acceptance(accepted, device, portal.package)
    if not device.get("hardware_gpu"):
        raise RuntimeError("watchdog acceptance requires the hardware GPU")
    worker = portal.live_worker(commit=device["commit"])
    if worker["state"] != "ready" or worker["active_job"] is not None:
        raise RuntimeError("watchdog acceptance requires an idle live worker")
    baseline = protected_snapshot(portal)
    runlog.write_json(out / "protected-before.json", baseline)
    runlog.write_json(out / "device-before.json", device)
    runlog.write_json(out / "worker-before.json", worker)
    cfg = GPTConfig(d=32, n_layers=1, n_heads=2, d_ff=48, ctx=8)
    spec = TrainSpec(tokens=128, batch=2, seed=19)
    corpus = out / "corpus.bin"
    corpus.write_bytes(b"the cat sat on the mat. " * 100)
    prefix = runlog.new_run_id("watchdog")
    results, checkpoints = {}, {}
    observation = {}
    for label in ("control", "probe"):
        seed_all(19)
        model = TinyGPT(cfg)
        root = out / label
        job = prepare_job(root, model, corpus, spec, prefix + "-" + label)
        if label == "probe":
            job["runtime_fault_probe"] = {
                "kind": "published_fence_stall",
                "after_checkpoint_step": 2,
            }
            runlog.write_json(root / "job.json", job)
            portal.submit(root, purpose="functional")
            binding = json.loads((root / "submitted.json").read_text())
            observation = observe_exit(
                portal, job["job_id"], binding["sha256"], device["commit"], out
            )
            runlog.write_json(out / "process-exit.json", observation)
            # Explicit, once-only acceptance step after observed exit, never a keep-alive.
            if start_package(portal) != "started":
                raise RuntimeError("process reappeared without the acceptance restart")
            new_worker = portal.live_worker(commit=device["commit"])
            if (
                new_worker["worker_id"] == observation["worker_id"]
                or new_worker["state"] != "ready"
                or new_worker["active_job"] is not None
            ):
                raise RuntimeError("restart did not produce a new idle worker")
            runlog.write_json(out / "worker-after-restart.json", new_worker)
            fault = portal.status(job["job_id"])
            runlog.write_json(out / "watchdog-fault.json", fault)
            verify_fault(fault, binding["sha256"])
            portal.retrieve(fault["checkpoint"], out / "interrupted-checkpoint.json")
        portal.train(
            root,
            model,
            spec,
            lambda *_: None,
            purpose="functional",
            acceptance=None,
            recover=label == "probe",
        )
        results[label] = json.loads((root / "result.json").read_text())
        checkpoint = out / (label + "-checkpoint.json")
        portal.retrieve(results[label]["checkpoint"], checkpoint)
        checkpoints[label] = json.loads(checkpoint.read_text())
    after = protected_snapshot(portal, baseline)
    runlog.write_json(out / "protected-after.json", after)
    exact = compare_results(
        results["control"], results["probe"], checkpoints["control"], checkpoints["probe"]
    )
    proof = {
        "purpose": "functional",
        "package": portal.package,
        "commit": device["commit"],
        "observation": observation,
        "exact_recovery": exact,
        "protected_unchanged": baseline == after,
        "protection_scope": "pre-existing inbox inventory; committed scientific job JSON "
        "bytes and result descriptors; archived payloads checked by inventory, not rehashed",
        "probe_jobs": [prefix + "-control", prefix + "-probe"],
        "ok": exact and baseline == after,
    }
    runlog.write_json(out / "watchdog.json", proof)
    if not proof["ok"]:
        raise RuntimeError("watchdog recovery or protected-state comparison failed")
    return proof


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--acceptance", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    torch.set_num_threads(2)
    try:
        proof = qualify(Portal.configured(), args.out, json.loads(args.acceptance.read_text()))
    except BaseException as error:
        runlog.write_json(args.out / "failure.json", {"ok": False, "error": repr(error)})
        raise
    print(json.dumps(proof), flush=True)


if __name__ == "__main__":
    main()
