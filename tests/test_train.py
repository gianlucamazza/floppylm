import copy
import math

import numpy as np
import pytest
import torch

from floppylm.model import GPTConfig, QLinear, TinyGPT
from floppylm.pack import pack, pack_sections, unpack
from floppylm.train import (
    ASSIGN_EVERY,
    CHECKPOINT_EVERY,
    PARTIAL_PROB,
    DataStream,
    TrainSpec,
    Trunk,
    _optimizer,
    _step,
    _tie_book,
    eval_windows,
    lr_at,
    mask_seed,
    prepare_vector_step,
    schedule,
    sliding_bpb,
    train_wsd,
)
from floppylm.vq import VectorBook, pcg32

DATA = np.frombuffer(b"the cat sat on the mat. " * 800, dtype=np.uint8)
CFG = GPTConfig(d=32, n_layers=1, n_heads=2, d_ff=48, ctx=32)
SPEC = TrainSpec(tokens=8 * 32 * 12, branches=3, batch=8, lr=3e-3, seed=0)


def test_wsd_schedule_boundaries() -> None:
    assert lr_at(0, 10, 1.0, None, 0) == 0.1
    assert lr_at(9, 10, 1.0, None, 0) == 1.0
    assert lr_at(500, 10, 1.0, None, 0) == 1.0
    assert lr_at(99, 10, 1.0, 100, 10) == 1.0
    assert lr_at(100, 10, 1.0, 100, 10) == 0.9
    assert lr_at(109, 10, 1.0, 100, 10) == 0.0


def test_schedule_counts() -> None:
    s = schedule(SPEC, 32)
    assert s["ends"] == [12, 24, 48] and s["cooldowns"] == [1, 2, 4]
    assert s["trunk_steps"] == 44


# -- sliding evaluation against an independent oracle ------------------------------------------


class FixedDist(torch.nn.Module):
    """Context-free model: the same next-byte distribution q everywhere."""

    def __init__(self, ctx: int, q: torch.Tensor) -> None:
        super().__init__()
        self.cfg = GPTConfig(ctx=ctx)
        self.logq = q.log()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.logq.expand(*x.shape, 256)


@pytest.mark.parametrize(
    ("n", "ctx", "stride"),
    [(5000, 64, 32), (40, 64, 32), (65, 64, 32), (66, 64, 32), (2, 8, 4), (1000, 16, 16)],
)
def test_sliding_eval_scores_every_target_once(n: int, ctx: int, stride: int) -> None:
    rng = np.random.default_rng(n)
    data = rng.integers(0, 256, n).astype(np.uint8)
    q = torch.from_numpy(rng.dirichlet(np.ones(256))).float()
    got, count = sliding_bpb(FixedDist(ctx, q), data, n, stride=stride, batch=7)
    oracle = float(-torch.log2(q[torch.from_numpy(data[1:].astype(np.int64))]).mean())
    assert count == n - 1
    assert math.isclose(got, oracle, rel_tol=1e-5)


def test_eval_windows_cover_targets_exactly_once() -> None:
    for n, ctx, stride in [(5000, 64, 32), (97, 16, 5), (17, 16, 8), (18, 16, 8)]:
        seen = []
        for j, length, first in eval_windows(n, ctx, stride):
            seen += list(range(j + 1 + first, j + length))
        assert sorted(seen) == list(range(1, n))


def test_sliding_eval_rejects_empty() -> None:
    with pytest.raises(ValueError):
        sliding_bpb(FixedDist(8, torch.full((256,), 1 / 256)), np.zeros(1, np.uint8), 1)


# -- WSD: trunk isolation and deterministic resume ----------------------------------------------


def _state_equal(a: dict, b: dict) -> bool:
    return all(torch.equal(a[k], b[k]) for k in a)


