"""CPU campaign path for the 1/16 pilot. Does not dispatch a console job.

Reads the published ADR 0024 shapes. A functional smoke trains a tiny
synthetic stand-in and is not a scientific result. The smoke does not freeze
a selection and does not reserve a final test. publish_signal reads eighteen
closed cells, freezes the eligible validation artifacts, and reserves one
final test. score_final_test is the only read of the test split, and it runs
once. The 1/16 signal is not the F1 verdict.

A dead job lock does not block the cell. If summary.json is absent and
trunk.pt matches the model, training resumes from that checkpoint. A cooldown
whose branch file is already present at that boundary is not run again.
"""

from __future__ import annotations

import hashlib
import json
import os
import statistics
import subprocess
from dataclasses import asdict
from pathlib import Path

import numpy as np
import torch

from .data import load as load_split
from .e1_plan import (
    SEEDS,
    TARGET_BYTES,
    VECTOR_LR,
    VECTOR_WD,
    MeanBpb,
    f1_abl,
    f1_holds,
    f1_separation,
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
from .parity import admissible, paired_sigma
from .seed import seed_all
from .train import TrainSpec, schedule, sliding_bpb, train_wsd
from .vq import VectorBook

# Largest batch at or under the E0 CLI default of 32 that lands T on a step
# at context 256. 20_780_800 / 256 = 81_175, and 81_175 % 25 == 0.
PILOT_BATCH = 25
PILOT_CTX = 256
# Roadmap S7 windows used by the E0 campaign. Saturation is recorded, not a gate.
EVAL_VAL_BYTES = 1 << 20
TEST_BYTES = 1 << 21
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


def _json_ready(value: object) -> object:
    """Turn numpy scalars into JSON values. A numpy bool is not a Python bool."""
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.integer):
        return int(value)
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    return value


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_json_ready(payload), indent=2) + "\n")


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
        + (
            "Trunk seconds were not saved. The training finished and the summary "
            "writer failed before the account was written.\n"
            if summary.get("account_recorded") is False
            else ""
        )
    )


def _pid_alive(pid: object) -> bool:
    if type(pid) is not int or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _claim_job(lock: Path, index: int) -> None:
    """One live job. A lock whose pid is dead does not block a resume."""
    if lock.exists():
        try:
            owner = json.loads(lock.read_text())
        except json.JSONDecodeError as exc:
            raise ValueError("job lock is not readable") from exc
        if not isinstance(owner, dict):
            raise ValueError("job lock is not readable")
        if _pid_alive(owner.get("pid")):
            raise ValueError("one scientific job at a time")
        lock.unlink()
    try:
        _exclusive_json(lock, {"index": index, "pid": os.getpid()})
    except ValueError as exc:
        raise ValueError("one scientific job at a time") from exc


def _load_trunk(path: Path) -> dict | None:
    if not path.is_file():
        return None
    ckpt = torch.load(path, map_location="cpu", weights_only=False)
    if not isinstance(ckpt, dict) or "step" not in ckpt or "model" not in ckpt:
        raise ValueError("trunk checkpoint is not a training checkpoint")
    if "spec" not in ckpt:
        raise ValueError("trunk checkpoint is not a training checkpoint")
    return ckpt


def _trunk_matches(model: TinyGPT, spec: TrainSpec, ckpt: dict) -> bool:
    if ckpt["spec"] != asdict(spec):
        return False
    current = model.state_dict()
    saved = ckpt["model"]
    if set(saved) != set(current):
        return False
    return all(tuple(saved[key].shape) == tuple(current[key].shape) for key in current)


def _resume_checkpoint(
    model: TinyGPT, spec: TrainSpec, path: Path, *, required: bool
) -> dict | None:
    """Return a trunk that belongs to this model. A foreign trunk is not resumed."""
    ckpt = _load_trunk(path)
    if ckpt is None:
        return None
    if _trunk_matches(model, spec, ckpt):
        return ckpt
    if required:
        raise ValueError("trunk checkpoint does not match this cell")
    return None


