"""CPU campaign path for the 1/16 pilot. Does not dispatch a console job.

Reads the published ADR 0024 shapes. A functional smoke trains a tiny
synthetic stand-in and is not a scientific result. The smoke does not freeze
a selection and does not reserve a final test. The test split stays closed
until a scientific cell freezes.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np

from .e1_plan import (
    SEEDS,
    TARGET_BYTES,
    pilot_tokens,
    published_shapes,
    scalar_arms,
    scalar_seed0_params,
)
from .model import GPTConfig, TinyGPT
from .parity import admissible
from .train import TrainSpec, schedule, train_wsd

# Largest batch at or under the E0 CLI default of 32 that lands T on a step
# at context 256. 20_780_800 / 256 = 81_175, and 81_175 % 25 == 0.
PILOT_BATCH = 25
PILOT_CTX = 256


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
