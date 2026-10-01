"""Independent PyTorch/autograd oracle for each native E0 tensor operation."""

from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path

import torch
import torch.nn.functional as F

from floppylm import runlog

from .jobs import compare


def fixtures(seed: int = 41) -> tuple[dict, dict]:
    generator = torch.Generator().manual_seed(seed)
    cases, expected = [], []

    def random(*shape):
        return torch.randn(shape, generator=generator, dtype=torch.float32)

    def add(name, op, inputs, function, parameters=None, gradients=None):
        parameters = parameters or {}
        gradients = gradients if gradients is not None else list(range(len(inputs)))
        values = [x.detach().clone().requires_grad_(i in gradients) for i, x in enumerate(inputs)]
        output = function(*values)
        upstream = random(*output.shape)
        derivative = torch.autograd.grad(
            output, [values[i] for i in gradients], grad_outputs=upstream
        )
        buffers = [x.detach().flatten().tolist() for x in values]
        buffers += [[]] * (3 - len(buffers))
        buffers += [output.detach().flatten().tolist(), upstream.flatten().tolist()]
        for mode, result in [
            (0, output),
            *[(i + 1, g) for i, g in zip(gradients, derivative, strict=True)],
        ]:
            case_id = f"{name}:{mode}"
            cases.append(
                {
                    "id": case_id,
                    "command": {"op": op, "mode": mode, "count": result.numel(), **parameters},
                    "inputs": buffers,
                }
            )
            expected.append(
                {
                    "id": case_id,
                    "shape": list(result.shape),
                    "values": result.detach().flatten().tolist(),
                }
            )

    add("add", 0, [random(7, 9), random(7, 9)], lambda x, w: x + w)
    add("multiply", 9, [random(7, 9), random(7, 9)], lambda x, w: x * w)
    for rows, cols, out in [(7, 11, 13), (17, 96, 391)]:
        add(
            f"linear-{rows}-{cols}-{out}",
            1,
            [random(rows, cols), random(out, cols)],
            lambda x, w: F.linear(x, w),
            {"rows": rows, "cols": cols, "out": out},
        )
    for magnitude in (1.0, 1e-5):
        x = random(7, 9) * magnitude
        x[0] = 0
        epsilon = torch.finfo(torch.float32).eps
        add(
            f"rmsnorm-{magnitude}",
            2,
            [x, random(9)],
            lambda x, w: x * torch.rsqrt(x.square().mean(-1, keepdim=True) + epsilon) * w,
            {"rows": 7, "cols": 9, "epsilon": epsilon},
        )
    batch, heads, seq, head_dim = 2, 3, 5, 8
    width = heads * head_dim

    def rope(x):
        angle = torch.arange(seq, dtype=torch.float32)[:, None] * torch.pow(
            10000.0, -torch.arange(0, head_dim, 2, dtype=torch.float32) / head_dim
        )
        even, odd = x[..., 0::2], x[..., 1::2]
        return torch.stack(
            (even * angle.cos() - odd * angle.sin(), odd * angle.cos() + even * angle.sin()), -1
        ).flatten(-2)

    add("rope", 3, [random(batch * heads, seq, head_dim)], rope, {"cols": head_dim, "seq": seq})
    for aux, function in enumerate((F.gelu, lambda x: F.relu(x).square(), F.silu)):
        x = torch.cat((torch.linspace(-12, 12, 97), torch.tensor([-1e-7, 0.0, 1e-7])))
        add(f"activation-{aux}", 4, [x], function, {"aux": aux})
    for part in range(3):
        add(
            f"heads-{part}",
            5,
            [random(batch, seq, 3 * width)],
            lambda x, part=part: (
                x.reshape(batch, seq, 3, heads, head_dim)[:, :, part]
                .permute(0, 2, 1, 3)
                .contiguous()
            ),
            {"batch": batch, "seq": seq, "heads": heads, "cols": width, "aux": part},
        )
    add(
        "unheads",
        6,
        [random(batch, heads, seq, head_dim)],
        lambda x: x.permute(0, 2, 1, 3).contiguous().reshape(batch, seq, width),
        {"batch": batch, "seq": seq, "heads": heads, "cols": width},
    )
    tokens = torch.tensor([0, 2, 2, 4, 0, 7, 4], dtype=torch.float32)
    add(
        "embedding-repeat",
        7,
        [tokens, random(9, 5)],
        lambda x, w: F.embedding(x.long(), w),
        {"rows": 7, "cols": 5},
        gradients=[1],
    )
    for part in range(2):
        add(
            f"slice-{part}",
            8,
            [random(7, 22)],
            lambda x, part=part: x[:, part * 11 : (part + 1) * 11],
            {"rows": 7, "cols": 22, "out": 11, "aux": part},
        )
    groups, rows = batch * heads, batch * heads * seq
    add(
        "attention-scores",
        11,
        [random(groups, seq, head_dim), random(groups, seq, head_dim)],
        lambda x, w: x @ w.transpose(-1, -2) / math.sqrt(head_dim),
        {"rows": rows, "cols": head_dim, "seq": seq},
    )
    mask = torch.ones(seq, seq, dtype=torch.bool).triu(1)
    add(
        "causal-softmax",
        12,
        [random(groups, seq, seq)],
        lambda x: x.masked_fill(mask, float("-inf")).softmax(-1),
        {"rows": rows, "cols": seq, "seq": seq},
    )
    add(
        "causal-weighted",
        13,
        [random(groups, seq, seq), random(groups, seq, head_dim)],
        lambda x, w: x.masked_fill(mask, 0) @ w,
        {"rows": rows, "cols": head_dim, "seq": seq},
    )
    labels = torch.randint(11, (7,), generator=generator).float()
    add(
        "cross-entropy",
        10,
        [random(7, 11), labels],
        lambda x, w: F.cross_entropy(x, w.long(), reduction="none"),
        {"rows": 7, "cols": 11},
        gradients=[0],
    )
    shifted = torch.tensor([[1000.0, 994.0], [10000.0, 9994.0], [-1000.0, -1006.0]])
    add(
        "cross-entropy-shift",
        10,
        [shifted, torch.zeros(3)],
        lambda x, w: F.cross_entropy(x, w.long(), reduction="none"),
        {"rows": 3, "cols": 2},
        gradients=[0],
    )
    return {"schema": "floppylm.e0.kernels.v1", "seed": seed, "cases": cases}, {
        "oracle": "independent PyTorch operations and autograd",
        "seed": seed,
        "cases": expected,
    }


