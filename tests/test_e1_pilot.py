import hashlib
import json
import statistics

import numpy as np
import pytest

from floppylm.e1_pilot import (
    cell_id,
    cell_plan,
    freeze_selection,
    materialize_cell,
    open_final_test,
    pilot_schedule,
    pilot_t,
    publish_signal,
    run_functional_smoke,
    run_scientific_cell,
    score_cooldown,
    score_final_test,
    signal_from_cells,
)
from floppylm.e1_plan import (
    TARGET_BYTES,
    ff_bounds,
    init_pack,
    published_shapes,
    scalar_arms,
    shape_for_seed,
)
from floppylm.model import GPTConfig, TinyGPT
from floppylm.pack import pack_sections
from floppylm.parity import admissible


def test_schedule_lands_on_t_2t_4t():
    sch = pilot_schedule()
    tokens = pilot_t()
    assert tokens == 20_780_800
    assert sch["token_ends"] == (tokens, 2 * tokens, 4 * tokens)
    assert sch["ends"][0] * sch["per_step"] == tokens


def test_cell_plan_is_eighteen_recipes_and_seed_repair_keeps_width():
    cells = cell_plan()
    assert len(cells) == 18
    assert sum(cell["core"] == "vq" for cell in cells) == 12
    shape = published_shapes()[0]
    repaired = shape_for_seed(shape, 1)
    assert (repaired.d, repaired.n_layers) == (shape.d, shape.n_layers)
    lo, hi = ff_bounds(shape.d)
    assert lo <= repaired.d_ff <= hi
    assert shape_for_seed(shape, 0) == shape


def test_functional_smoke_is_not_a_result(tmp_path):
    record = run_functional_smoke(tmp_path)
    assert record["kind"] == "functional"
    assert record["scientific_result"] is False
    assert record["final_test_opened"] is False
    assert record["console_job"] is False
    assert record["cells"] == 18
    written = json.loads((tmp_path / "summary.json").read_text())
    assert written == record
    notes = (tmp_path / "notes.md").read_text()
    assert "not a scientific result" in notes
    assert "test split was not opened" in notes
    assert not (tmp_path / "freeze.json").exists()
    assert not (tmp_path / "final-test.reservation.json").exists()


def _item(name: str, nbytes: int, *, smoke: bool) -> dict:
    return {
        "name": name,
        "model_bytes": nbytes,
        "sha256": "ab" * 32,
        "val_bpb": 1.25,
        "smoke": smoke,
    }


def test_freeze_and_final_test_stay_closed_for_a_functional_record(tmp_path):
    functional = freeze_selection(
        tmp_path / "fun", (_item("smoke", 100, smoke=True),), purpose="functional"
    )
    assert functional["scientific_result"] is False
    assert functional["final_test_opened"] is False
    with pytest.raises(ValueError, match="scientific freeze"):
        open_final_test(functional, tmp_path / "closed")
    assert not (tmp_path / "closed" / "final-test.reservation.json").exists()
    refused = tmp_path / "refused"
    with pytest.raises(ValueError, match="byte parity"):
        freeze_selection(refused, (_item("wide", 100, smoke=False),), purpose="scientific")
    assert not (refused / "freeze.json").exists()
    with pytest.raises(ValueError, match="smoke cell"):
        freeze_selection(
            tmp_path / "smoke-sci", (_item("smoke", 85934, smoke=True),), purpose="scientific"
        )
    kept = freeze_selection(
        tmp_path / "sci", (_item("fixed-0.5", 85934, smoke=False),), purpose="scientific"
    )
    assert kept["final_test_opened"] is False
    with pytest.raises(ValueError, match="already exists"):
        freeze_selection(
            tmp_path / "sci", (_item("fixed-0.5", 85934, smoke=False),), purpose="scientific"
        )
    opened = open_final_test(kept, tmp_path / "sci")
    assert opened["final_test_opened"] is True
    assert opened["test_split_read"] is False
    reservation = json.loads((tmp_path / "sci" / "final-test.reservation.json").read_text())
    assert reservation["test_split_read"] is False
    with pytest.raises(ValueError, match="once"):
        open_final_test(kept, tmp_path / "sci")


