"""WSD training with cooldown branches from one trunk, trunk checkpoints, sliding evaluation.

Protocol (ADR 0005 §3–5): the trunk runs at constant LR after warmup; for each branch end
E in (T, 2T, 4T, ...) a deep copy of model, optimizer and data stream cools down linearly to
zero over the last `cooldown_frac * E` steps. The trunk never sees the cooldowns: they use
their own copy of the data-stream RNG, so the trunk continues exactly as if they had not run.

A vq core (ADR 0023) assigns group indices every 64 steps and keeps those indices and
scales. Training forwards use partial-quantization probability 0.1. The cooldown artifact
is the quantized container of that held assignment. Scalar trunks do not take this path.

The trunk writes a checkpoint every 64 optimizer steps and again at each cooldown
boundary, before the fork. The checkpoint carries the trunk step count and the trunk
seconds counted so far. A resumed file that has no trunk seconds continues the weights
and leaves that account incomplete.
"""

from __future__ import annotations

import copy
import hashlib
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass

import numpy as np
import torch
import torch.nn.functional as F

from .model import QLinear, TinyGPT
from .vq import VectorCodec

# Optimization constants of the E0 protocol (ADR 0005, ADR 0008; S2 for the WSD fractions).
WARMUP_FRAC, COOLDOWN_FRAC = 0.02, 0.1
ADAMW_BETAS, ADAMW_EPS = (0.9, 0.95), 1e-8
GRAD_CLIP = 1.0
# ADR 0023 decision 7. Not TrainSpec fields: a scalar checkpoint's spec must stay exact.
ASSIGN_EVERY = 64
PARTIAL_PROB = 0.1
# Trunk snapshot interval. Not a TrainSpec field. The cooldown boundary is an extra snapshot.
CHECKPOINT_EVERY = 64


@dataclass(frozen=True)
class TrainSpec:
    tokens: int  # T: the first cooldown ends at T; later ones at 2T, 4T, ...
    branches: int = 3
    batch: int = 32
    lr: float = 3e-3
    wd: float = 0.1
    warmup_frac: float = WARMUP_FRAC  # of T (roadmap S2)
    cooldown_frac: float = COOLDOWN_FRAC  # of each branch's total steps (roadmap S2)
    seed: int = 0


@dataclass(frozen=True)
class QuantRamp:
    """Partial-quantization probability, linear from PARTIAL_PROB to 1 over [start, end).

    A diagnostic recipe, not ADR 0023 decision 7. The pilot driver does not set it, and it
    is not in a checkpoint, so a resume must set the same ramp again.
    """

    start: int
    end: int

    def __post_init__(self) -> None:
        if type(self.start) is not int or type(self.end) is not int:
            raise ValueError("quant ramp bounds must be ints")
        if not 0 <= self.start < self.end:
            raise ValueError("quant ramp needs 0 <= start < end")

    def at(self, step: int) -> float:
        done = min(max(step - self.start, 0) / (self.end - self.start), 1.0)
        return PARTIAL_PROB + (1.0 - PARTIAL_PROB) * done


def lr_at(step: int, warmup: int, peak: float, cd_start: int | None, cd_len: int) -> float:
    """Warmup-stable-decay: linear warmup, flat, linear to 0 over the cooldown."""
    if step < warmup:
        return peak * (step + 1) / warmup
    if cd_start is None or step < cd_start:
        return peak
    return peak * max(0.0, 1 - (step - cd_start + 1) / cd_len)