def test_cooldowns_do_not_touch_the_trunk() -> None:
    torch.manual_seed(0)
    m = TinyGPT(CFG)
    ckpts = []
    train_wsd(m, DATA, SPEC, lambda *a: None, on_checkpoint=ckpts.append, log=lambda s: None)
    # Reference: the same trunk with no cooldowns at all.
    torch.manual_seed(0)
    ref = TinyGPT(CFG)
    trunk = Trunk(ref, _optimizer(ref, SPEC), DataStream(DATA, SPEC.batch, CFG.ctx, SPEC.seed))
    sch = schedule(SPEC, CFG.ctx)
    for ckpt in ckpts:
        while trunk.step < ckpt["step"]:
            _step(
                trunk.model,
                trunk.opt,
                trunk.stream,
                lr_at(trunk.step, sch["warmup"], SPEC.lr, None, 0),
            )
            trunk.step += 1
        assert "vq" not in ckpt
        assert _state_equal(ckpt["model"], ref.state_dict())
        assert ckpt["data_rng"] == trunk.stream.state()


def test_resume_from_trunk_checkpoint_is_deterministic() -> None:
    def run(resume=None, stop_after=None):
        torch.manual_seed(0)
        m = TinyGPT(CFG)
        out, ckpts = [], []
        train_wsd(
            m,
            DATA,
            SPEC,
            lambda e, b, i: out.append((e, b.state_dict())),
            on_checkpoint=ckpts.append,
            resume=resume,
            log=lambda s: None,
        )
        return out, ckpts

    full, ckpts = run()
    resumed, _ = run(resume=ckpts[1])
    assert [e for e, _ in resumed] == [e for e, _ in full[1:]]
    for (_, a), (_, b) in zip(resumed, full[1:], strict=True):
        assert _state_equal(a, b)


def test_periodic_checkpoint_resumes_the_same_trunk_and_keeps_the_account() -> None:
    torch.manual_seed(0)
    torch.set_num_threads(1)
    spec = TrainSpec(tokens=80 * 4 * CFG.ctx, branches=1, batch=4, lr=3e-3, seed=1)

    def run(resume=None):
        torch.manual_seed(0)
        model = TinyGPT(CFG)
        out, ckpts = [], []
        acct = train_wsd(
            model,
            DATA,
            spec,
            lambda e, b, _i: out.append((e, b.state_dict())),
            on_checkpoint=ckpts.append,
            resume=resume,
            log=lambda _s: None,
        )
        return out, ckpts, acct

    full, ckpts, full_acct = run()
    sch = schedule(spec, CFG.ctx)
    cd_start = sch["ends"][0] - sch["cooldowns"][0]
    assert [ckpt["step"] for ckpt in ckpts] == [CHECKPOINT_EVERY, cd_start]
    mid = ckpts[0]
    assert mid["step"] == CHECKPOINT_EVERY
    assert mid["trunk_steps"] == CHECKPOINT_EVERY
    assert isinstance(mid["trunk_seconds"], float) and mid["trunk_seconds"] >= 0
    resumed, _, resumed_acct = run(resume=mid)
    assert _state_equal(resumed[0][1], full[0][1])
    assert resumed_acct["trunk_steps"] == full_acct["trunk_steps"] == cd_start
    carried = copy.deepcopy(mid)
    carried["trunk_seconds"] = 1000.0
    _, _, carried_acct = run(resume=carried)
    assert 1000.0 <= carried_acct["trunk_seconds"] < 1500.0
    bare = copy.deepcopy(mid)
    del bare["trunk_steps"]
    del bare["trunk_seconds"]
    _, _, bare_acct = run(resume=bare)
    assert bare_acct["trunk_seconds"] is None
    assert bare_acct["trunk_steps"] == cd_start


def test_train_wsd_branches_improve() -> None:
    torch.manual_seed(0)
    m = TinyGPT(CFG)
    got = []
    acct = train_wsd(
        m, DATA, SPEC, lambda e, b, i: got.append(sliding_bpb(b, DATA, 4000)[0]), log=lambda s: None
    )
    assert len(got) == 3 and got[-1] < got[0] < 8.0
    assert acct["trunk_steps"] == 44 and [c["cooldown_steps"] for c in acct["cooldowns"]] == [
        1,
        2,
        4,
    ]


# -- ADR 0023 vector assignment on the host trainer --------------------------------------------


VQ_CFG = GPTConfig(
    vocab=256,
    d=32,
    n_layers=1,
    n_heads=2,
    d_ff=20,
    ctx=16,
    core_fmt="vq",
    emb_fmt="4bit",
    scale_policy="row8log",
)


