import json

import numpy as np
import pytest

from floppylm.e1_pilot import (
    cell_plan,
    freeze_selection,
    materialize_cell,
    open_final_test,
    pilot_schedule,
    pilot_t,
    run_functional_smoke,
    run_scientific_cell,
    score_cooldown,
)
from floppylm.e1_plan import ff_bounds, init_pack, published_shapes, scalar_arms, shape_for_seed
from floppylm.model import GPTConfig, TinyGPT


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
