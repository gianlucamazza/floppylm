"""E0 v2 — scalar frontier bench under the ADR 0005 protocol.

Usage:
  python experiments/e0_v2.py --plan [--budget-frac F] [--mlp gelu]
  python experiments/e0_v2.py --run --d 64 --layers 4 [--fmt ternary] [--seed 0] [...]
  python experiments/e0_v2.py --run --smoke            # functional check, not a result
  python experiments/e0_v2.py --grid --jobs 4 [...]    # solver grid, one thread per run
  python experiments/e0_v2.py --parity RUN_ID [RUN_ID ...]
  python experiments/e0_v2.py --freeze RUN_ID [...] --name NAME
  python experiments/e0_v2.py --final-test NAME
  python experiments/e0_v2.py --verify-data

Training and tuning read only train/val. The test split is read only by --final-test, on a
frozen selection whose artifact hashes are re-verified. Long runs: nohup, outside
background.slice (ADR 0003 amendment); use `python -u`.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
import traceback
from dataclasses import asdict
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from floppylm import data as data_mod
from floppylm import parity, runlog, shapes
from floppylm.model import GPTConfig, TinyGPT
from floppylm.pack import pack_sections, unpack
from floppylm.seed import seed_all
from floppylm.train import TrainSpec, schedule, sliding_bpb, train_wsd

DATA = ROOT / "data" / "tinystories"
RAW = ROOT / "data" / "raw"
RUNS = ROOT / "runs"
EVIDENCE = ROOT / "docs" / "evidence" / "e0-v2"
FULL_BUDGET_BITS = 11_000_000
SAT_THRESHOLD = 0.01
TOKENS_PER_PARAM = 20  # roadmap S1
VAL_BYTES, TEST_BYTES = 1 << 20, 1 << 21  # roadmap S7
FLOP_FORMULA = "3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens"


def budget_bits(frac: float) -> float:
    return FULL_BUDGET_BITS * frac


def build_config(a: argparse.Namespace) -> GPTConfig:
    base = GPTConfig(
        d=a.d,
        n_layers=a.layers,
        n_heads=a.d // shapes.HEAD_DIM,
        d_ff=a.d_ff or a.d,
        mlp=a.mlp,
        core_fmt=a.fmt,
        scale_policy=a.scale_policy,
        delta=a.delta,
        qk_norm=a.qk_norm,
        ctx=a.ctx,
    )
    if a.d_ff:
        return base
    cfg = shapes.fill_d_ff(base, budget_bits(a.budget_frac))
    if cfg is None:
        raise SystemExit(f"no d_ff fits the budget for d={a.d}, layers={a.layers}")
    return cfg


def flops(model: TinyGPT, tokens: int) -> float:
    return 3 * model.flops_per_token() * tokens


def notes_md(s: dict) -> str:
    kind = "**Smoke: prova funzionale, non un risultato scientifico.**\n\n" if s["smoke"] else ""
    rows = "\n".join(
        f"| {b['end_step']} | {b['tokens_seen']:,} | {b['model_bytes']:,} | {b['fill']:.4f} | "
        f"{b['val_bpb']:.4f} | `{b['sha256'][:12]}` |"
        for b in s["branches"]
    )
    sat = s["saturation"]
    return f"""# {s["run_id"]}

{kind}Stato: **{s["status"]}**. Configurazione e ambiente completi in `summary.json`; manifest in
`runs/{s["run_id"]}/manifest.json`.

| Fine cooldown (step) | Token visti | Byte | Riempimento | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
{rows}

- Saturazione: {sat["verdict"]} (bpb(4T) − bpb(2T) = {sat["delta_signed"]}).
- Parità individuale ±1% sul target: {s["parity_individual_ok"]}.
- Compute stimato: {s["compute"]["total_flops"]:.3e} FLOP ({FLOP_FORMULA}), wall
  {s["compute"]["wall_seconds"]:.0f} s a {s["environment"]["torch_threads"]} thread.

