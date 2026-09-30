"""WSD training with cooldown branches from one trunk, and sliding-window evaluation."""

from __future__ import annotations

import copy
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass

import numpy as np
import torch
import torch.nn.functional as F

from .model import QLinear, TinyGPT
from .pack import pack_sections, unpack


@dataclass(frozen=True)
class TrainSpec:
    tokens: int  # T: the first cooldown ends at T; later ones at 2T, 4T, ...
    branches: int = 3  # cooldowns ending at T, 2T, 4T
    batch: int = 32
    lr: float = 3e-3
    wd: float = 0.1
    warmup_frac: float = 0.02  # of T
    cooldown_frac: float = 0.1  # of each branch's total tokens
    seed: int = 0


def lr_at(step: int, warmup: int, peak: float, cd_start: int | None, cd_len: int) -> float:
    """Warmup-stable-decay: linear warmup, flat, linear to 0 over the cooldown."""
    if step < warmup:
        return peak * (step + 1) / warmup
    if cd_start is None or step < cd_start:
        return peak
    return peak * max(0.0, 1 - (step - cd_start + 1) / cd_len)


def batches(data: np.ndarray, batch: int, ctx: int, rng: np.random.Generator) -> Iterator:
    while True:
        ix = rng.integers(0, len(data) - ctx - 1, size=batch)
        chunk = torch.from_numpy(np.stack([data[i : i + ctx + 1] for i in ix]).astype(np.int64))
        yield chunk[:, :-1], chunk[:, 1:]


@torch.no_grad()
def sliding_bpb(
    model: TinyGPT, data: np.ndarray, n_bytes: int, stride: int | None = None, batch: int = 32
) -> tuple[float, int]:
    """Bits per byte over data[:n_bytes]; each byte is scored once, with >= ctx-stride context
    except in the first window. Returns (bpb, scored bytes)."""
    ctx = model.cfg.ctx
    stride = stride or ctx // 2
    arr = torch.from_numpy(np.asarray(data[: min(n_bytes, len(data))]).astype(np.int64))
    n = arr.numel()
    starts = list(range(0, n - ctx, stride))  # every window is a full ctx + 1 bytes
    was = model.training
    model.eval()
    total, count = 0.0, 0
    for i in range(0, len(starts), batch):
        s = starts[i : i + batch]
        c = torch.stack([arr[j : j + ctx + 1] for j in s])
        nll = F.cross_entropy(model(c[:, :-1]).transpose(1, 2), c[:, 1:], reduction="none")
        for r, j in enumerate(s):
            first = 0 if j == 0 else ctx - stride  # score only bytes not scored before
            total += nll[r, first:].sum().item()
            count += ctx - first
    model.train(was)
    return total / count / np.log(2), count


def _optimizer(model: TinyGPT, spec: TrainSpec) -> torch.optim.Optimizer:
    q = [m.weight for m in model.modules() if isinstance(m, QLinear)]
    ids = {id(p) for p in q}
    other = [p for p in model.parameters() if id(p) not in ids]
    return torch.optim.AdamW(
        [{"params": q, "weight_decay": spec.wd}, {"params": other, "weight_decay": 0.0}],
        lr=spec.lr,
        betas=(0.9, 0.95),
    )


def train_wsd(
    model: TinyGPT,
    data: np.ndarray,
    spec: TrainSpec,
    on_branch: Callable[[int, TinyGPT, dict], None],
    log: Callable[[str], None] = print,
) -> None:
    """Trunk at constant LR; at each branch point clone, cool down, report, discard the clone."""
    ctx = model.cfg.ctx
    per_step = spec.batch * ctx
    T = max(1, spec.tokens // per_step)
    warm = max(1, int(spec.warmup_frac * T))
    ends = [T * 2**k for k in range(spec.branches)]
    gen = batches(data, spec.batch, ctx, np.random.default_rng(spec.seed))
    opt = _optimizer(model, spec)
    step, t0 = 0, time.time()

    def one_step(m: TinyGPT, o: torch.optim.Optimizer, lr: float) -> float:
        for g in o.param_groups:
            g["lr"] = lr
        x, y = next(gen)
        loss = F.cross_entropy(m(x).flatten(0, 1), y.flatten())
        o.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(m.parameters(), 1.0)
        o.step()
        return loss.item()

    for end in ends:
        cd_len = max(1, int(spec.cooldown_frac * end))
        cd_start = end - cd_len
        while step < cd_start:
            one_step(model, opt, lr_at(step, warm, spec.lr, None, 0))
            step += 1
        branch, bopt = branch_copy(model, opt, spec)
        for s in range(cd_start, end):
            one_step(branch, bopt, lr_at(s, warm, spec.lr, cd_start, cd_len))
        elapsed = time.time() - t0
        info = {
            "steps": end,
            "tokens": end * per_step,
            "trunk_steps": step,
            "wall_seconds": round(elapsed, 1),
        }
        log(f"branch end={end} tokens={end * per_step:,} wall={elapsed:.0f}s")
        on_branch(end, branch, info)
        del branch, bopt


def branch_copy(model: TinyGPT, opt: torch.optim.Optimizer, spec: TrainSpec):
    m2 = copy.deepcopy(model)
    o2 = _optimizer(m2, spec)
    o2.load_state_dict(copy.deepcopy(opt.state_dict()))
    return m2, o2


def evaluate_counted(
    model: TinyGPT, val: np.ndarray, test: np.ndarray, val_bytes: int, test_bytes: int
) -> dict:
    """Pack, unpack, and evaluate the counted model."""
    blob, parts = pack_sections(model)
    counted = unpack(blob)
    vb, vn = sliding_bpb(counted, val, val_bytes)
    tb, tn = sliding_bpb(counted, test, test_bytes)
    return {
        "model_bytes": len(blob),
        "sections": parts,
        "val_bpb": vb,
        "val_scored": vn,
        "test_bpb": tb,
        "test_scored": tn,
        "blob": blob,
    }