class DataStream:
    """Random ctx+1 windows from a byte array; its RNG state is the position in the stream."""

    def __init__(self, data: np.ndarray, batch: int, ctx: int, seed: int) -> None:
        if len(data) < ctx + 2:
            raise ValueError("training data shorter than one window")
        self.data, self.batch, self.ctx = data, batch, ctx
        self.rng = np.random.default_rng(seed)

    def offsets(self) -> np.ndarray:
        """Start offsets of the next batch of windows; advances the stream."""
        return self.rng.integers(0, len(self.data) - self.ctx - 1, size=self.batch)

    def next(self) -> tuple[torch.Tensor, torch.Tensor]:
        ix = self.offsets()
        c = np.stack([self.data[i : i + self.ctx + 1] for i in ix]).astype(np.int64)
        c = torch.from_numpy(c)
        return c[:, :-1], c[:, 1:]

    def plan(self, steps: int) -> np.ndarray:
        """Window offsets of the next `steps` batches, in order (the E0 index plan)."""
        return np.concatenate([self.offsets() for _ in range(steps)])

    def fork(self) -> DataStream:
        other = copy.copy(self)
        other.rng = copy.deepcopy(self.rng)
        return other

    def state(self) -> dict:
        return self.rng.bit_generator.state

    def set_state(self, state: dict) -> None:
        self.rng.bit_generator.state = state


def eval_windows(n: int, ctx: int, stride: int) -> list[tuple[int, int, int]]:
    """(start, length, first scored offset) so that every target index 1..n-1 is scored once.

    A window starting at j of length L predicts targets j+1 .. j+L-1. Full windows advance by
    `stride`; one last window is aligned to the end to cover the tail; data shorter than a
    window is a single window.
    """
    if n < 2:
        return []
    if n <= ctx + 1:
        return [(0, n, 0)]
    out, done = [], 0  # done = last scored target index
    j = 0
    while j + ctx + 1 <= n:
        out.append((j, ctx + 1, done - j))
        done = j + ctx
        j += stride
    if done < n - 1:
        j = n - ctx - 1
        out.append((j, ctx + 1, done - j))
    return out


@torch.no_grad()
def sliding_bpb(
    model: torch.nn.Module,
    data: np.ndarray,
    n_bytes: int,
    stride: int | None = None,
    batch: int = 32,
) -> tuple[float, int]:
    """Bits per byte over the targets of data[:n_bytes], each scored once (roadmap S7).

    Returns (bpb, number of scored target bytes). Every scored target after the first window has
    at least ctx - stride bytes of context.
    """
    ctx = model.cfg.ctx
    stride = stride or ctx // 2
    arr = torch.from_numpy(np.asarray(data[: min(n_bytes, len(data))]).astype(np.int64))
    wins = eval_windows(arr.numel(), ctx, stride)
    if not wins:
        raise ValueError("need at least 2 bytes to evaluate")
    was = model.training
    model.eval()
    total, count = 0.0, 0
    for i in range(0, len(wins), batch):
        group = wins[i : i + batch]
        length = group[0][1]
        c = torch.stack([arr[j : j + length] for j, _, _ in group])
        nll = F.cross_entropy(model(c[:, :-1]).transpose(1, 2), c[:, 1:], reduction="none")
        for r, (_, _, first) in enumerate(group):
            total += nll[r, first:].sum().item()
            count += nll.size(1) - first
    model.train(was)
    return total / count / np.log(2), count


def _optimizer(model: TinyGPT, spec: TrainSpec) -> torch.optim.Optimizer:
    # Matrices take the recipe's weight decay. Norms and a learned book do not.
    q = [m.weight for m in model.modules() if isinstance(m, QLinear)]
    ids = {id(p) for p in q}
    other = [p for p in model.parameters() if id(p) not in ids]
    return torch.optim.AdamW(
        [{"params": q, "weight_decay": spec.wd}, {"params": other, "weight_decay": 0.0}],
        lr=spec.lr,
        betas=ADAMW_BETAS,
        eps=ADAMW_EPS,
    )


