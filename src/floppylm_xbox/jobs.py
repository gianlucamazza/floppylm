"""Portable E0 jobs and independent numerical gates for xbox-gpu-training.

Python owns initialization, sample indices, canonical FLP2 and evaluation. The native
backend receives train data only. A reference result cannot certify GPU acceptance.
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import asdict
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

from floppylm import runlog
from floppylm.codec import scalar
from floppylm.model import GPTConfig, QLinear, TinyGPT
from floppylm.seed import seed_all
from floppylm.train import DataStream, TrainSpec, _optimizer, schedule

ABS_GATE, REL_GATE, REL_FLOOR = 1e-5, 1e-4, 1e-2


def tensors(model: TinyGPT) -> list[dict]:
    names = {id(p): name for name, p in model.named_parameters()}
    result = []
    for tensor in model.stored_tensors():
        weight = tensor.weight.detach().float().cpu()
        result.append(
            {
                "name": names[id(tensor.weight)],
                "rows": weight.size(0) if weight.ndim == 2 else 1,
                "cols": weight.size(-1),
                "norm": not isinstance(tensor, QLinear),
                "values": weight.reshape(-1).tolist(),
            }
        )
    return result


def restore_tensors(model: TinyGPT, records: list[dict]) -> None:
    expected = tensors(model)
    if len(records) != len(expected):
        raise ValueError("incorrect parameter count")
    with torch.no_grad():
        for tensor, metadata, record in zip(model.stored_tensors(), expected, records, strict=True):
            for key in ("name", "rows", "cols", "norm"):
                if record[key] != metadata[key]:
                    raise ValueError(f"tensor metadata mismatch: {key}")
            values = torch.tensor(record["values"], dtype=torch.float32)
            if values.numel() != tensor.weight.numel() or not torch.isfinite(values).all():
                raise ValueError("invalid parameter values")
            tensor.weight.copy_(values.reshape_as(tensor.weight))


def descriptor(path: Path, root: Path) -> dict:
    return {
        "path": str(path.relative_to(root)),
        "bytes": path.stat().st_size,
        "sha256": runlog.sha256_file(path),
    }


def prepare_job(root: Path, model: TinyGPT, train_file: Path, spec: TrainSpec, job_id: str) -> dict:
    """Freeze the actual Python data stream, not a replacement C++ RNG."""
    if spec.branches != 3 or spec.warmup_frac != 0.02 or spec.cooldown_frac != 0.1:
        raise ValueError("Xbox E0 requires the declared three-branch WSD protocol")
    root.mkdir(parents=True, exist_ok=False)
    # Share the hash-bound corpus inode; never modify a prepared training corpus.
    os.link(train_file, root / "train.bin")
    runlog.write_json(
        root / "initial.json", {"config": model.cfg.to_dict(), "tensors": tensors(model)}
    )
    data = np.memmap(root / "train.bin", mode="r", dtype=np.uint8)
    stream = DataStream(data, spec.batch, model.cfg.ctx, spec.seed)
    sch = schedule(spec, model.cfg.ctx)
    (root / "indices.bin").write_bytes(stream.plan(sch["ends"][-1]).astype("<u8").tobytes())
    job = {
        "schema": "floppylm.e0.job.v1",
        "job_id": job_id,
        "config": model.cfg.to_dict(),
        "spec": asdict(spec),
        "initialization": descriptor(root / "initial.json", root),
        "data": descriptor(root / "train.bin", root),
        "indices": descriptor(root / "indices.bin", root),
    }
    runlog.write_json(root / "job.json", job)
    return job


def compare(actual, expected) -> dict:
    a, b = np.asarray(actual, dtype=np.float32), np.asarray(expected, dtype=np.float32)
    if a.shape != b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
        return {"ok": False, "reason": "shape or nonfinite mismatch"}
    error = np.abs(a.astype(np.float64) - b)
    meaningful = np.abs(b) >= REL_FLOOR
    relative = error[meaningful] / np.abs(b[meaningful])
    absolute_max = float(error.max(initial=0))
    relative_max = float(relative.max(initial=0))
    return {
        "ok": bool(np.all(error <= ABS_GATE + REL_GATE * np.abs(b))),
        "max_bound_excess": float((error - (ABS_GATE + REL_GATE * np.abs(b))).max(initial=0)),
        "max_abs": absolute_max,
        "max_rel": relative_max,
    }


def fixture(model: TinyGPT, batch: int = 2) -> tuple[dict, dict]:
    """Independent PyTorch forward/autograd/AdamW oracle on one deterministic batch."""
    spec = TrainSpec(tokens=1024, batch=batch)
    initial = {"config": model.cfg.to_dict(), "tensors": tensors(model)}
    stream = DataStream(
        np.frombuffer(b"the cat sat on the mat. " * 20, dtype=np.uint8), batch, model.cfg.ctx, 7
    )
    x, y = stream.next()
    initial |= {
        "tokens": x.flatten().tolist(),
        "targets": y.flatten().tolist(),
        "batch": batch,
        "lr": spec.lr,
        "wd": spec.wd,
    }
    quantization = []
    names = {id(p): name for name, p in model.named_parameters()}
    for tensor in model.stored_tensors():
        if isinstance(tensor, QLinear):
            symbols, scales = tensor.codec.quantize(tensor.weight)
            quantization.append(
                {
                    "name": names[id(tensor.weight)],
                    "symbols": symbols.flatten().tolist(),
                    "scales": scales.flatten().tolist(),
                }
            )
    opt = _optimizer(model, spec)
    logits = model(x)
    loss = F.cross_entropy(logits.flatten(0, 1), y.flatten())
    loss.backward()
    gradients = {name: p.grad.flatten().tolist() for name, p in model.named_parameters()}
    norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
    opt.step()
    expected = {
        "logits": logits.detach().flatten().tolist(),
        "loss": loss.item(),
        "gradient_norm": norm.item(),
        "gradients": gradients,
        "quantization": quantization,
        "tensors": tensors(model),
    }
    return initial, expected


def verify_fixture(
    binary: Path,
    directory: Path,
    cfg: GPTConfig,
    *,
    gpu: bool = False,
    shader: Path | None = None,
    seed: int = 19,
) -> dict:
    directory.mkdir(parents=True, exist_ok=False)
    seed_all(seed)
    initial, expected = fixture(TinyGPT(cfg))
    runlog.write_json(directory / "fixture.json", initial)
    runlog.write_json(directory / "expected.json", expected)
    command = [
        str(binary.resolve()),
        "--fixture",
        str(directory / "fixture.json"),
        "--out",
        str(directory / "actual.json"),
    ]
    if not gpu:
        command.append("--reference")
    if shader:
        command.extend(["--shader", str(shader)])
    subprocess.run(command, check=True)
    actual = json.loads((directory / "actual.json").read_text())
    return check_fixture(actual, expected, cfg, directory, gpu=gpu, seed=seed)


def check_fixture(actual, expected, cfg, directory, *, gpu=True, seed=19):
    gates = {
        key: compare(actual[key], expected[key]) for key in ("logits", "loss", "gradient_norm")
    }
    gates["gradient-coverage"] = {
        "ok": len(actual["gradients"]) == len(expected["gradients"])
        and {r["name"] for r in actual["gradients"]} == set(expected["gradients"])
    }
    for record in actual["gradients"]:
        gates["gradient:" + record["name"]] = compare(
            record["values"], expected["gradients"][record["name"]]
        )
    update_diagnostics = {}
    for a, b in zip(actual["tensors"], expected["tensors"], strict=True):
        gates["tensor-metadata:" + b["name"]] = {
            "ok": all(a[k] == b[k] for k in ("name", "rows", "cols", "norm"))
        }
        update_diagnostics[b["name"]] = compare(a["values"], b["values"])
        gates["finite-update:" + b["name"]] = {
            "ok": bool(np.isfinite(np.float32(a["values"])).all())
        }
    for a, b in zip(actual["quantization"], expected["quantization"], strict=True):
        gates["symbols:" + b["name"]] = {
            "ok": a["name"] == b["name"] and a["symbols"] == b["symbols"]
        }
        gates["scales:" + b["name"]] = {
            "ok": scalar("ternary", cfg.scale_policy).scale_to_bytes(
                torch.tensor(a["scales"]).reshape(-1, 1)
            )
            == scalar("ternary", cfg.scale_policy).scale_to_bytes(
                torch.tensor(b["scales"]).reshape(-1, 1)
            )
        }
    if gpu:
        gates["hardware"] = {"ok": actual["hardware_gpu"] and actual["dispatches"] > 0}
    report = {
        "config": cfg.to_dict(),
        "seed": seed,
        "update_diagnostics": update_diagnostics,
        "purpose": "functional",
        "hardware_gpu": actual["hardware_gpu"],
        "gates": gates,
        "ok": all(v["ok"] for v in gates.values()),
    }
    runlog.write_json(directory / "parity.json", report)
    return report


def verify_optimizer(
    binary: Path | None, directory: Path, cfg: GPTConfig, *, executor=None
) -> dict:
    """AdamW receives identical gradients in both implementations, including tiny ones."""
    directory.mkdir(parents=True, exist_ok=False)
    seed_all(19)
    model = TinyGPT(cfg)
    spec = TrainSpec(tokens=1024)
    initial = {"config": cfg.to_dict(), "tensors": tensors(model), "steps": []}
    names = {id(p): name for name, p in model.named_parameters()}
    optimizer = _optimizer(model, spec)
    expected = []
    generator = torch.Generator().manual_seed(2718)
    for step, (magnitude, lr) in enumerate(((1e-8, 0.001), (1e-4, 0.003), (0.02, 0.01)), 1):
        gradients = []
        for tensor in model.stored_tensors():
            weight = tensor.weight
            grad = torch.randn(weight.shape, generator=generator) * magnitude
            weight.grad = grad
            gradients.append({"name": names[id(weight)], "values": grad.flatten().tolist()})
        initial["steps"].append({"step": step, "lr": lr, "wd": spec.wd, "gradients": gradients})
        norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        for group in optimizer.param_groups:
            group["lr"] = lr
        optimizer.step()
        moments = []
        for tensor in model.stored_tensors():
            state = optimizer.state[tensor.weight]
            moments.append(
                {
                    "name": names[id(tensor.weight)],
                    "first": state["exp_avg"].flatten().tolist(),
                    "second": state["exp_avg_sq"].flatten().tolist(),
                }
            )
        expected.append(
            {"tensors": tensors(model), "moments": moments, "gradient_norm": norm.item()}
        )
    runlog.write_json(directory / "fixture.json", initial)
    runlog.write_json(directory / "expected.json", {"steps": expected})
    if executor is not None:
        initial["schema"] = "floppylm.e0.optimizer.v1"
        runlog.write_json(directory / "actual.json", executor(initial))
    else:
        subprocess.run(
            [
                str(binary.resolve()),
                "--optimizer-fixture",
                str(directory / "fixture.json"),
                "--out",
                str(directory / "actual.json"),
            ],
            check=True,
        )
    actual = json.loads((directory / "actual.json").read_text())
    gates = {}
    for step, (a, b) in enumerate(zip(actual["steps"], expected, strict=True), 1):
        gates[f"{step}:norm"] = compare(a["gradient_norm"], b["gradient_norm"])
        for x, y in zip(a["tensors"], b["tensors"], strict=True):
            gates[f"{step}:weight:{y['name']}"] = compare(x["values"], y["values"])
        for x, y in zip(a["moments"], b["moments"], strict=True):
            for field in ("first", "second"):
                gates[f"{step}:{field}:{y['name']}"] = compare(x[field], y[field])
    report = {
        "purpose": "functional",
        "oracle": "PyTorch AdamW, identical input gradients",
        "gates": gates,
        "ok": all(v["ok"] for v in gates.values()),
    }
    runlog.write_json(directory / "parity.json", report)
    return report


def zero_row_gate(policy: str, core_fmt: str) -> dict:
    """S9 is independent of backend parity, including the tied 4-bit embedding."""
    weights = torch.tensor([[0.0, 0.0, 0.0, 0.0], [1.0, -1.0, 2.0, -2.0]])
    gates = {}
    for fmt in (core_fmt, "4bit"):
        codec = scalar(fmt, policy)
        symbols, scales = codec.quantize(weights)
        decoded = codec.dequant(symbols, scales)
        serialized = codec.decode(*codec.encode(weights), weights.shape)
        gates[fmt] = {
            "zero_scale": bool(scales[0].eq(0).all()),
            "zero_reconstruction": bool(decoded[0].eq(0).all()),
            "zero_serialized_reconstruction": bool(serialized[0].eq(0).all()),
            "actual_zero_row": serialized[0].tolist(),
        }
    return {
        "policy": policy,
        "core_fmt": core_fmt,
        "gates": gates,
        "ok": all(
            g["zero_scale"] and g["zero_reconstruction"] and g["zero_serialized_reconstruction"]
            for g in gates.values()
        ),
    }
