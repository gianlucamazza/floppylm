"""CPU campaign path for the 1/16 pilot. Does not dispatch a console job.

Reads the published ADR 0024 shapes. A functional smoke trains a tiny
synthetic stand-in and is not a scientific result. The smoke does not freeze
a selection and does not reserve a final test. The test split stays closed
until a scientific cell freezes.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

import numpy as np
import torch

from .data import load as load_split
from .e1_plan import (
    SEEDS,
    TARGET_BYTES,
    VECTOR_LR,
    VECTOR_WD,
    init_pack,
    pilot_tokens,
    published_shapes,
    scalar_arms,
    scalar_s3,
    scalar_seed0_params,
    shape_for_seed,
    vector_config,
    vector_s3,
)
from .model import GPTConfig, TinyGPT
from .pack import pack_sections, unpack
from .parity import admissible
from .seed import seed_all
from .train import TrainSpec, schedule, sliding_bpb, train_wsd
from .vq import VectorBook

# Largest batch at or under the E0 CLI default of 32 that lands T on a step
# at context 256. 20_780_800 / 256 = 81_175, and 81_175 % 25 == 0.
PILOT_BATCH = 25
PILOT_CTX = 256
# Roadmap S7 window used by the E0 campaign. Saturation is recorded, not a gate.
EVAL_VAL_BYTES = 1 << 20
SATURATION_ABS = 0.01


def pilot_t() -> int:
    """Shared token count. The same integer for every arm and every seed."""
    return pilot_tokens(published_shapes(), scalar_seed0_params())


def pilot_schedule() -> dict:
    """Cooldowns end at T, 2T and 4T tokens. Does not train."""
    tokens = pilot_t()
    spec = TrainSpec(tokens=tokens, branches=3, batch=PILOT_BATCH, seed=0)
    sch = schedule(spec, PILOT_CTX)
    per_step = sch["per_step"]
    token_ends = tuple(end * per_step for end in sch["ends"])
    if token_ends != (tokens, 2 * tokens, 4 * tokens):
        raise ValueError("pilot schedule missed T, 2T and 4T")
    sch["token_T"] = tokens
    sch["token_ends"] = token_ends
    return sch


def cell_plan() -> tuple[dict, ...]:
    """Six recipes times three seeds. Seeds 1 and 2 resolve d_ff at cell start."""
    cells: list[dict] = []
    for arm in scalar_arms():
        for seed in SEEDS:
            cells.append({"arm": arm.name, "seed": seed, "core": arm.name})
    for shape in published_shapes():
        label = f"vq-{shape.rate}-{'learned' if shape.learned else 'fixed'}"
        for seed in SEEDS:
            cells.append(
                {
                    "arm": label,
                    "seed": seed,
                    "core": "vq",
                    "d": shape.d,
                    "n_layers": shape.n_layers,
                    "d_ff": shape.d_ff if seed == 0 else None,
                    "rate": shape.rate,
                    "learned": shape.learned,
                }
            )
    if len(cells) != 18:
        raise ValueError("the pilot is six recipes times three seeds")
    return tuple(cells)


def _exclusive_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    except FileExistsError as exc:
        raise ValueError("the record already exists") from exc
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def _freeze_item(item: dict) -> dict:
    name = item.get("name")
    digest = item.get("sha256")
    nbytes = item.get("model_bytes")
    score = item.get("val_bpb")
    smoke = item.get("smoke")
    if not isinstance(name, str) or not name:
        raise ValueError("freeze item needs a name")
    if not isinstance(digest, str) or len(digest) != 64:
        raise ValueError("freeze item needs a sha256")
    try:
        int(digest, 16)
    except ValueError as exc:
        raise ValueError("freeze item needs a sha256") from exc
    if type(nbytes) is not int or nbytes < 1:
        raise ValueError("freeze item needs model_bytes")
    if type(score) is not float:
        raise ValueError("freeze item needs a val_bpb")
    if type(smoke) is not bool:
        raise ValueError("freeze item needs a smoke flag")
    return {
        "name": name,
        "sha256": digest,
        "model_bytes": nbytes,
        "val_bpb": score,
        "smoke": smoke,
    }


def freeze_selection(root: Path, items: tuple[dict, ...], *, purpose: str) -> dict:
    """Write one freeze file. A scientific freeze keeps eligible packed sizes only."""
    if purpose not in ("functional", "scientific"):
        raise ValueError("freeze purpose is functional or scientific")
    if not items:
        raise ValueError("a freeze names at least one artifact")
    kept = tuple(_freeze_item(item) for item in items)
    if len({item["name"] for item in kept}) != len(kept):
        raise ValueError("freeze item names must be unique")
    if purpose == "scientific":
        if any(item["smoke"] for item in kept):
            raise ValueError("a scientific freeze rejects a smoke cell")
        sizes = {item["name"]: item["model_bytes"] for item in kept}
        ok, reasons = admissible(sizes, TARGET_BYTES)
        if not ok:
            raise ValueError("selection fails byte parity: " + "; ".join(reasons))
    record = {
        "purpose": purpose,
        "items": list(kept),
        "final_test_opened": False,
        "scientific_result": False,
    }
    _exclusive_json(Path(root) / "freeze.json", record)
    return record


def open_final_test(selection: dict, dest: Path) -> dict:
    """Reserve the one final test. Does not read the test split.

    The synthetic smoke does not call this. A functional freeze cannot open it.
    """
    if selection.get("purpose") != "scientific":
        raise ValueError("the final test opens only after a scientific freeze")
    if selection.get("final_test_opened") is True:
        raise ValueError("the final test runs once")
    dest = Path(dest)
    reservation = dest / "final-test.reservation.json"
    if reservation.exists():
        raise ValueError("the final test runs once: reservation exists")
    payload = {
        "purpose": "scientific",
        "final_test_opened": True,
        "test_split_read": False,
        "n_items": len(selection.get("items", ())),
    }
    _exclusive_json(reservation, payload)
    return {**selection, "final_test_opened": True, "test_split_read": False}


def run_functional_smoke(root: Path) -> dict:
    """One tiny synthetic train. The record is functional, not a result.

    Does not open the test split and does not reserve a final test.
    """
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    sch = pilot_schedule()
    data = np.frombuffer(b"the cat sat on the mat. " * 400, dtype=np.uint8)
    cfg = GPTConfig(vocab=256, d=32, n_layers=1, n_heads=2, d_ff=48, ctx=32)
    spec = TrainSpec(tokens=8 * 32 * 12, branches=3, batch=8, lr=3e-3, wd=0.1, seed=0)
    train_wsd(TinyGPT(cfg), data, spec, lambda *_args: None, log=lambda _line: None)
    record = {
        "kind": "functional",
        "scientific_result": False,
        "final_test_opened": False,
        "console_job": False,
        "token_T": sch["token_T"],
        "token_ends": list(sch["token_ends"]),
        "cells": len(cell_plan()),
    }
    (root / "summary.json").write_text(json.dumps(record, indent=2) + "\n")
    (root / "notes.md").write_text(
        "Functional smoke of the 1/16 CPU campaign path.\n"
        "This file is not a scientific result. The test split was not opened.\n"
        f"Published T is {record['token_T']}. Cooldown tokens are {record['token_ends']}.\n"
        "The pilot cells have not started.\n"
    )
    return record


def cell_id(plan: dict) -> str:
    """Stable name of one recipe and seed. Not a path on this machine."""
    return f"{plan['arm']}-s{plan['seed']}"


def materialize_cell(index: int) -> dict:
    """Build one of the eighteen cells from the published shapes.

    Seed 0 keeps the published vector shape. Seeds 1 and 2 may change only
    d_ff. Does not train and does not read a split.
    """
    cells = cell_plan()
    if type(index) is not int or not 0 <= index < len(cells):
        raise ValueError("pilot cell index is 0..17")
    plan = cells[index]
    tokens = pilot_t()
    seed = plan["seed"]
    if plan["core"] == "vq":
        shape = next(
            item
            for item in published_shapes()
            if item.rate == plan["rate"] and item.learned is plan["learned"]
        )
        resolved = shape_for_seed(shape, seed)
        cfg = vector_config(resolved.d, resolved.n_layers, resolved.d_ff)
        book = VectorBook(8, resolved.rate, seed, learned=resolved.learned)
        lr, wd = VECTOR_LR, VECTOR_WD
        seed_all(seed)
        model = TinyGPT(cfg, book)
        nominal_d_ff = shape.d_ff
    else:
        arm = next(item for item in scalar_arms() if item.name == plan["arm"])
        cfg, record = init_pack(arm.nominal, seed=seed)
        lr, wd = arm.lr, arm.wd
        seed_all(seed)
        model = TinyGPT(cfg)
        nominal_d_ff = arm.nominal.d_ff
        resolved = None
        plan = {**plan, "init_submitted_d_ff": record["submitted_d_ff"]}
    spec = TrainSpec(tokens=tokens, branches=3, batch=PILOT_BATCH, lr=lr, wd=wd, seed=seed)
    sch = schedule(spec, cfg.ctx)
    token_ends = tuple(end * sch["per_step"] for end in sch["ends"])
    if token_ends != (tokens, 2 * tokens, 4 * tokens):
        raise ValueError("pilot schedule missed T, 2T and 4T")
    return {
        "index": index,
        "id": cell_id(plan),
        "plan": plan,
        "model": model,
        "cfg": cfg,
        "spec": spec,
        "nominal_d_ff": nominal_d_ff,
        "submitted_d_ff": cfg.d_ff,
        "token_ends": token_ends,
        "resolved": resolved,
    }


def score_cooldown(model: TinyGPT, val: np.ndarray, info: dict) -> dict:
    """Pack the cooldown, score validation bytes, and return the branch record.

    The array passed in is the validation split. This function does not open
    the test split.
    """
    blob, parts = pack_sections(model)
    counted = unpack(blob)
    n_eval = min(len(val), EVAL_VAL_BYTES)
    val_bpb, scored = sliding_bpb(counted, val, n_eval)
    nbytes = len(blob)
    return {
        "end_step": info["end_step"],
        "tokens_seen": info["tokens_seen"],
        "cooldown_steps": info["cooldown_steps"],
        "model_bytes": nbytes,
        "fill": nbytes / TARGET_BYTES,
        "sha256": hashlib.sha256(blob).hexdigest(),
        "val_bpb": val_bpb,
        "val_scored_bytes": scored,
        "sections": parts,
        "blob": blob,
    }


def _git_sha() -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return out.strip() or None


def _public_branch(row: dict) -> dict:
    return {key: value for key, value in row.items() if key != "blob"}


def _eligible(branches: list[dict]) -> tuple[bool, list[str]]:
    sizes = {str(row["tokens_seen"]): row["model_bytes"] for row in branches}
    return admissible(sizes, TARGET_BYTES)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def _notes(summary: dict) -> str:
    branches = summary["branches"]
    scores = " / ".join(f"{row['val_bpb']:.4f}" for row in branches)
    counted = branches[-1]
    return (
        f"# {summary['id']}\n\n"
        "Scientific CPU cell of the 1/16 pilot. Not a console job.\n"
        "The test split was not opened. This file is not the pilot signal\n"
        "and it is not the F1 verdict.\n\n"
        f"T is {summary['token_T']}. Cooldown tokens are {summary['token_ends']}.\n"
        f"Submitted d_ff is {summary['submitted_d_ff']}. S3 applied: {summary['s3_applied']}.\n"
        f"4T packed bytes are {counted['model_bytes']} (fill {counted['fill']:.6f}).\n"
        f"Validation bpb at T, 2T and 4T: {scores}.\n"
        f"Saturation |4T − 2T| is {summary['saturation']['abs_delta']}. "
        "It is recorded and is not a gate.\n"
        f"Eligible for the signal: {summary['eligible']}.\n"
    )


def _train_attempt(
    model: TinyGPT, train: np.ndarray, val: np.ndarray, spec: TrainSpec, run_dir: Path
) -> tuple[list[dict], dict]:
    branches: list[dict] = []

    def on_branch(end: int, branch: TinyGPT, info: dict) -> None:
        row = score_cooldown(branch, val, info)
        artifact = run_dir / f"branch-{end}.flp"
        artifact.write_bytes(row["blob"])
        branches.append(row)
        public = [_public_branch(item) for item in branches]
        _write_json(run_dir / "branches.json", {"branches": public})
        print(
            json.dumps(
                {"end_step": end, "model_bytes": row["model_bytes"], "val_bpb": row["val_bpb"]}
            ),
            flush=True,
        )

    def on_checkpoint(ckpt: dict) -> None:
        target = run_dir / "trunk.pt"
        temporary = target.with_suffix(".pt.tmp")
        torch.save(ckpt, temporary)
        temporary.replace(target)

    account = train_wsd(model, train, spec, on_branch, on_checkpoint, log=print)
    if len(branches) != 3 or branches[-1]["tokens_seen"] != 4 * spec.tokens:
        raise ValueError("the scientific cell did not close T, 2T and 4T")
    return branches, account


def _apply_s3(built: dict, measured_bytes: int, retry_count: int) -> dict:
    plan = built["plan"]
    seed = plan["seed"]
    if plan["core"] == "vq":
        found = vector_s3(
            built["resolved"], seed, measured_bytes, smoke=False, retry_count=retry_count
        )
        if found is None:
            raise ValueError("S3 was asked to repair an admissible file")
        cfg = vector_config(found.d, found.n_layers, found.d_ff)
        book = VectorBook(8, found.rate, seed, learned=found.learned)
        seed_all(seed)
        model = TinyGPT(cfg, book)
        resolved = found
    else:
        cfg = scalar_s3(built["cfg"], measured_bytes, smoke=False, retry_count=retry_count)
        if cfg is None:
            raise ValueError("S3 was asked to repair an admissible file")
        seed_all(seed)
        model = TinyGPT(cfg)
        resolved = None
    return {**built, "model": model, "cfg": cfg, "submitted_d_ff": cfg.d_ff, "resolved": resolved}


def run_scientific_cell(index: int, data_dir: Path, run_root: Path, evidence_root: Path) -> dict:
    """Train one cell on the lab CPU. One job at a time. Does not open the test split.

    Writes notes.md and summary.json when the cell closes. Artifacts stay under
    the run directory. A second S3 is refused.
    """
    data_dir = Path(data_dir)
    if not (data_dir / "train.bin").is_file() or not (data_dir / "val.bin").is_file():
        raise ValueError("a scientific cell needs the frozen train and val splits")
    run_root = Path(run_root)
    evidence_root = Path(evidence_root)
    run_root.mkdir(parents=True, exist_ok=True)
    lock = run_root / "job.lock"
    if lock.exists():
        raise ValueError("one scientific job at a time")
    _exclusive_json(lock, {"index": index, "pid": os.getpid()})
    try:
        return _run_locked_cell(index, data_dir, run_root, evidence_root)
    finally:
        lock.unlink(missing_ok=True)


def _run_locked_cell(index: int, data_dir: Path, run_root: Path, evidence_root: Path) -> dict:
    built = materialize_cell(index)
    evidence = evidence_root / built["id"]
    if (evidence / "summary.json").exists():
        raise ValueError("cell evidence already exists")
    run_dir = run_root / built["id"]
    run_dir.mkdir(parents=True, exist_ok=True)
    threads = os.cpu_count() or 1
    torch.set_num_threads(threads)
    train = load_split(data_dir, "train")
    val = load_split(data_dir, "val")
    attempts: list[dict] = []
    s3_error = None
    for retry_count in (0, 1):
        branches, account = _train_attempt(built["model"], train, val, built["spec"], run_dir)
        ok, reasons = _eligible(branches)
        attempts.append(
            {
                "retry_count": retry_count,
                "submitted_d_ff": built["submitted_d_ff"],
                "eligible": ok,
                "reasons": reasons,
                "branches": [_public_branch(row) for row in branches],
                "trunk_seconds": account["trunk_seconds"],
            }
        )
        if ok or retry_count == 1:
            break
        try:
            built = _apply_s3(built, branches[-1]["model_bytes"], retry_count)
        except ValueError as exc:
            s3_error = str(exc)
            break
    counted = attempts[-1]
    branches = counted["branches"]
    delta = abs(branches[2]["val_bpb"] - branches[1]["val_bpb"])
    summary = {
        "kind": "scientific-cell",
        "id": built["id"],
        "index": index,
        "arm": built["plan"]["arm"],
        "seed": built["plan"]["seed"],
        "core": built["plan"]["core"],
        "d": built["cfg"].d,
        "n_layers": built["cfg"].n_layers,
        "nominal_d_ff": built["nominal_d_ff"],
        "submitted_d_ff": counted["submitted_d_ff"],
        "rate": built["plan"].get("rate"),
        "learned": built["plan"].get("learned"),
        "token_T": built["spec"].tokens,
        "token_ends": list(built["token_ends"]),
        "batch": built["spec"].batch,
        "lr": built["spec"].lr,
        "wd": built["spec"].wd,
        "threads": threads,
        "source": _git_sha(),
        "console_job": False,
        "final_test_opened": False,
        "test_split_read": False,
        "signal_published": False,
        "s3_applied": len(attempts) == 2 and s3_error is None,
        "s3_error": s3_error,
        "eligible": counted["eligible"],
        "attempts": attempts,
        "branches": branches,
        "saturation": {
            "abs_delta": delta,
            "criterion": f"|bpb(4T) - bpb(2T)| < {SATURATION_ABS}",
            "saturated": delta < SATURATION_ABS,
            "gate": False,
        },
        "flops_per_token": built["model"].flops_per_token(),
        "stored_params": built["model"].stored_params(),
    }
    _write_json(evidence / "summary.json", summary)
    (evidence / "notes.md").write_text(_notes(summary))
    return summary
