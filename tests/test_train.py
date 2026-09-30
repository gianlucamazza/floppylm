import math

import numpy as np
import torch

from floppylm.model import GPTConfig, TinyGPT
from floppylm.train import TrainSpec, lr_at, sliding_bpb, train_wsd


def test_wsd_schedule_boundaries() -> None:
    assert lr_at(0, 10, 1.0, None, 0) == 0.1
    assert lr_at(9, 10, 1.0, None, 0) == 1.0
    assert lr_at(500, 10, 1.0, None, 0) == 1.0
    assert lr_at(100, 10, 1.0, 100, 10) == 0.9
    assert lr_at(109, 10, 1.0, 100, 10) == 0.0


class Uniform(torch.nn.Module):
    def __init__(self, ctx: int) -> None:
        super().__init__()
        self.cfg = GPTConfig(ctx=ctx)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return torch.zeros(*x.shape, 256)


def test_sliding_eval_uniform_and_coverage() -> None:
    data = np.random.default_rng(0).integers(0, 256, 5000).astype(np.uint8)
    bpb, n = sliding_bpb(Uniform(64), data, 5000, stride=32)
    assert math.isclose(bpb, 8.0, rel_tol=1e-6)
    starts = len(range(0, 5000 - 64, 32))
    assert n == 64 + (starts - 1) * 32


def test_train_wsd_branches_improve_on_repetitive_data() -> None:
    torch.manual_seed(0)
    data = np.frombuffer(b"abcabcabd" * 4000, dtype=np.uint8)
    m = TinyGPT(GPTConfig(d=32, n_layers=1, n_heads=2, d_ff=64, ctx=32))
    got = []
    spec = TrainSpec(tokens=32 * 8 * 40, branches=2, batch=8, lr=3e-3, seed=0)
    train_wsd(
        m,
        data,
        spec,
        lambda end, b, info: got.append(sliding_bpb(b, data, 4000)[0]),
        log=lambda s: None,
    )
    assert len(got) == 2 and got[1] < got[0] < 8.0