@dataclass
class Trunk:
    """Everything needed to continue the trunk deterministically."""

    model: TinyGPT
    opt: torch.optim.Optimizer
    stream: DataStream
    step: int = 0

    def checkpoint(self, spec: TrainSpec, account: dict | None = None) -> dict:
        ckpt = {
            "model": copy.deepcopy(self.model.state_dict()),
            "opt": copy.deepcopy(self.opt.state_dict()),
            "step": self.step,
            "data_rng": copy.deepcopy(self.stream.state()),
            "torch_rng": torch.get_rng_state(),
            "spec": asdict(spec),
        }
        if self.model.cfg.core_fmt == "vq":
            ckpt["vq"] = vector_state(self.model)
        if account is not None:
            steps = account["trunk_steps"]
            seconds = account["trunk_seconds"]
            if type(steps) is not int or steps != self.step:
                raise ValueError("checkpoint trunk_steps do not match the step")
            if seconds is not None and (
                isinstance(seconds, bool)
                or not isinstance(seconds, (int, float))
                or seconds < 0
            ):
                raise ValueError("checkpoint trunk_seconds is not a duration")
            ckpt["trunk_steps"] = steps
            ckpt["trunk_seconds"] = None if seconds is None else float(seconds)
        return ckpt

    @classmethod
    def restore(cls, model: TinyGPT, data: np.ndarray, spec: TrainSpec, ckpt: dict) -> Trunk:
        if ckpt["spec"] != asdict(spec):
            raise ValueError("checkpoint was made with a different TrainSpec")
        model.load_state_dict(ckpt["model"])
        if model.cfg.core_fmt == "vq":
            if "vq" not in ckpt:
                raise ValueError("vq checkpoint is missing assignment state")
            load_vector_state(model, ckpt["vq"])
        elif "vq" in ckpt:
            raise ValueError("scalar checkpoint carries vector assignment state")
        opt = _optimizer(model, spec)
        opt.load_state_dict(ckpt["opt"])
        stream = DataStream(data, spec.batch, model.cfg.ctx, spec.seed)
        stream.set_state(ckpt["data_rng"])
        torch.set_rng_state(ckpt["torch_rng"])
        return cls(model, opt, stream, ckpt["step"])


def mask_seed(arm_seed: int, step: int, name: str) -> int:
    """Partial-quantization mask seed. It does not touch the global RNG."""
    digest = hashlib.sha256(f"{arm_seed}:{step}:{name}".encode()).digest()
    return int.from_bytes(digest[:8], "little") & ((1 << 63) - 1)


def _core_linears(model: TinyGPT) -> list[tuple[str, QLinear]]:
    return [
        (name, module)
        for name, module in model.named_modules()
        if isinstance(module, QLinear) and isinstance(module.codec, VectorCodec)
    ]


def _tie_book(model: TinyGPT) -> None:
    """Point every core codec at the module book. A fork must not grow a second one."""
    book = model.book
    if book is None:
        return
    for _, module in _core_linears(model):
        module.codec.book = book


def prepare_vector_step(model: TinyGPT, step: int, arm_seed: int) -> None:
    """Assign on the cadence, then hold indices and scales. Master weights stay put."""
    if model.cfg.core_fmt != "vq":
        return
    if type(step) is not int or step < 0 or type(arm_seed) is not int or arm_seed < 0:
        raise ValueError("vq step and arm seed must be non-negative ints")
    _tie_book(model)
    cores = _core_linears(model)
    if step % ASSIGN_EVERY == 0:
        used: set[int] = set()
        for _, module in cores:
            symbols, scale_bytes = module.codec.encode(module.weight.detach())
            stored = np.ascontiguousarray(symbols, dtype=np.int64)
            module.assignment = (stored, bytes(scale_bytes))
            used.update(int(i) for i in np.unique(stored).tolist())
        book = model.book
        assert book is not None
        dead = [i for i in range(book.levels) if i not in used]
        # A fixed book is the seed. Log the dead entry and do not rewrite it.
        for index in dead:
            model.reseed_log.append({"step": step, "index": index, "learned": book.learned})
        if dead and book.learned:
            book.reseed(dead)
        model.assigned_at = step
    elif model.assigned_at is None:
        raise ValueError("vq training step before the first assignment")
    for name, module in cores:
        if module.assignment is None:
            raise ValueError(f"vq core {name} has no assignment")
        module._partial_prob = (
            PARTIAL_PROB if model.quant_ramp is None else model.quant_ramp.at(step)
        )
        module._mask_seed = mask_seed(arm_seed, step, name)