def _vq(learned: bool, seed: int = 5) -> TinyGPT:
    torch.manual_seed(0)
    return TinyGPT(VQ_CFG, VectorBook(8, 0.5, seed, learned=learned))


def _zero_core(model: TinyGPT) -> None:
    with torch.no_grad():
        for module in model.modules():
            if isinstance(module, QLinear) and module is not model.emb:
                module.weight.zero_()


def _opt_equal(a: torch.optim.Optimizer, b: torch.optim.Optimizer) -> bool:
    left, right = a.state_dict(), b.state_dict()
    same_groups = left["param_groups"] == right["param_groups"]
    if not same_groups or left["state"].keys() != right["state"].keys():
        return False
    for key, row in left["state"].items():
        other = right["state"][key]
        if row.keys() != other.keys():
            return False
        for name, value in row.items():
            other_value = other[name]
            if torch.is_tensor(value):
                if not torch.equal(value, other_value):
                    return False
            elif value != other_value:
                return False
    return True


def _entry_rows(seed: int, skip: int, take: int, dimension: int) -> torch.Tensor:
    draws = pcg32(seed, (skip + take) * dimension * 12)
    draws = draws[skip * dimension * 12 :].astype(np.uint64) & 0xFFFF
    summed = draws.reshape(take, dimension, 12).sum(-1).astype(np.int64)
    values = ((summed - 393210) / 65536).astype(np.float32)
    return torch.from_numpy(np.ascontiguousarray(values)).half().float()


def test_vector_recipe_is_not_a_train_spec_field() -> None:
    assert set(TrainSpec.__dataclass_fields__) == {
        "tokens",
        "branches",
        "batch",
        "lr",
        "wd",
        "warmup_frac",
        "cooldown_frac",
        "seed",
    }
    assert ASSIGN_EVERY == 64 and PARTIAL_PROB == 0.1


def test_learned_book_is_not_a_decayed_matrix() -> None:
    learned = _vq(True)
    fixed = _vq(False)
    spec = TrainSpec(tokens=1)
    opt = _optimizer(learned, spec)
    decayed = {id(p) for p in opt.param_groups[0]["params"]}
    rest = {id(p) for p in opt.param_groups[1]["params"]}
    assert id(learned.book.values) not in decayed
    assert id(learned.book.values) in rest
    assert opt.param_groups[1]["weight_decay"] == 0.0
    fixed_decay = {id(p) for p in _optimizer(fixed, spec).param_groups[0]["params"]}
    assert id(fixed.book.values) not in fixed_decay
    assert fixed.book.values.requires_grad is False


def test_vq_assignment_holds_for_64_steps() -> None:
    model = _vq(True)
    spec = TrainSpec(tokens=VQ_CFG.ctx, batch=2, seed=1)
    opt = _optimizer(model, spec)
    stream = DataStream(DATA, spec.batch, VQ_CFG.ctx, spec.seed)
    _step(model, opt, stream, spec.lr, step=0, seed=spec.seed)
    held = model.blocks[0].qkv.assignment
    assert held is not None and model.assigned_at == 0
    assert model.emb.assignment is None
    for step in range(1, ASSIGN_EVERY):
        _step(model, opt, stream, spec.lr, step=step, seed=spec.seed)
        assert model.blocks[0].qkv.assignment[0] is held[0]
        assert model.assigned_at == 0
    _step(model, opt, stream, spec.lr, step=ASSIGN_EVERY, seed=spec.seed)
    assert model.assigned_at == ASSIGN_EVERY
    assert model.blocks[0].qkv.assignment[0] is not held[0]
    qkv = model.blocks[0].qkv
    symbols, scales = qkv.assignment
    expect = qkv.codec.partial_weight(
        qkv.weight,
        PARTIAL_PROB,
        mask_seed(spec.seed, ASSIGN_EVERY, "blocks.0.qkv"),
        symbols=symbols,
        scale_bytes=scales,
    )
    assert torch.equal(qkv.qweight(), expect)
    model.eval()
    full = qkv.codec.partial_weight(qkv.weight, 1.0, 0, symbols=symbols, scale_bytes=scales)
    assert torch.equal(qkv.qweight(), full)


