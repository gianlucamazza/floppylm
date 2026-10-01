"""Exercise actual Xbox app suspension through Dev Home, then exact checkpoint recovery."""

from __future__ import annotations

import argparse
import base64
import json
import sys
import time
from pathlib import Path
from urllib.parse import urlencode

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from floppylm import runlog
from floppylm.model import GPTConfig, TinyGPT
from floppylm.seed import seed_all
from floppylm.train import TrainSpec
from floppylm_xbox.jobs import prepare_job
from floppylm_xbox.portal import Portal


def launch(portal, package, app):
    query = urlencode(
        {
            k: base64.b64encode(v.encode()).decode()
            for k, v in {"package": package, "appid": app}.items()
        }
    )
    portal.request("POST", "/api/taskmanager/app?" + query, b"", {"Content-Length": "0"})


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
        raise RuntimeError("lifecycle proof requires the validated package")
    installed = portal.request("GET", "/api/app/packagemanager/packages", json_result=True)
    home = [
        x
        for x in installed["InstalledPackages"]
        if x["PackageFamilyName"] == "Microsoft.Xbox.DevHome"
    ]
    if len(home) != 1:
        raise RuntimeError("expected the installed Dev Home package")
    cfg = GPTConfig(d=32, n_layers=1, n_heads=2, d_ff=48, ctx=8)
    spec = TrainSpec(tokens=8192, batch=2, seed=19)
    corpus = a.out / "corpus.bin"
    corpus.write_bytes(b"the cat sat on the mat. " * 100)
    prefix = runlog.new_run_id("lifecycle")
    seed_all(19)
    job = prepare_job(a.out / "suspended", TinyGPT(cfg), corpus, spec, prefix + "-suspended")
    portal.submit(a.out / "suspended", purpose="functional")
    deadline = time.monotonic() + 120
    while True:
        try:
            report = portal.status(job["job_id"])
        except FileNotFoundError:
            if time.monotonic() >= deadline:
                raise TimeoutError("job was not claimed before suspension probe") from None
            time.sleep(1)
            continue
        if report["state"] != "running":
            raise RuntimeError("job stopped before suspension probe")
        if report.get("trunk_step", 0) >= 64:
            break
        if time.monotonic() >= deadline:
            raise TimeoutError("no live checkpoint before suspension")
        time.sleep(1)
    runlog.write_json(a.out / "before-suspend.json", report)
    trainer_aumid = portal.package.split("_")[0] + "_" + portal.package.split("__")[-1] + "!App"
    try:
        launch(portal, home[0]["PackageFullName"], home[0]["PackageRelativeId"])
        time.sleep(8)
        suspended = portal.status(job["job_id"])
        runlog.write_json(a.out / "after-suspend.json", suspended)
    finally:
        launch(portal, portal.package, trainer_aumid)
    # A foreground activation restores the app after the real lifecycle event.
    report = portal.wait(job["job_id"])
    marker = portal.get(job["job_id"] + ".cancel").decode()
    if report["state"] != "interrupted" or marker != "suspend":
        raise RuntimeError("actual suspension did not produce a checkpoint interruption")
    portal.train(
        a.out / "suspended",
        TinyGPT(cfg),
        spec,
        lambda *_: None,
        purpose="functional",
        acceptance=None,
        recover=True,
    )
    resumed = json.loads((a.out / "suspended/result.json").read_text())
    seed_all(19)
    prepare_job(a.out / "full", TinyGPT(cfg), corpus, spec, prefix + "-full")
    portal.train(
        a.out / "full", TinyGPT(cfg), spec, lambda *_: None, purpose="functional", acceptance=None
    )
    full = json.loads((a.out / "full/result.json").read_text())
    for label, result in (("full", full), ("suspended", resumed)):
        portal.retrieve(result["checkpoint"], a.out / (label + "-checkpoint.json"))
    left = json.loads((a.out / "full-checkpoint.json").read_text())
    right = json.loads((a.out / "suspended-checkpoint.json").read_text())
    exact = all(left[k] == right[k] for k in ("step", "stream_position", "tensors", "moments"))
    exact &= [b["artifact"]["sha256"] for b in full["branches"]] == [
        b["artifact"]["sha256"] for b in resumed["branches"]
    ]
    proof = {
        "purpose": "functional",
        "package": portal.package,
        "commit": device["commit"],
        "suspend_marker": marker,
        "checkpoint_interruption": report,
        "ok": exact,
    }
    runlog.write_json(a.out / "lifecycle.json", proof)
    print(json.dumps({"lifecycle_exact": exact}), flush=True)
    return 0 if exact else 1


if __name__ == "__main__":
    raise SystemExit(main())
