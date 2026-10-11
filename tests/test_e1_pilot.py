import json

import pytest

from floppylm.e1_pilot import (
    cell_plan,
    freeze_selection,
    open_final_test,
    pilot_schedule,
    pilot_t,
    run_functional_smoke,
)
from floppylm.e1_plan import ff_bounds, published_shapes, shape_for_seed


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
