import json

import pytest

from floppylm.runlog import make_exclusive_dir, new_run_id, set_status, write_atomic


def test_run_ids_are_unique() -> None:
    assert len({new_run_id("x") for _ in range(50)}) == 50


def test_exclusive_dir_and_atomic_write(tmp_path) -> None:
    d = make_exclusive_dir(tmp_path / "r1")
    with pytest.raises(FileExistsError):
        make_exclusive_dir(tmp_path / "r1")
    write_atomic(d / "a.txt", "one")
    write_atomic(d / "a.txt", "two")
    assert (d / "a.txt").read_text() == "two"
    assert [p.name for p in d.iterdir()] == ["a.txt"]


def test_status_states(tmp_path) -> None:
    set_status(tmp_path, "running")
    assert json.loads((tmp_path / "status.json").read_text())["state"] == "running"
    with pytest.raises(AssertionError):
        set_status(tmp_path, "done")