def test_eval_keeps_held_scales_when_the_master_moves() -> None:
    model = _vq(True)
    prepare_vector_step(model, 0, 1)
    qkv = model.blocks[0].qkv
    symbols, scales = qkv.assignment
    with torch.no_grad():
        qkv.weight.mul_(3)
    model.eval()
    held = qkv.codec.partial_weight(qkv.weight, 1.0, 0, symbols=symbols, scale_bytes=scales)
    assert torch.equal(qkv.qweight(), held)
    assert not torch.equal(held, qkv.codec.weight(qkv.weight))


def test_dead_learned_entry_is_reseeded_and_a_fixed_book_is_not() -> None:
    learned = _vq(True, seed=11)
    _zero_core(learned)
    before = learned.book.values.detach().clone()
    prepare_vector_step(learned, 0, 1)
    dead = [row["index"] for row in learned.reseed_log]
    assert learned.reseed_log == [{"step": 0, "index": index, "learned": True} for index in dead]
    assert dead == sorted(dead) and len(dead) == learned.book.levels - 1
    assert learned.book.values.shape == before.shape
    used = set(range(learned.book.levels)) - set(dead)
    assert len(used) == 1
    kept = next(iter(used))
    assert torch.equal(learned.book.values[kept], before[kept])
    expect = _entry_rows(11, learned.book.levels, len(dead), learned.book.dimension)
    for row, index in zip(expect, dead, strict=True):
        assert torch.equal(learned.book.values[index], row)
    drawn = learned.book.levels * learned.book.dimension * 12
    assert learned.book.stream.drawn == drawn + len(dead) * learned.book.dimension * 12
    first = learned.book.values[dead[0]].detach().clone()
    prepare_vector_step(learned, 1, 1)
    assert learned.book.stream.drawn == drawn + len(dead) * learned.book.dimension * 12
    assert learned.assigned_at == 0
    prepare_vector_step(learned, ASSIGN_EVERY, 1)
    assert learned.book.values.shape[0] == learned.book.levels
    assert learned.assigned_at == ASSIGN_EVERY
    assert any(row["step"] == ASSIGN_EVERY for row in learned.reseed_log)
    if any(row["index"] == dead[0] and row["step"] == ASSIGN_EVERY for row in learned.reseed_log):
        assert not torch.equal(learned.book.values[dead[0]], first)

    fixed = _vq(False, seed=11)
    _zero_core(fixed)
    original = fixed.book.values.detach().clone()
    prepare_vector_step(fixed, 0, 1)
    assert len(fixed.book.to_bytes()) == 16
    assert torch.equal(fixed.book.values, original)
    assert fixed.book.stream.drawn == drawn
    assert [row["index"] for row in fixed.reseed_log] == dead
    assert all(row["learned"] is False for row in fixed.reseed_log)
    blob, parts = pack_sections(fixed)
    assert parts["shared"] == 16
    assert pack(unpack(blob)) == blob