def vector_state(model: TinyGPT) -> dict:
    """Indices, scales, book identity, and the PCG stream. Not the master weights."""
    if model.cfg.core_fmt != "vq" or model.book is None:
        raise ValueError("vector state requires a vq model")
    _tie_book(model)
    book = model.book
    if model.assigned_at is None:
        cores = None
    else:
        cores = {}
        for name, module in _core_linears(model):
            if module.assignment is None:
                raise ValueError(f"vq checkpoint missing assignment for {name}")
            symbols, scales = module.assignment
            cores[name] = {
                "symbols": np.array(symbols, dtype=np.int64, copy=True),
                "scales": bytes(scales),
            }
    return {
        "book": {
            "seed": book.seed,
            "learned": book.learned,
            "dimension": book.dimension,
            "bits": book.bits,
        },
        "stream": book.stream.state_dict(),
        "assigned_at": model.assigned_at,
        "reseed_log": [dict(row) for row in model.reseed_log],
        "cores": cores,
    }


def load_vector_state(model: TinyGPT, state: dict) -> None:
    """Restore a held assignment. This does not encode the master weights."""
    if model.cfg.core_fmt != "vq" or model.book is None:
        raise ValueError("vector state requires a vq model")
    _tie_book(model)
    book = model.book
    meta = state["book"]
    if (book.seed, book.learned, book.dimension, book.bits) != (
        meta["seed"],
        meta["learned"],
        meta["dimension"],
        meta["bits"],
    ):
        raise ValueError("checkpoint book does not match the model")
    book.stream.load_state_dict(state["stream"])
    model.assigned_at = state["assigned_at"]
    model.reseed_log = [dict(row) for row in state["reseed_log"]]
    cores = _core_linears(model)
    saved = state["cores"]
    if state["assigned_at"] is None:
        if saved:
            raise ValueError("vq checkpoint assignment does not match the step")
        for _, module in cores:
            module.assignment = None
        return
    if set(saved) != {name for name, _ in cores}:
        raise ValueError("checkpoint assignments do not match the core tensors")
    for name, module in cores:
        row = saved[name]
        module.assignment = (
            np.array(row["symbols"], dtype=np.int64, copy=True),
            bytes(row["scales"]),
        )


def _step(
    model: TinyGPT,
    opt: torch.optim.Optimizer,
    stream: DataStream,
    lr: float,
    *,
    step: int | None = None,
    seed: int = 0,
) -> float:
    if model.cfg.core_fmt == "vq":
        if step is None:
            raise ValueError("vq step is required")
        prepare_vector_step(model, step, seed)
    for g in opt.param_groups:
        g["lr"] = lr
    x, y = stream.next()
    loss = F.cross_entropy(model(x).flatten(0, 1), y.flatten())
    if not torch.isfinite(loss):
        raise FloatingPointError("non-finite training loss")
    opt.zero_grad(set_to_none=True)
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), GRAD_CLIP)
    opt.step()
    return loss.item()