def _read_branch_records(run_dir: Path) -> dict[int, dict]:
    path = run_dir / "branches.json"
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text())
    rows = payload.get("branches") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise ValueError("branches.json has no branch list")
    found: dict[int, dict] = {}
    for row in rows:
        if not isinstance(row, dict) or type(row.get("end_step")) is not int:
            raise ValueError("branch record needs an end_step")
        found[row["end_step"]] = row
    return found


def _read_attempts(run_dir: Path) -> dict:
    path = run_dir / "attempts.json"
    if not path.is_file():
        return {"attempts": [], "s3_error": None}
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict) or not isinstance(payload.get("attempts"), list):
        raise ValueError("attempts.json has no attempt list")
    return {"attempts": payload["attempts"], "s3_error": payload.get("s3_error")}


def _finished_branch(
    run_dir: Path, end: int, recorded: dict[int, dict], val: np.ndarray, sch: dict
) -> dict:
    """Use the cooldown file already on disk. Do not train it again."""
    artifact = run_dir / f"branch-{end}.flp"
    if not artifact.is_file():
        raise ValueError("resumed trunk passed a cooldown whose branch file is missing")
    blob = artifact.read_bytes()
    digest = hashlib.sha256(blob).hexdigest()
    expected_tokens = end * sch["per_step"]
    cd_len = dict(zip(sch["ends"], sch["cooldowns"], strict=True))[end]
    row = recorded.get(end)
    if row is not None:
        if row.get("sha256") != digest or row.get("model_bytes") != len(blob):
            raise ValueError("branch file does not match the recorded cooldown")
        if row.get("end_step") != end or row.get("tokens_seen") != expected_tokens:
            raise ValueError("branch record does not match the cooldown")
        return {**row, "blob": blob}
    info = {"end_step": end, "tokens_seen": expected_tokens, "cooldown_steps": cd_len}
    scored = score_cooldown(unpack(blob), val, info)
    if scored["blob"] != blob:
        raise ValueError("saved cooldown does not round-trip")
    return scored


def _cell_finished(attempts: list[dict], s3_error: str | None) -> bool:
    if s3_error is not None:
        return True
    if not attempts:
        return False
    if attempts[-1].get("eligible") is True:
        return True
    return len(attempts) >= 2


def _train_attempt(
    model: TinyGPT,
    train: np.ndarray,
    val: np.ndarray,
    spec: TrainSpec,
    run_dir: Path,
    resume: dict | None = None,
) -> tuple[list[dict], dict]:
    run_dir.mkdir(parents=True, exist_ok=True)
    branches: list[dict] = []
    recorded = _read_branch_records(run_dir)
    sch = schedule(spec, model.cfg.ctx)
    resumed_step = None if resume is None else resume["step"]
    cd_start_of = {
        end: end - cd_len for end, cd_len in zip(sch["ends"], sch["cooldowns"], strict=True)
    }
    if resume is not None:
        for end in sch["ends"]:
            if resumed_step > cd_start_of[end]:
                branches.append(_finished_branch(run_dir, end, recorded, val, sch))
            else:
                break

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

    def skip_cooldown(end: int) -> bool:
        # Only a resume that is already sitting on this boundary can keep the file.
        if resumed_step != cd_start_of[end]:
            return False
        if not (run_dir / f"branch-{end}.flp").is_file():
            return False
        branches.append(_finished_branch(run_dir, end, recorded, val, sch))
        return True

    account = train_wsd(
        model,
        train,
        spec,
        on_branch,
        on_checkpoint,
        resume=resume,
        log=print,
        skip_cooldown=skip_cooldown,
    )
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
    _claim_job(lock, index)
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
    prior = _read_attempts(run_dir)
    attempts: list[dict] = list(prior["attempts"])
    s3_error = prior["s3_error"]
    if attempts and attempts[0].get("eligible") is False and s3_error is None:
        try:
            built = _apply_s3(built, attempts[0]["branches"][-1]["model_bytes"], 0)
        except ValueError as exc:
            s3_error = str(exc)
    if not _cell_finished(attempts, s3_error):
        pending = 1 if attempts else 0
        while True:
            resume = _resume_checkpoint(
                built["model"],
                built["spec"],
                run_dir / "trunk.pt",
                required=pending == 0,
            )
            branches, account = _train_attempt(
                built["model"], train, val, built["spec"], run_dir, resume=resume
            )
            ok, reasons = _eligible(branches)
            attempts.append(
                {
                    "retry_count": pending,
                    "submitted_d_ff": built["submitted_d_ff"],
                    "eligible": ok,
                    "reasons": reasons,
                    "branches": [_public_branch(row) for row in branches],
                    "trunk_seconds": account["trunk_seconds"],
                }
            )
            _write_json(run_dir / "attempts.json", {"attempts": attempts, "s3_error": s3_error})
            if ok or pending == 1:
                break
            try:
                built = _apply_s3(built, branches[-1]["model_bytes"], 0)
            except ValueError as exc:
                s3_error = str(exc)
                break
            pending = 1
    if not attempts:
        raise ValueError("a scientific cell closed without an attempt")
    counted = attempts[-1]
    branches = counted["branches"]
    delta = float(abs(branches[2]["val_bpb"] - branches[1]["val_bpb"]))
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
            "saturated": bool(delta < SATURATION_ABS),
            "gate": False,
        },
        "flops_per_token": built["model"].flops_per_token(),
        "stored_params": built["model"].stored_params(),
    }
    _write_json(evidence / "summary.json", summary)
    (evidence / "notes.md").write_text(_notes(summary))
    return summary