def test_materialize_cell_keeps_the_published_seed0_shape_and_shared_t():
    ternary = materialize_cell(0)
    assert ternary["spec"].tokens == 20_780_800
    assert ternary["spec"].batch == 25
    assert ternary["token_ends"] == (20_780_800, 41_561_600, 83_123_200)
    assert (ternary["cfg"].d, ternary["cfg"].n_layers, ternary["cfg"].d_ff) == (80, 4, 262)
    two = materialize_cell(3)
    cfg, record = init_pack(scalar_arms()[1].nominal, seed=0)
    assert two["cfg"].d_ff == cfg.d_ff == record["submitted_d_ff"]
    assert (two["cfg"].d, two["cfg"].n_layers) == (96, 3)
    vector = materialize_cell(6)
    shape = published_shapes()[0]
    assert (vector["cfg"].d, vector["cfg"].n_layers, vector["cfg"].d_ff) == (
        shape.d,
        shape.n_layers,
        shape.d_ff,
    )
    assert vector["spec"].tokens == ternary["spec"].tokens
    assert vector["model"].cfg.core_fmt == "vq"
    repaired = materialize_cell(7)
    assert (repaired["cfg"].d, repaired["cfg"].n_layers) == (shape.d, shape.n_layers)
    lo, hi = ff_bounds(shape.d)
    assert lo <= repaired["cfg"].d_ff <= hi


def test_score_cooldown_packs_the_model_and_scores_the_given_bytes():
    cfg = GPTConfig(vocab=256, d=32, n_layers=1, n_heads=2, d_ff=48, ctx=32)
    row = score_cooldown(
        TinyGPT(cfg),
        np.arange(400, dtype=np.uint8),
        {"end_step": 4, "tokens_seen": 256, "cooldown_steps": 1},
    )
    assert row["model_bytes"] == len(row["blob"])
    assert len(row["sha256"]) == 64
    assert row["val_scored_bytes"] > 0
    assert isinstance(row["val_bpb"], float)


def test_scientific_cell_does_not_start_without_the_val_split(tmp_path):
    (tmp_path / "train.bin").write_bytes(b"abc")
    with pytest.raises(ValueError, match="frozen train and val"):
        run_scientific_cell(0, tmp_path, tmp_path / "runs", tmp_path / "evidence")
    assert not (tmp_path / "runs" / "job.lock").exists()
    assert not (tmp_path / "evidence").exists()


def _default_bpb(plan: dict) -> tuple[float, float, float]:
    table = {
        "ternary": (1.25, 1.25, 1.25),
        "2bit": (1.0, 1.0, 1.0),
        "vq-0.5-fixed": (0.5, 0.5, 0.5),
        "vq-0.5-learned": (0.75, 0.75, 0.75),
        "vq-0.75-fixed": (1.5, 1.5, 1.5),
        "vq-0.75-learned": (1.75, 1.75, 1.75),
    }
    return table[plan["arm"]]


def _retarget(
    row: dict, *, nbytes: int, bpb: tuple[float, float, float], sha: str | None = None
) -> None:
    tokens = pilot_t()
    ends = (tokens, 2 * tokens, 4 * tokens)
    digest = sha or row["branches"][0]["sha256"]
    for branch, seen, score in zip(row["branches"], ends, bpb, strict=True):
        branch["tokens_seen"] = seen
        branch["model_bytes"] = nbytes
        branch["fill"] = nbytes / TARGET_BYTES
        branch["sha256"] = digest
        branch["val_bpb"] = float(score)
    ok, _reasons = admissible({str(seen): nbytes for seen in ends}, TARGET_BYTES)
    row["eligible"] = ok


def _one_cell(plan: dict) -> dict:
    tokens = pilot_t()
    ends = (tokens, 2 * tokens, 4 * tokens)
    bpb = _default_bpb(plan)
    branches = []
    for seen, score in zip(ends, bpb, strict=True):
        branches.append(
            {
                "tokens_seen": seen,
                "model_bytes": 85934,
                "fill": 85934 / TARGET_BYTES,
                "sha256": "ab" * 32,
                "val_bpb": float(score),
            }
        )
    ok, _reasons = admissible({str(seen): 85934 for seen in ends}, TARGET_BYTES)
    return {
        "kind": "scientific-cell",
        "id": cell_id(plan),
        "arm": plan["arm"],
        "seed": plan["seed"],
        "core": plan["core"],
        "token_T": tokens,
        "token_ends": list(ends),
        "console_job": False,
        "final_test_opened": False,
        "test_split_read": False,
        "s3_error": None,
        "eligible": ok,
        "attempts": [{"retry_count": 0, "trunk_seconds": 1.0}],
        "branches": branches,
        "saturation": {"abs_delta": 0.5, "saturated": False, "gate": False},
        "flops_per_token": 3.0,
        "stored_params": 10,
    }


