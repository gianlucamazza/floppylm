"""E0-lite — byte-level bench and scalar frontier (ternary / 2-bit) at miniature budgets.

Usage:
  python experiments/e0_lite.py --plan [--budget-frac 0.0625]
  python experiments/e0_lite.py --smoke
  python experiments/e0_lite.py --run --fmt ternary --d 96 --layers 3 [--seed 0] [--tokens N]
  python experiments/e0_lite.py --full [--budget-frac 0.0625] [--seed 0]

Budget: 11 Mbit * budget-frac of coded *model* bytes (ADR 0004 amendment §1).
Long runs: nohup, outside background.slice (ADR 0003 amendment).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from floppylm.data import load
from floppylm.metrics import bpb
from floppylm.model import GPTConfig, TinyGPT
from floppylm.pack import nominal_bits, pack, unpack
from floppylm.seed import seed_all

DATA = ROOT / "data" / "tinystories"
EVIDENCE = ROOT / "docs" / "evidence" / "e0-lite"
RUNS = ROOT / "runs"
FULL_BUDGET_BITS = 11_000_000
HEAD_DIM = 16
WIDTHS = tuple(range(64, 257, 16))
EMB_SHARE = (0.08, 0.20)  # ADR 0004 amendment §2: embedding ~15% of bits
FORMATS = ("ternary", "2bit")
BATCH, CTX = 32, 256
TOKENS_PER_PARAM = 20
EVAL_VAL_BYTES, EVAL_TEST_BYTES = 1 << 20, 1 << 21


def max_layers(fmt: str, d: int, budget_bits: float) -> int:
    n = 0
    while nominal_bits(GPTConfig(d=d, n_layers=n + 1, n_heads=d // HEAD_DIM, core_fmt=fmt)) <= (
        budget_bits
    ):
        n += 1
    return n


def shape_grid(budget_bits: float) -> list[GPTConfig]:
    grid = []
    for fmt in FORMATS:
        for d in WIDTHS:
            n = max_layers(fmt, d, budget_bits)
            cfg = GPTConfig(d=d, n_layers=n, n_heads=d // HEAD_DIM, core_fmt=fmt)
            share = cfg.vocab * d * 4 / nominal_bits(cfg)
            if 2 <= n <= 16 and EMB_SHARE[0] <= share <= EMB_SHARE[1]:
                grid.append(cfg)
    return grid


def stored_params(cfg: GPTConfig) -> int:
    return cfg.n_layers * 12 * cfg.d * cfg.d + cfg.vocab * cfg.d


def batches(data: np.ndarray, rng: np.random.Generator):
    while True:
        ix = rng.integers(0, len(data) - CTX - 1, size=BATCH)
        chunk = torch.from_numpy(np.stack([data[i : i + CTX + 1] for i in ix]).astype(np.int64))
        yield chunk[:, :-1], chunk[:, 1:]


@torch.no_grad()
def evaluate(model: TinyGPT, data: np.ndarray, n_bytes: int) -> float:
    """Non-overlapping windows of CTX+1 bytes from the start of the split."""
    model.eval()
    n_win = min(n_bytes, len(data) - 1) // (CTX + 1)
    arr = torch.from_numpy(np.asarray(data[: n_win * (CTX + 1)]).astype(np.int64))
    arr = arr.view(n_win, CTX + 1)
    total = 0.0
    for i in range(0, n_win, 64):
        c = arr[i : i + 64]
        total += bpb(model(c[:, :-1]), c[:, 1:]) * c.size(0)
    model.train()
    return total / n_win


def train(cfg: GPTConfig, seed: int, tokens: int, tag: str, budget_bits: float) -> dict:
    seed_all(seed)
    torch.set_num_threads(4)
    train_data, val_data, test_data = load(DATA, "train"), load(DATA, "val"), load(DATA, "test")
    model = TinyGPT(cfg)
    steps = max(1, tokens // (BATCH * CTX))
    warm = max(1, steps // 20)
    opt = torch.optim.AdamW(model.parameters(), lr=3e-3, betas=(0.9, 0.95), weight_decay=0.01)
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt,
        lambda s: (
            (s + 1) / warm
            if s < warm
            else 0.1 + 0.45 * (1 + math.cos(math.pi * (s - warm) / max(1, steps - warm)))
        ),
    )
    gen = batches(train_data, np.random.default_rng(seed))
    curve: list[tuple[int, float]] = []
    t0 = time.time()
    for step in range(steps):
        x, y = next(gen)
        loss = torch.nn.functional.cross_entropy(model(x).flatten(0, 1), y.flatten())
        opt.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        sched.step()
        if (step + 1) % max(1, steps // 10) == 0 or step + 1 == steps:
            curve.append((step + 1, evaluate(model, val_data, EVAL_VAL_BYTES // 4)))
            print(f"[{tag}] step {step + 1}/{steps} val_bpb {curve[-1][1]:.4f}", flush=True)
    train_s = time.time() - t0

    blob = pack(model)
    RUNS.joinpath(tag).mkdir(parents=True, exist_ok=True)
    RUNS.joinpath(tag, "model.flp").write_bytes(blob)
    counted = unpack(blob)  # every reported bpb comes from the counted bytes
    tail = [v for s, v in curve if s >= 0.9 * steps]
    n_eff = stored_params(cfg)
    return {
        "tag": tag,
        "config": cfg.__dict__,
        "seed": seed,
        "budget_bits": budget_bits,
        "model_bytes": len(blob),
        "model_bits": 8 * len(blob),
        "fits_budget": 8 * len(blob) <= budget_bits,
        "nominal_bits": nominal_bits(cfg),
        "core_params": model.core_params(),
        "stored_params": n_eff,
        "emb_share_nominal": cfg.vocab * cfg.d * 4 / nominal_bits(cfg),
        "tokens": steps * BATCH * CTX,
        "tokens_per_stored_param": steps * BATCH * CTX / n_eff,
        "train_flops_6n": 6 * n_eff * steps * BATCH * CTX,
        "train_seconds": round(train_s, 1),
        "tok_per_s": round(steps * BATCH * CTX / train_s),
        "val_curve": curve,
        "tail_delta_bpb": (tail[0] - tail[-1]) if len(tail) > 1 else None,
        "val_bpb": evaluate(counted, val_data, EVAL_VAL_BYTES),
        "test_bpb": evaluate(counted, test_data, EVAL_TEST_BYTES),
        "torch_threads": torch.get_num_threads(),
    }


def write(result: dict) -> None:
    path = EVIDENCE / "runs" / f"{result['tag']}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=1))
    print(json.dumps({k: result[k] for k in ("tag", "model_bytes", "val_bpb", "test_bpb")}))


def tag_of(cfg: GPTConfig, frac: float, seed: int) -> str:
    return f"b{round(1 / frac)}-{cfg.core_fmt}-d{cfg.d}-l{cfg.n_layers}-s{seed}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--plan", action="store_true", help="print the shape grid, no training")
    mode.add_argument("--smoke", action="store_true", help="tiny run, seconds, no evidence")
    mode.add_argument("--run", action="store_true", help="train one config")
    mode.add_argument("--full", action="store_true", help="train the whole grid (long: nohup)")
    ap.add_argument("--budget-frac", type=float, default=1 / 16)
    ap.add_argument("--fmt", choices=FORMATS, default="ternary")
    ap.add_argument("--d", type=int, default=96)
    ap.add_argument("--layers", type=int, default=3)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--tokens", type=int, default=0, help="0 = 20 x stored params")
    args = ap.parse_args()
    if not (args.plan or args.smoke or args.run or args.full):
        ap.print_help()
        return 2

    budget = FULL_BUDGET_BITS * args.budget_frac
    if args.plan:
        print(f"budget {budget:,.0f} bit ({budget / 8 / 1024:.1f} KiB)")
        for c in shape_grid(budget):
            print(
                f"{c.core_fmt:8s} d={c.d:4d} L={c.n_layers:2d} nominal={nominal_bits(c):>10,.0f}"
                f" emb_share={c.vocab * c.d * 4 / nominal_bits(c):.2f}"
                f" stored={stored_params(c):>9,d} tokens={TOKENS_PER_PARAM * stored_params(c):,d}"
            )
        return 0
    if args.smoke:
        cfg = GPTConfig(d=32, n_layers=1, n_heads=2)
        r = train(cfg, 0, 30 * BATCH * CTX, "smoke", budget)
        print(json.dumps({k: r[k] for k in ("model_bytes", "val_bpb", "test_bpb", "tok_per_s")}))
        return 0
    configs = (
        shape_grid(budget)
        if args.full
        else [
            GPTConfig(d=args.d, n_layers=args.layers, n_heads=args.d // HEAD_DIM, core_fmt=args.fmt)
        ]
    )
    for cfg in configs:
        tokens = args.tokens or TOKENS_PER_PARAM * stored_params(cfg)
        write(train(cfg, args.seed, tokens, tag_of(cfg, args.budget_frac, args.seed), budget))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