def test_vq_resume_continues_the_held_assignment() -> None:
    spec = TrainSpec(tokens=80 * 4 * VQ_CFG.ctx, branches=1, batch=4, seed=2)

    def march(model, opt, stream, start: int, end: int) -> None:
        for step in range(start, end):
            _step(model, opt, stream, spec.lr, step=step, seed=spec.seed)

    model = _vq(True, seed=9)
    opt = _optimizer(model, spec)
    stream = DataStream(DATA, spec.batch, VQ_CFG.ctx, spec.seed)
    march(model, opt, stream, 0, 70)
    fork = copy.deepcopy(model)
    _tie_book(fork)
    assert fork.book is fork.blocks[0].qkv.codec.book
    assert fork.book is not model.book
    ckpt = Trunk(model, opt, stream, 70).checkpoint(spec)
    assert ckpt["vq"]["assigned_at"] == ASSIGN_EVERY
    fresh = model.blocks[0].qkv.codec.encode(model.blocks[0].qkv.weight.detach())[0]
    assert not np.array_equal(ckpt["vq"]["cores"]["blocks.0.qkv"]["symbols"], fresh)

    other = _vq(True, seed=9)
    restored = Trunk.restore(other, DATA, spec, ckpt)
    assert other.assigned_at == ASSIGN_EVERY
    assert np.array_equal(other.blocks[0].qkv.assignment[0], model.blocks[0].qkv.assignment[0])
    assert other.blocks[0].qkv.assignment[1] == model.blocks[0].qkv.assignment[1]
    assert other.book.stream.state_dict() == model.book.stream.state_dict()
    assert other.reseed_log == model.reseed_log
    march(model, opt, stream, 70, 80)
    march(other, restored.opt, restored.stream, 70, 80)
    assert _state_equal(model.state_dict(), other.state_dict())
    assert _opt_equal(opt, restored.opt)
    assert np.array_equal(model.blocks[0].qkv.assignment[0], other.blocks[0].qkv.assignment[0])
    assert model.reseed_log == other.reseed_log
    assert model.book.stream.state_dict() == other.book.stream.state_dict()
    assert model.assigned_at == other.assigned_at == ASSIGN_EVERY


def test_cooldown_artifact_is_the_held_quantized_container() -> None:
    spec = TrainSpec(tokens=80 * 4 * VQ_CFG.ctx, branches=1, batch=4, seed=3)
    model = _vq(True, seed=4)
    saved: dict = {}
    ckpts: list = []

    def on_branch(end: int, branch: TinyGPT, info: dict) -> None:
        assert branch.book is branch.blocks[0].qkv.codec.book
        qkv = branch.blocks[0].qkv
        recon = qkv.codec.decode(qkv.assignment[0], qkv.assignment[1], tuple(qkv.weight.shape))
        assert not torch.equal(qkv.weight.detach(), recon)
        blob, parts = pack_sections(branch)
        assert parts["shared"] == len(branch.book.to_bytes())
        assert pack(unpack(blob)) == blob
        x = torch.randint(0, VQ_CFG.vocab, (2, 8))
        branch.eval()
        assert torch.equal(branch(x), unpack(blob)(x))
        saved["end"] = end
        saved["state"] = copy.deepcopy(branch.state_dict())
        saved["symbols"] = qkv.assignment[0].copy()
        saved["log"] = list(branch.reseed_log)

    train_wsd(model, DATA, spec, on_branch, on_checkpoint=ckpts.append, log=lambda _s: None)
    sch = schedule(spec, VQ_CFG.ctx)
    cd_start = sch["ends"][0] - sch["cooldowns"][0]
    expected = list(range(CHECKPOINT_EVERY, cd_start, CHECKPOINT_EVERY))
    expected.append(cd_start)
    assert saved["end"] == sch["ends"][0]
    assert [ckpt["step"] for ckpt in ckpts] == expected and "vq" in ckpts[-1]
    assert ckpts[-1]["trunk_steps"] == cd_start

    resumed: dict = {}

    def on_resume(end: int, branch: TinyGPT, info: dict) -> None:
        resumed["state"] = branch.state_dict()
        resumed["symbols"] = branch.blocks[0].qkv.assignment[0].copy()
        resumed["log"] = list(branch.reseed_log)

    train_wsd(
        _vq(True, seed=4),
        DATA,
        spec,
        on_resume,
        resume=ckpts[-1],
        log=lambda _s: None,
    )
    assert _state_equal(resumed["state"], saved["state"])
    assert np.array_equal(resumed["symbols"], saved["symbols"])
    assert resumed["log"] == saved["log"]


def test_pack_uses_the_held_symbols() -> None:
    model = _vq(True, seed=6)
    prepare_vector_step(model, 0, 1)
    qkv = model.blocks[0].qkv
    _symbols, scales = qkv.assignment
    forced = np.zeros_like(_symbols)
    qkv.assignment = (forced, scales)
    blob, parts = pack_sections(model)
    assert parts["shared"] == len(model.book.to_bytes())
    back = unpack(blob)
    expect = qkv.codec.decode(forced, scales, tuple(qkv.weight.shape))
    assert torch.equal(back.blocks[0].qkv.weight, expect)
    assert pack(back) == blob