def verify(directory: Path, *, binary: Path | None = None, executor=None, hardware=True) -> dict:
    directory.mkdir(parents=True, exist_ok=False)
    initial, expected = fixtures()
    runlog.write_json(directory / "fixture.json", initial)
    runlog.write_json(directory / "expected.json", expected)
    if executor is not None:
        actual = executor(initial)
        runlog.write_json(directory / "actual.json", actual)
    else:
        subprocess.run(
            [
                str(binary.resolve()),
                "--kernel-fixture",
                str(directory / "fixture.json"),
                "--out",
                str(directory / "actual.json"),
                "--reference",
            ],
            check=True,
        )
        actual = json.loads((directory / "actual.json").read_text())
    actual_ids = [c["id"] for c in actual["cases"]]
    expected_ids = [c["id"] for c in expected["cases"]]
    gates = {"coverage": {"ok": actual_ids == expected_ids}}
    if actual_ids == expected_ids:
        for a, b in zip(actual["cases"], expected["cases"], strict=True):
            gates[b["id"]] = compare(a["values"], b["values"])
            if hardware:
                gates[b["id"]]["ok"] &= a["dispatches"] > 0
    if hardware:
        gates["hardware"] = {"ok": actual["hardware_gpu"] and actual["dispatches"] > 0}
    report = {
        "purpose": "functional",
        "hardware_gpu": actual["hardware_gpu"],
        "oracle": expected["oracle"],
        "case_count": len(expected_ids),
        "gates": gates,
        "ok": all(g["ok"] for g in gates.values()),
    }
    runlog.write_json(directory / "parity.json", report)
    return report