def schedule(spec: TrainSpec, ctx: int) -> dict:
    """Step counts of the protocol, with tokens = steps * batch * ctx exactly."""
    per_step = spec.batch * ctx
    T = max(1, spec.tokens // per_step)
    ends = [T * 2**k for k in range(spec.branches)]
    cds = [max(1, int(spec.cooldown_frac * e)) for e in ends]
    return {
        "per_step": per_step,
        "T": T,
        "warmup": max(1, int(spec.warmup_frac * T)),
        "ends": ends,
        "cooldowns": cds,
        "trunk_steps": ends[-1] - cds[-1],
    }


def _opened_account(resume: dict | None) -> tuple[dict, bool]:
    """Trunk account carried by a checkpoint. Missing seconds are not invented."""
    acct: dict = {"trunk_steps": 0, "cooldowns": [], "trunk_seconds": 0.0}
    if resume is None:
        return acct, True
    step = resume["step"]
    if type(step) is not int or step < 0:
        raise ValueError("checkpoint step is not a trunk step")
    stored = resume.get("trunk_steps")
    if stored is not None and stored != step:
        raise ValueError("checkpoint trunk_steps do not match the step")
    seconds = resume.get("trunk_seconds")
    if "trunk_seconds" not in resume or seconds is None:
        acct["trunk_steps"] = step
        acct["trunk_seconds"] = None
        return acct, False
    if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or seconds < 0:
        raise ValueError("checkpoint trunk_seconds is not a duration")
    acct["trunk_steps"] = step
    acct["trunk_seconds"] = float(seconds)
    return acct, True


def train_wsd(
    model: TinyGPT,
    data: np.ndarray,
    spec: TrainSpec,
    on_branch: Callable[[int, TinyGPT, dict], None],
    on_checkpoint: Callable[[dict], None] | None = None,
    resume: dict | None = None,
    log: Callable[[str], None] = print,
    skip_cooldown: Callable[[int], bool] | None = None,
) -> dict:
    """Run the trunk; at each branch point fork, cool down, report, discard the fork.

    Writes a trunk checkpoint every CHECKPOINT_EVERY steps and at each cooldown
    boundary. skip_cooldown, when true, does not run that cooldown. A resumed
    checkpoint with no trunk seconds returns trunk_seconds as None.

    Returns compute accounting: trunk and per-cooldown steps/tokens and wall seconds.
    """
    sch = schedule(spec, model.cfg.ctx)
    if resume is None:
        trunk = Trunk(
            model, _optimizer(model, spec), DataStream(data, spec.batch, model.cfg.ctx, spec.seed)
        )
    else:
        trunk = Trunk.restore(model, data, spec, resume)
    acct, complete = _opened_account(resume)

    def take(target: TinyGPT, opt: torch.optim.Optimizer, stream: DataStream, lr: float, step: int):
        before = len(getattr(target, "reseed_log", ()))
        _step(target, opt, stream, lr, step=step, seed=spec.seed)
        fresh = len(getattr(target, "reseed_log", ())) - before
        if fresh:
            log(f"dead code step={step} entries={fresh}")

    def emit(t0: float) -> float:
        now = time.time()
        if complete:
            acct["trunk_seconds"] += now - t0
        if on_checkpoint is not None:
            on_checkpoint(trunk.checkpoint(spec, acct))
        return now

    for end, cd_len in zip(sch["ends"], sch["cooldowns"], strict=True):
        cd_start = end - cd_len
        if trunk.step > cd_start:
            continue  # resumed past this branch point
        already = trunk.step == cd_start
        t0 = time.time()
        while trunk.step < cd_start:
            take(
                trunk.model,
                trunk.opt,
                trunk.stream,
                lr_at(trunk.step, sch["warmup"], spec.lr, None, 0),
                trunk.step,
            )
            trunk.step += 1
            acct["trunk_steps"] += 1
            if trunk.step < cd_start and trunk.step % CHECKPOINT_EVERY == 0:
                t0 = emit(t0)
        if not already:
            emit(t0)
        if skip_cooldown is not None and skip_cooldown(end):
            continue
        branch = copy.deepcopy(trunk.model)
        _tie_book(branch)
        bopt = _optimizer(branch, spec)
        bopt.load_state_dict(copy.deepcopy(trunk.opt.state_dict()))
        bstream = trunk.stream.fork()
        t0 = time.time()
        for s in range(cd_start, end):
            take(branch, bopt, bstream, lr_at(s, sch["warmup"], spec.lr, cd_start, cd_len), s)
        info = {
            "end_step": end,
            "cooldown_steps": cd_len,
            "cooldown_start": cd_start,
            "tokens_seen": end * sch["per_step"],
            "cooldown_seconds": time.time() - t0,
        }
        acct["cooldowns"].append(info)
        log(f"branch end={end} tokens={end * sch['per_step']:,}")
        on_branch(end, branch, info)
        del branch, bopt, bstream
    acct["trunk_tokens"] = acct["trunk_steps"] * sch["per_step"]
    return acct