def _required_float(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(label)
    return float(value)


def _required_number(value: object, label: str) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(label)
    return value


def _check_summary(summary: dict, plan: dict) -> None:
    """A closed cell matches its plan row and did not open the test split."""
    if summary.get("kind") != "scientific-cell":
        raise ValueError("the signal reads scientific cells")
    if summary.get("id") != cell_id(plan):
        raise ValueError("cell id does not match the plan")
    if summary.get("arm") != plan["arm"] or summary.get("seed") != plan["seed"]:
        raise ValueError("cell arm or seed does not match the plan")
    if summary.get("core") != plan["core"]:
        raise ValueError("cell core does not match the plan")
    if summary.get("final_test_opened") is not False or summary.get("test_split_read") is not False:
        raise ValueError("a cell does not open the final test")
    if summary.get("console_job") is not False:
        raise ValueError("a cell is not a console job")
    tokens = pilot_t()
    expected = (tokens, 2 * tokens, 4 * tokens)
    if tuple(summary.get("token_ends") or ()) != expected or summary.get("token_T") != tokens:
        raise ValueError("cell token ends are not T, 2T and 4T")
    branches = summary.get("branches")
    if not isinstance(branches, list) or len(branches) != 3:
        raise ValueError("a scientific cell closes three cooldowns")
    for row, seen in zip(branches, expected, strict=True):
        if row.get("tokens_seen") != seen:
            raise ValueError("cooldown tokens do not match T, 2T and 4T")
        digest = row.get("sha256")
        if not isinstance(digest, str) or len(digest) != 64:
            raise ValueError("cooldown needs a sha256")
        try:
            int(digest, 16)
        except ValueError as exc:
            raise ValueError("cooldown needs a sha256") from exc
        if type(row.get("model_bytes")) is not int:
            raise ValueError("cooldown needs model_bytes")
        _required_float(row.get("val_bpb"), "cooldown needs a val_bpb")
        _required_float(row.get("fill"), "cooldown needs a fill")
    if summary.get("saturation", {}).get("gate") is not False:
        raise ValueError("saturation is recorded and is not a gate")
    ok, _reasons = _eligible(branches)
    if summary.get("eligible") is not ok:
        raise ValueError("cell eligibility does not match packed bytes")


def _trunk_seconds(summary: dict) -> float | None:
    """Sum recorded trunk seconds. A missing account stays null and is not invented."""
    attempts = summary.get("attempts")
    if not isinstance(attempts, list) or not attempts:
        raise ValueError("cell costs need the recorded attempts")
    total = 0.0
    for attempt in attempts:
        seconds = attempt.get("trunk_seconds")
        if seconds is None:
            return None
        total += _required_float(seconds, "cell costs need trunk_seconds")
    return total


def _cooldown_scores(summary: dict) -> tuple[float, float, float]:
    scores = tuple(
        _required_float(row["val_bpb"], "cooldown needs a val_bpb") for row in summary["branches"]
    )
    if len(scores) != 3:
        raise ValueError("a scientific cell closes three cooldowns")
    return scores[0], scores[1], scores[2]


def _minimizers(means: dict[str, MeanBpb], field: str) -> list[str]:
    best = min(getattr(arm, field) for arm in means.values())
    return sorted(name for name, arm in means.items() if getattr(arm, field) == best)


def _unique_best(names: list[str]) -> str | None:
    if len(names) == 1:
        return names[0]
    return None


def signal_from_cells(summaries: list[dict] | tuple[dict, ...]) -> dict:
    """Validation signal from the eighteen closed cells. Not the F1 verdict.

    Eligible cells are the only ones in the means. Saturation is copied and
    does not drop a cell. A seed mismatch records a null F1 and does not
    invent a sample sd. Rank disagreement is recorded and is not a failure.
    """
    plans = cell_plan()
    if len(summaries) != len(plans):
        raise ValueError("the signal needs the eighteen pilot cells")
    by_id: dict[str, dict] = {}
    for summary in summaries:
        ident = summary.get("id")
        if not isinstance(ident, str) or ident in by_id:
            raise ValueError("duplicate pilot cell")
        by_id[ident] = summary
    ordered: list[dict] = []
    for plan in plans:
        ident = cell_id(plan)
        summary = by_id.get(ident)
        if summary is None:
            raise ValueError("the signal needs the eighteen pilot cells")
        _check_summary(summary, plan)
        ordered.append(summary)

    tokens = pilot_t()
    ends = (tokens, 2 * tokens, 4 * tokens)
    eligible_rows: list[dict] = []
    exclusions: list[dict] = []
    saturation: list[dict] = []
    costs_cells: list[dict] = []
    fills: dict[str, float] = {}
    frozen: list[dict] = []
    for summary in ordered:
        branches = summary["branches"]
        ok, reasons = _eligible(branches)
        counted = branches[-1]
        fills[summary["id"]] = _required_float(counted["fill"], "cooldown needs a fill")
        sat = summary["saturation"]
        saturation.append(
            {
                "id": summary["id"],
                "abs_delta": _required_float(sat.get("abs_delta"), "saturation needs abs_delta"),
                "saturated": sat.get("saturated"),
                "gate": False,
            }
        )
        trunk_seconds = _trunk_seconds(summary)
        costs_cells.append(
            {
                "id": summary["id"],
                "trunk_seconds": trunk_seconds,
                "account_complete": trunk_seconds is not None,
                "flops_per_token": _required_number(
                    summary.get("flops_per_token"), "cell costs need flops_per_token"
                ),
                "stored_params": _required_number(
                    summary.get("stored_params"), "cell costs need stored_params"
                ),
            }
        )
        if not ok:
            exclusions.append(
                {"id": summary["id"], "reasons": reasons, "s3_error": summary.get("s3_error")}
            )
            continue
        scores = _cooldown_scores(summary)
        eligible_rows.append(
            {
                "id": summary["id"],
                "arm": summary["arm"],
                "seed": summary["seed"],
                "core": summary["core"],
                "scores": scores,
            }
        )
        frozen.append(
            {
                "name": summary["id"],
                "sha256": counted["sha256"],
                "model_bytes": counted["model_bytes"],
                "val_bpb": float(counted["val_bpb"]),
            }
        )

    by_arm: dict[str, list[dict]] = {}
    for row in eligible_rows:
        by_arm.setdefault(row["arm"], []).append(row)
    arm_means = {
        arm: MeanBpb(*(statistics.fmean(row["scores"][i] for row in rows) for i in range(3)))
        for arm, rows in by_arm.items()
    }
    arms = {
        arm: {
            "seeds": sorted(row["seed"] for row in by_arm[arm]),
            "t": mean.t,
            "t2": mean.t2,
            "t4": mean.t4,
            "n": len(by_arm[arm]),
        }
        for arm, mean in arm_means.items()
    }
    scalar_means = {arm: mean for arm, mean in arm_means.items() if not arm.startswith("vq-")}
    vector_means = {arm: mean for arm, mean in arm_means.items() if arm.startswith("vq-")}
    scalar_at_4t = _minimizers(scalar_means, "t4") if scalar_means else []
    vector_at_4t = _minimizers(vector_means, "t4") if vector_means else []
    best_scalar = _unique_best(scalar_at_4t)
    best_vector = _unique_best(vector_at_4t)
    if arm_means:
        rank = {
            "at_T": _minimizers(arm_means, "t"),
            "at_2T": _minimizers(arm_means, "t2"),
            "at_4T": _minimizers(arm_means, "t4"),
        }
        earlier = set(rank["at_T"]) & set(rank["at_2T"])
        rank["winner_at_4t_also_minimizes_earlier"] = set(rank["at_4T"]) <= earlier
    else:
        rank = {
            "at_T": [],
            "at_2T": [],
            "at_4T": [],
            "winner_at_4t_also_minimizes_earlier": None,
        }

    paired = None
    separation = None
    f1_at_1_16 = None
    if best_scalar is not None and best_vector is not None:
        scalar_map = {row["seed"]: row["scores"][2] for row in by_arm[best_scalar]}
        vector_map = {row["seed"]: row["scores"][2] for row in by_arm[best_vector]}
        try:
            paired_raw = paired_sigma(scalar_map, vector_map)
        except ValueError:
            paired_raw = None
        if paired_raw is not None:
            paired = {
                "seeds": paired_raw["seeds"],
                "mean": paired_raw["mean"],
                "sd": paired_raw["sd"],
                "n": paired_raw["n"],
            }
            separation = f1_separation(paired["sd"])
            f1_at_1_16 = f1_holds(arm_means[best_vector], arm_means[best_scalar], paired["sd"])

    ablations = []
    for rate in (0.5, 0.75):
        learned = {row["seed"]: row for row in by_arm.get(f"vq-{rate}-learned", ())}
        fixed = {row["seed"]: row for row in by_arm.get(f"vq-{rate}-fixed", ())}
        for seed in sorted(set(learned) & set(fixed)):
            left = learned[seed]["scores"]
            right = fixed[seed]["scores"]
            ablations.append(
                {
                    "rate": rate,
                    "seed": seed,
                    "t": f1_abl(left[0], right[0]),
                    "t2": f1_abl(left[1], right[1]),
                    "t4": f1_abl(left[2], right[2]),
                }
            )

    parity_sizes = {item["name"]: item["model_bytes"] for item in frozen}
    if parity_sizes:
        parity_ok, parity_reasons = admissible(parity_sizes, TARGET_BYTES)
        if not parity_ok:
            raise ValueError("eligible cells failed byte parity")
    else:
        parity_ok, parity_reasons = False, ["no eligible cell"]
    return {
        "kind": "pilot-signal",
        "scientific_result": False,
        "f1_verdict": None,
        "f1_at_1_16": f1_at_1_16,
        "f1_separation": separation,
        "final_test_opened": False,
        "test_split_read": False,
        "console_job": False,
        "token_T": tokens,
        "token_ends": list(ends),
        "n_cells": len(ordered),
        "n_eligible": len(eligible_rows),
        "parity": {"ok": parity_ok, "reasons": parity_reasons},
        "arms": arms,
        "best_scalar": best_scalar,
        "best_vector": best_vector,
        "scalar_at_4t": scalar_at_4t,
        "vector_at_4t": vector_at_4t,
        "rank": rank,
        "paired": paired,
        "f1_abl": ablations,
        "saturation": saturation,
        "costs": {
            "trunk_seconds": (
                sum(row["trunk_seconds"] for row in costs_cells)
                if all(row["account_complete"] for row in costs_cells)
                else None
            ),
            "account_complete": all(row["account_complete"] for row in costs_cells),
            "cells": costs_cells,
        },
        "exclusions": exclusions,
        "fill": fills,
        "frozen_hashes": frozen,
    }


def _signal_notes(signal: dict) -> str:
    f1 = signal["f1_at_1_16"]
    shown = "null" if f1 is None else str(f1).lower()
    lines = [
        "# 1/16 pilot signal",
        "",
        "Validation signal from the closed CPU cells. This file is not the F1 verdict.",
        "The verdict needs the same sign at 1/16 and at 1/4.",
        f"F1 at 1/16 is {shown}.",
        "Saturation is recorded and is not a gate.",
        f"Eligible cells: {signal['n_eligible']}. Exclusions: {len(signal['exclusions'])}.",
    ]
    if signal["final_test_opened"]:
        lines.append("A final test is reserved. This file did not read the test split.")
    else:
        lines.append("No eligible cell. No freeze and no final test were written.")
    lines.append("No console job was dispatched.")
    return "\n".join(lines) + "\n"


def publish_signal(evidence_root: Path, dest: Path) -> dict:
    """Read eighteen cell summaries and write the signal. Does not train.

    Freezes eligible 4T hashes and reserves the final test. Zero eligible
    cells publish the exclusions and do not freeze or reserve. Does not read
    the test split.
    """
    evidence_root = Path(evidence_root)
    dest = Path(dest)
    if (
        (dest / "summary.json").exists()
        or (dest / "freeze.json").exists()
        or (dest / "final-test.reservation.json").exists()
    ):
        raise ValueError("the signal record already exists")
    summaries = []
    for plan in cell_plan():
        path = evidence_root / cell_id(plan) / "summary.json"
        if not path.is_file():
            raise ValueError("a pilot cell is missing")
        summaries.append(json.loads(path.read_text()))
    signal = signal_from_cells(summaries)
    if signal["frozen_hashes"]:
        items = tuple({**item, "smoke": False} for item in signal["frozen_hashes"])
        freeze = freeze_selection(dest, items, purpose="scientific")
        open_final_test(freeze, dest)
        signal["final_test_opened"] = True
        signal["test_split_read"] = False
        signal["frozen_hashes"] = [
            {
                "name": item["name"],
                "sha256": item["sha256"],
                "model_bytes": item["model_bytes"],
                "val_bpb": item["val_bpb"],
            }
            for item in freeze["items"]
        ]
    _exclusive_json(dest / "summary.json", signal)
    (dest / "notes.md").write_text(_signal_notes(signal))
    return signal


def score_final_test(data_dir: Path, dest: Path, artifacts: dict[str, bytes]) -> dict:
    """Score the frozen artifacts once. The test split is read after the checks.

    The reservation and the freeze must already exist. A second call refuses.
    This does not decide the F1 verdict.
    """
    dest = Path(dest)
    data_dir = Path(data_dir)
    if not (dest / "final-test.reservation.json").is_file():
        raise ValueError("the final test scores only after the reservation")
    freeze_path = dest / "freeze.json"
    if not freeze_path.is_file():
        raise ValueError("the final test scores only a frozen selection")
    out = dest / "final-test.json"
    if out.exists():
        raise ValueError("the final test runs once")
    freeze = json.loads(freeze_path.read_text())
    if freeze.get("purpose") != "scientific":
        raise ValueError("the final test scores only a scientific freeze")
    items = freeze.get("items") or []
    if not items:
        raise ValueError("the final test scores a nonempty freeze")
    checked: list[tuple[dict, bytes]] = []
    for item in items:
        blob = artifacts.get(item["name"])
        if blob is None:
            raise ValueError("frozen artifact is missing")
        if hashlib.sha256(blob).hexdigest() != item["sha256"]:
            raise ValueError("frozen artifact hash mismatch")
        if len(blob) != item["model_bytes"]:
            raise ValueError("frozen artifact size mismatch")
        checked.append((item, blob))
    test_path = data_dir / "test.bin"
    if not test_path.is_file():
        raise ValueError("the final test needs the frozen test split")
    test = load_split(data_dir, "test")
    results = []
    for item, blob in checked:
        bpb, scored = sliding_bpb(unpack(blob), test, TEST_BYTES)
        results.append(
            {
                "name": item["name"],
                "sha256": item["sha256"],
                "model_bytes": item["model_bytes"],
                "test_bpb": bpb,
                "test_scored_bytes": scored,
            }
        )
    payload = {
        "kind": "final-test",
        "purpose": "scientific",
        "test_split_read": True,
        "f1_verdict": None,
        "console_job": False,
        "results": results,
    }
    _exclusive_json(out, payload)
    return payload
