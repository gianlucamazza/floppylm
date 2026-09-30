import math

import numpy as np
import pytest
import torch

from floppylm.model import GPTConfig, TinyGPT
from floppylm.train import (
    DataStream,
    TrainSpec,
    Trunk,
    _optimizer,
    _step,
    eval_windows,
    lr_at,
    schedule,
    sliding_bpb,
    train_wsd,
)

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