def _campaign() -> list[dict]:
    return [_one_cell(plan) for plan in cell_plan()]


def _write_cells(root, rows: list[dict]) -> None:
    for row in rows:
        path = root / row["id"] / "summary.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(row) + "\n")


def test_signal_uses_eligible_cells_and_does_not_decide_the_verdict(tmp_path):
    rows = _campaign()
    for row in rows:
        if row["id"] == "ternary-s0":
            _retarget(row, nbytes=85934, bpb=(1.5, 1.5, 1.5))
            row["saturation"]["saturated"] = False
            row["attempts"] = [
                {"retry_count": 0, "trunk_seconds": 2.0},
                {"retry_count": 1, "trunk_seconds": 0.5},
            ]
        elif row["arm"] == "ternary":
            _retarget(row, nbytes=85934, bpb=(1.25, 1.25, 1.25))
            row["saturation"]["saturated"] = True
        elif row["arm"] == "vq-0.75-learned":
            _retarget(row, nbytes=1000, bpb=(0.25, 0.25, 0.25))
            row["s3_error"] = "solver returned the same shape"
    signal = signal_from_cells(rows)
    assert signal["best_scalar"] == "2bit"
    assert signal["best_vector"] == "vq-0.5-fixed"
    assert signal["arms"]["ternary"]["t4"] == statistics.fmean([1.5, 1.25, 1.25])
    assert signal["f1_at_1_16"] is True
    assert signal["f1_verdict"] is None
    assert signal["scientific_result"] is False
    assert signal["f1_separation"] == 0.02
    assert signal["paired"]["sd"] == 0.0
    assert signal["paired"]["n"] == 3
    assert signal["rank"]["at_4T"] == ["vq-0.5-fixed"]
    assert signal["rank"]["winner_at_4t_also_minimizes_earlier"] is True
    learned = [item for item in signal["f1_abl"] if item["rate"] == 0.5]
    assert len(learned) == 3
    assert {item["t4"] for item in learned} == {0.25}
    assert [item for item in signal["f1_abl"] if item["rate"] == 0.75] == []
    excluded = {item["id"] for item in signal["exclusions"]}
    assert excluded == {f"vq-0.75-learned-s{seed}" for seed in (0, 1, 2)}
    assert {item["s3_error"] for item in signal["exclusions"]} == {"solver returned the same shape"}
    assert signal["costs"]["trunk_seconds"] == 19.5
    assert {item["stored_params"] for item in signal["costs"]["cells"]} == {10}
    assert "total_flops" not in signal["costs"]
    assert all(item["gate"] is False for item in signal["saturation"])
    assert signal["parity"]["ok"] is True
    assert signal["fill"]["ternary-s0"] == 85934 / TARGET_BYTES
    evidence = tmp_path / "evidence"
    _write_cells(evidence, rows)
    dest = tmp_path / "signal"
    published = publish_signal(evidence, dest)
    assert published["final_test_opened"] is True
    assert published["test_split_read"] is False
    assert published["console_job"] is False
    notes = (dest / "notes.md").read_text()
    assert "not the F1 verdict" in notes
    assert "did not read the test split" in notes
    freeze = json.loads((dest / "freeze.json").read_text())
    frozen_names = {item["name"] for item in freeze["items"]}
    assert "vq-0.75-learned-s0" not in frozen_names
    assert "ternary-s0" in frozen_names
    reservation = json.loads((dest / "final-test.reservation.json").read_text())
    assert reservation["test_split_read"] is False
    assert not (dest / "final-test.json").exists()
    with pytest.raises(ValueError, match="already exists"):
        publish_signal(evidence, dest)


def test_f1_is_null_when_the_paired_seeds_differ():
    rows = _campaign()
    for row in rows:
        if row["id"] == "vq-0.5-fixed-s2":
            _retarget(row, nbytes=1000, bpb=(0.5, 0.5, 0.5))
    signal = signal_from_cells(rows)
    assert signal["best_vector"] == "vq-0.5-fixed"
    assert signal["best_scalar"] == "2bit"
    assert signal["f1_at_1_16"] is None
    assert signal["paired"] is None
    assert signal["f1_verdict"] is None


