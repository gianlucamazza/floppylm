import math

import torch

from floppylm.metrics import bpb


def test_uniform_model_is_8_bits_per_byte() -> None:
    logits = torch.zeros(3, 10, 256)
    y = torch.randint(0, 256, (3, 10))
    assert math.isclose(bpb(logits, y), 8.0, rel_tol=1e-6)


def test_perfect_model_is_zero() -> None:
    y = torch.randint(0, 256, (2, 5))
    logits = torch.full((2, 5, 256), -1e4).scatter(-1, y.unsqueeze(-1), 1e4)
    assert bpb(logits, y) < 1e-6