Non misurato qui: test (solo `--final-test` su selezione congelata), σ appaiata, confronto fra
bracci.
"""


def cmd_run(a: argparse.Namespace) -> int:
    if a.smoke:
        a.d, a.layers, a.d_ff, a.ctx, a.budget_frac = 32, 1, 48, 64, a.budget_frac
        a.tokens, a.batch = a.tokens or 8 * 64 * 16, 8
        a.val_bytes = min(a.val_bytes, 1 << 14)
    cfg = build_config(a)
    seed_all(a.seed)
    torch.set_num_threads(a.threads)
    model = TinyGPT(cfg)
    tokens = a.tokens or TOKENS_PER_PARAM * model.stored_params()
    spec = TrainSpec(
        tokens=tokens, branches=a.branches, batch=a.batch, lr=a.lr, wd=a.wd, seed=a.seed
    )
    tag = ("smoke" if a.smoke else f"b{round(1 / a.budget_frac)}") + (
        f"-{cfg.core_fmt}-d{cfg.d}-l{cfg.n_layers}-f{cfg.d_ff}-s{a.seed}"
    )
    run_id = runlog.new_run_id(tag)
    run_dir = runlog.make_exclusive_dir(RUNS / run_id)
    ev_dir = runlog.make_exclusive_dir(EVIDENCE / "runs" / run_id)
    target = budget_bits(a.budget_frac) / 8
    manifest = {
        "run_id": run_id,
        "created": runlog.now(),
        "config": cfg.to_dict(),
        "spec": asdict(spec),
        "schedule": schedule(spec, cfg.ctx),
        "budget_bits": budget_bits(a.budget_frac),
        "target_bytes": target,
        "smoke": a.smoke,
        "data": data_mod.manifest(DATA, RAW),
        "sources": runlog.sources(ROOT),
        "environment": runlog.environment(a.threads),
        "argv": sys.argv,
    }
    runlog.write_json(run_dir / "manifest.json", manifest)
    runlog.set_status(run_dir, "running", pid=os.getpid())
    summary = {
        "run_id": run_id,
        "smoke": a.smoke,
        "config": cfg.to_dict(),
        "spec": asdict(spec),
        "target_bytes": target,
        "environment": manifest["environment"],
        "sources": manifest["sources"],
        "data_sha256": {
            s: v["sha256"] for s, v in manifest["data"]["verified"]["prepared"].items()
        },
        "branches": [],
        "status": "running",
    }
    train = data_mod.load(DATA, "train")
    val = data_mod.load(DATA, "val")  # test is never opened here
    t0 = time.time()

    def on_checkpoint(ckpt: dict) -> None:
        path = run_dir / f"trunk-{ckpt['step']}.pt"
        tmp = path.with_suffix(".pt.tmp")
        torch.save(ckpt, tmp)
        tmp.replace(path)

    def on_branch(end: int, branch: TinyGPT, info: dict) -> None:
        blob, parts = pack_sections(branch)
        counted = unpack(blob)
        te = time.time()
        vb, vn = sliding_bpb(counted, val, a.val_bytes)
        path = run_dir / f"branch-{end}.flp"
        runlog.write_atomic(path, blob)
        rec = {
            **info,
            "model_bytes": len(blob),
            "sections": parts,
            "fill": len(blob) / target,
            "sha256": runlog.sha256_bytes(blob),
            "artifact": str(path.relative_to(ROOT)),
            "val_bpb": vb,
            "val_scored_bytes": vn,
            "eval_seconds": time.time() - te,
            "cooldown_flops": flops(model, info["cooldown_steps"] * spec.batch * cfg.ctx),
        }
        summary["branches"].append(rec)
        runlog.write_json(ev_dir / "summary.json", summary)  # partial, status still running
        print(
            json.dumps({k: rec[k] for k in ("end_step", "model_bytes", "fill", "val_bpb")}),
            flush=True,
        )

    def on_signal(signum, frame):  # noqa: ARG001
        raise KeyboardInterrupt(f"signal {signum}")

    signal.signal(signal.SIGTERM, on_signal)
    try:
        acct = train_wsd(
            model,
            train,
            spec,
            on_branch,
            on_checkpoint,
            log=lambda s: print(f"[{run_id}] {s}", flush=True),
        )
    except KeyboardInterrupt as e:
        summary["status"] = "interrupted"
        runlog.write_json(ev_dir / "summary.json", summary)
        runlog.set_status(run_dir, "interrupted", reason=str(e))
        return 130
    except Exception as e:
        summary["status"] = "failed"
        summary["error"] = repr(e)
        runlog.write_json(ev_dir / "summary.json", summary)
        runlog.set_status(run_dir, "failed", error=traceback.format_exc())
        raise

    bs = summary["branches"]
    if len(bs) >= 3:
        delta = bs[2]["val_bpb"] - bs[1]["val_bpb"]
        verdict = "saturo" if abs(delta) < SAT_THRESHOLD else "non saturo"
    else:
        delta, verdict = None, "non determinato (meno di 3 cooldown)"
    trunk_tokens = acct["trunk_tokens"]
    cd_tokens = sum(c["cooldown_steps"] for c in acct["cooldowns"]) * spec.batch * cfg.ctx
    summary |= {
        "status": "completed",
        "saturation": {
            "criterion": f"|bpb(4T) - bpb(2T)| < {SAT_THRESHOLD}",
            "delta_signed": delta,
            "verdict": verdict,
        },
        "parity_individual_ok": all(abs(b["fill"] - 1) <= parity.TOLERANCE for b in bs),
        "compute": {
            "formula": FLOP_FORMULA,
            "flops_per_token_forward": model.flops_per_token(),
            "trunk_tokens": trunk_tokens,
            "trunk_flops": flops(model, trunk_tokens),
            "cooldown_tokens": cd_tokens,
            "cooldown_flops": flops(model, cd_tokens),
            "total_tokens": trunk_tokens + cd_tokens,
            "total_flops": flops(model, trunk_tokens + cd_tokens),
            "trunk_seconds": acct["trunk_seconds"],
            "wall_seconds": time.time() - t0,
            "eval_seconds": sum(b["eval_seconds"] for b in bs),
        },
        "finished": runlog.now(),
    }
    runlog.write_json(ev_dir / "summary.json", summary)
    runlog.write_atomic(ev_dir / "notes.md", notes_md(summary))
    runlog.set_status(run_dir, "completed")
    print(f"completed {run_id}", flush=True)
    return 0


def _summary(run_id: str) -> dict:
    s = json.loads((EVIDENCE / "runs" / run_id / "summary.json").read_text())
    if s["status"] != "completed":
        raise SystemExit(f"{run_id} is {s['status']}, not completed")
    return s


def cmd_parity(a: argparse.Namespace) -> int:
    sums = {r: _summary(r) for r in a.parity}
    targets = {s["target_bytes"] for s in sums.values()}
    if len(targets) != 1:
        raise SystemExit("runs have different byte targets")
    sizes = {r: s["branches"][-1]["model_bytes"] for r, s in sums.items()}
    ok, reasons = parity.admissible(sizes, targets.pop())
    print(json.dumps({"admissible": ok, "sizes": sizes, "reasons": reasons}, indent=1))
    return 0 if ok else 1


def cmd_freeze(a: argparse.Namespace) -> int:
    items = []
    for r in a.freeze:
        b = _summary(r)["branches"][-1]
        if runlog.sha256_file(ROOT / b["artifact"]) != b["sha256"]:
            raise SystemExit(f"{r}: artifact hash mismatch")
        items.append(
            {"run_id": r, "artifact": b["artifact"], "sha256": b["sha256"], "val_bpb": b["val_bpb"]}
        )
    path = EVIDENCE / "selections" / f"{a.name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "x") as f:  # a selection is written once
        json.dump({"name": a.name, "frozen_at": runlog.now(), "items": items}, f, indent=1)
    print(path)
    return 0


def cmd_final_test(a: argparse.Namespace) -> int:
    sel = json.loads((EVIDENCE / "selections" / f"{a.final_test}.json").read_text())
    out = EVIDENCE / "selections" / f"{a.final_test}.test.json"
    if out.exists():
        raise SystemExit(f"{out} exists: the final test runs once per selection")
    test = data_mod.load(DATA, "test")
    results = []
    for it in sel["items"]:
        blob = (ROOT / it["artifact"]).read_bytes()
        if runlog.sha256_bytes(blob) != it["sha256"]:
            raise SystemExit(f"{it['run_id']}: artifact hash mismatch")
        bpb, n = sliding_bpb(unpack(blob), test, TEST_BYTES)
        results.append({**it, "test_bpb": bpb, "test_scored_bytes": n})
    runlog.write_json(
        out,
        {
            "selection": a.final_test,
            "evaluated_at": runlog.now(),
            "test_sha256": data_mod.manifest(DATA, RAW)["verified"]["prepared"]["test"]["sha256"],
            "results": results,
        },
    )
    print(out)
    return 0


def cmd_plan(a: argparse.Namespace) -> int:
    budget = budget_bits(a.budget_frac)
    base = GPTConfig(
        mlp=a.mlp, core_fmt=a.fmt, scale_policy=a.scale_policy, delta=a.delta, ctx=a.ctx
    )
    print(f"budget {budget:,.0f} bit ({budget / 8:,.0f} B)")
    for c in shapes.grid(base, budget):
        bits = c.nominal_bits()
        print(
            f"{c.core_fmt:8s} d={c.d:4d} L={c.n_layers:2d} d_ff={c.d_ff:5d}"
            f" fill={bits / budget:.4f}"
            f" emb_share={c.vocab * c.d * 4 / bits:.2f}"
        )
    return 0


def cmd_grid(a: argparse.Namespace) -> int:
    base = GPTConfig(
        mlp=a.mlp, core_fmt=a.fmt, scale_policy=a.scale_policy, delta=a.delta, ctx=a.ctx
    )
    cfgs = shapes.grid(base, budget_bits(a.budget_frac))
    log_dir = runlog.make_exclusive_dir(RUNS / runlog.new_run_id("grid"))
    procs: list[subprocess.Popen] = []
    for i, c in enumerate(cfgs):
        while len([p for p in procs if p.poll() is None]) >= a.jobs:
            time.sleep(5)
        cmd = [
            sys.executable,
            "-u",
            __file__,
            "--run",
            "--d",
            str(c.d),
            "--layers",
            str(c.n_layers),
            "--fmt",
            a.fmt,
            "--mlp",
            a.mlp,
            "--scale-policy",
            a.scale_policy,
            "--delta",
            str(a.delta),
            "--ctx",
            str(a.ctx),
            "--budget-frac",
            str(a.budget_frac),
            "--seed",
            str(a.seed),
            "--lr",
            str(a.lr),
            "--wd",
            str(a.wd),
            "--batch",
            str(a.batch),
            "--threads",
            "1",
        ] + (["--qk-norm"] if a.qk_norm else [])
        with open(log_dir / f"{i:02d}.log", "w") as f:
            procs.append(subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT))
    codes = [p.wait() for p in procs]
    print(json.dumps({"grid_dir": str(log_dir), "exit_codes": codes}))
    return 0 if all(c == 0 for c in codes) else 1


def cmd_verify_data(a: argparse.Namespace) -> int:  # noqa: ARG001
    r = data_mod.verify_reproducible(RAW, DATA, RUNS / "tmp")
    runlog.write_json(DATA / "reproducibility.json", r)
    print(json.dumps(r, indent=1))
    return 0 if r["reproduced"] else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--plan", action="store_true")
    mode.add_argument("--run", action="store_true")
    mode.add_argument("--grid", action="store_true")
    mode.add_argument("--parity", nargs="+", metavar="RUN_ID")
    mode.add_argument("--freeze", nargs="+", metavar="RUN_ID")
    mode.add_argument("--final-test", metavar="NAME")
    mode.add_argument("--verify-data", action="store_true")
    ap.add_argument("--smoke", action="store_true", help="with --run: tiny functional check")
    ap.add_argument("--name", help="selection name for --freeze")
    ap.add_argument("--budget-frac", type=float, default=1 / 16)
    ap.add_argument("--fmt", choices=("ternary", "2bit"), default="ternary")
    ap.add_argument("--mlp", choices=("gelu", "relu2", "swiglu"), default="gelu")
    ap.add_argument("--scale-policy", choices=("row16", "row8log", "tensor16"), default="row16")
    ap.add_argument("--delta", type=float, default=0.5)
    ap.add_argument("--qk-norm", action="store_true")
    ap.add_argument("--ctx", type=int, default=256)
    ap.add_argument("--d", type=int, default=64)
    ap.add_argument("--layers", type=int, default=4)
    ap.add_argument("--d-ff", type=int, default=0, help="0 = fill the budget")
    ap.add_argument("--tokens", type=int, default=0, help="T; 0 = 20 x stored params")
    ap.add_argument("--branches", type=int, default=3)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--lr", type=float, default=3e-3)
    ap.add_argument("--wd", type=float, default=0.1)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--val-bytes", type=int, default=VAL_BYTES)
    a = ap.parse_args()
    if a.plan:
        return cmd_plan(a)
    if a.run:
        return cmd_run(a)
    if a.grid:
        return cmd_grid(a)
    if a.parity:
        return cmd_parity(a)
    if a.freeze:
        if not a.name:
            ap.error("--freeze needs --name")
        return cmd_freeze(a)
    if a.final_test:
        return cmd_final_test(a)
    if a.verify_data:
        return cmd_verify_data(a)
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