def test_rank_disagreement_is_recorded():
    rows = _campaign()
    for row in rows:
        if row["arm"] == "vq-0.5-fixed":
            _retarget(row, nbytes=85934, bpb=(1.5, 0.5, 0.5))
    signal = signal_from_cells(rows)
    assert signal["rank"]["at_4T"] == ["vq-0.5-fixed"]
    assert signal["rank"]["winner_at_4t_also_minimizes_earlier"] is False
    assert signal["f1_at_1_16"] is False
    assert signal["f1_verdict"] is None


def test_signal_refuses_an_eligibility_flag_that_disagrees_with_the_bytes():
    rows = _campaign()
    rows[0]["eligible"] = not rows[0]["eligible"]
    with pytest.raises(ValueError, match="eligibility"):
        signal_from_cells(rows)


def test_signal_refuses_a_cell_that_opened_the_final_test():
    rows = _campaign()
    rows[0]["final_test_opened"] = True
    with pytest.raises(ValueError, match="final test"):
        signal_from_cells(rows)


def test_publish_signal_refuses_a_missing_cell(tmp_path):
    evidence = tmp_path / "evidence"
    _write_cells(evidence, _campaign()[:-1])
    dest = tmp_path / "signal"
    with pytest.raises(ValueError, match="missing"):
        publish_signal(evidence, dest)
    assert not (dest / "summary.json").exists()
    assert not (dest / "freeze.json").exists()


def test_zero_eligible_cells_publish_without_a_freeze(tmp_path):
    rows = _campaign()
    for row in rows:
        _retarget(row, nbytes=1000, bpb=(0.25, 0.25, 0.25))
        row["s3_error"] = "solver returned the same shape"
    signal = signal_from_cells(rows)
    assert signal["n_eligible"] == 0
    assert signal["f1_at_1_16"] is None
    assert signal["f1_verdict"] is None
    assert signal["frozen_hashes"] == []
    assert signal["rank"]["winner_at_4t_also_minimizes_earlier"] is None
    assert len(signal["exclusions"]) == 18
    evidence = tmp_path / "evidence"
    _write_cells(evidence, rows)
    dest = tmp_path / "signal"
    published = publish_signal(evidence, dest)
    assert published["final_test_opened"] is False
    assert published["test_split_read"] is False
    assert not (dest / "freeze.json").exists()
    assert not (dest / "final-test.reservation.json").exists()
    notes = (dest / "notes.md").read_text()
    assert "not the F1 verdict" in notes
    assert "No eligible cell" in notes


def test_score_final_test_reads_the_split_once_after_the_reservation(tmp_path):
    built = materialize_cell(0)
    blob, _parts = pack_sections(built["model"])
    nbytes = len(blob)
    ok, _reasons = admissible({"artifact": nbytes}, TARGET_BYTES)
    assert ok
    rows = _campaign()
    for row in rows:
        if row["id"] == "ternary-s0":
            _retarget(row, nbytes=nbytes, bpb=(1.0, 1.0, 1.0), sha=hashlib.sha256(blob).hexdigest())
        else:
            _retarget(row, nbytes=1000, bpb=(0.25, 0.25, 0.25))
    evidence = tmp_path / "evidence"
    _write_cells(evidence, rows)
    dest = tmp_path / "signal"
    signal = publish_signal(evidence, dest)
    assert [item["name"] for item in signal["frozen_hashes"]] == ["ternary-s0"]
    assert signal["test_split_read"] is False
    assert signal["f1_verdict"] is None
    data = tmp_path / "data"
    data.mkdir()
    with pytest.raises(ValueError, match="hash mismatch"):
        score_final_test(data, dest, {"ternary-s0": b"not-the-artifact"})
    assert not (data / "test.bin").exists()
    (data / "test.bin").write_bytes(bytes(range(128)))
    scored = score_final_test(data, dest, {"ternary-s0": blob})
    assert scored["test_split_read"] is True
    assert scored["f1_verdict"] is None
    assert scored["console_job"] is False
    assert scored["results"][0]["name"] == "ternary-s0"
    assert scored["results"][0]["test_scored_bytes"] > 0
    assert isinstance(scored["results"][0]["test_bpb"], float)
    with pytest.raises(ValueError, match="once"):
        score_final_test(data, dest, {"ternary-s0": blob})


def test_score_final_test_refuses_before_the_reservation(tmp_path):
    with pytest.raises(ValueError, match="reservation"):
        score_final_test(tmp_path, tmp_path / "missing", {})
    assert not (tmp_path / "test.bin").exists()
