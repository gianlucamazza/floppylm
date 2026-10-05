"""The c58a86 evidence figures quote the published eligible means."""

import ast
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("e0_figures", ROOT / "scripts/e0_figures.py")
figures = importlib.util.module_from_spec(spec)
sys.modules["e0_figures"] = figures
spec.loader.exec_module(figures)

RUNS = ROOT / "docs/evidence/e0-v2/runs"


def test_matplotlib_is_not_a_module_import():
    tree = ast.parse((ROOT / "scripts/e0_figures.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Import):
            names = [alias.name.split(".")[0] for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module.split(".")[0]]
        else:
            continue
        assert "matplotlib" not in names


def test_scale_means_match_the_published_labels():
    groups = figures.scale_groups(RUNS)
    assert figures.label(groups[0]["mean"]) == "1.5127/1.3933/1.3121"
    assert figures.label(groups[1]["mean"]) == "1.5076/1.3856/1.3059"
    assert all(a < b for a, b in zip(groups[1]["mean"], groups[0]["mean"], strict=True))


def test_gelu_repairs_repeat_the_row8log_repairs():
    scale = figures.scale_groups(RUNS)
    mlp = figures.mlp_groups(RUNS)
    assert [cell["val_bpb"] for cell in mlp[0]["cells"]] == [
        cell["val_bpb"] for cell in scale[1]["cells"]
    ]
    assert figures.label(mlp[0]["mean"]) == "1.5076/1.3856/1.3059"


def test_swiglu_choice_and_relu2_mean():
    gelu, swiglu, relu2 = figures.mlp_groups(RUNS)
    assert [cell["suffix"] for cell in swiglu["cells"]] == ["006-repair", "007-repair"]
    assert figures.label(swiglu["cells"][0]["val_bpb"]) == "1.4568/1.3403/1.2615"
    assert figures.label(swiglu["cells"][1]["val_bpb"]) == "1.4694/1.3544/1.2793"
    assert figures.label(swiglu["mean"]) == "1.4631/1.3473/1.2704"
    assert [cell["suffix"] for cell in relu2["cells"]] == ["008-repair", "009-repair"]
    assert figures.label(relu2["cells"][0]["val_bpb"]) == "1.4749/1.3597/1.2807"
    assert figures.label(relu2["cells"][1]["val_bpb"]) == "1.4790/1.3679/1.2837"
    assert figures.label(relu2["mean"]) == "1.4770/1.3638/1.2822"
    assert not relu2["single"]
    assert all(a < b for a, b in zip(swiglu["mean"], gelu["mean"], strict=True))
    assert all(a < b for a, b in zip(swiglu["mean"], relu2["mean"], strict=True))
    assert all(a < b for a, b in zip(relu2["mean"], gelu["mean"], strict=True))


def test_closed_cells_omit_trial_010():
    used = [cell for series in (*figures.SCALE, *figures.MLP) for cell in series.cells]
    assert all(not cell.startswith("010") for cell in used)


def test_committed_svgs_quote_those_labels():
    scale = (ROOT / "docs/evidence/e0-v2/neutral-scale-c58a86.svg").read_text(encoding="utf-8")
    mlp = (ROOT / "docs/evidence/e0-v2/neutral-mlp-c58a86.svg").read_text(encoding="utf-8")
    for text in ("1.5127", "1.3933", "1.3121", "1.5076", "1.3856", "1.3059"):
        assert text in scale
    assert "row8log mean is lower at T, 2T and 4T." in scale
    assert "Thin lines are the two seeds." in scale
    for text in ("1.4631", "1.3473", "1.2704", "1.4770", "1.3638", "1.2822"):
        assert text in mlp
    assert "SwiGLU is the recorded choice; nominal d_ff is 274." in mlp
    assert "SwiGLU mean is lower" in mlp
    assert "Nominal d_ff is 274." in mlp
    assert "Not an activation decision." not in mlp


def _summary(*, parity=True):
    ends = (10, 20, 30)
    rows = [{"end_step": step, "val_bpb": 1.5 - i * 0.1} for i, step in enumerate(ends)]
    return {
        "status": "completed",
        "parity_individual_ok": parity,
        "branches": rows,
        "backend": {"schedule": {"ends": list(ends)}},
        "config": {"mlp": "gelu", "scale_policy": "row8log"},
        "spec": {"seed": 0},
    }


def test_load_cell_rejects_an_ineligible_summary(tmp_path: Path):
    campaign = "e0-test"
    suffix = "000-repair"
    path = tmp_path / f"{campaign}-{suffix}"
    path.mkdir()
    (path / "summary.json").write_text(json.dumps(_summary(parity=False)), encoding="utf-8")
    with pytest.raises(ValueError, match="byte parity"):
        figures.load_cell(tmp_path, campaign, suffix)


def test_load_cell_rejects_a_branch_that_is_not_a_horizon(tmp_path: Path):
    campaign = "e0-test"
    suffix = "000-repair"
    path = tmp_path / f"{campaign}-{suffix}"
    path.mkdir()
    body = _summary()
    body["branches"][2]["end_step"] = 31
    (path / "summary.json").write_text(json.dumps(body), encoding="utf-8")
    with pytest.raises(ValueError, match="schedule ends"):
        figures.load_cell(tmp_path, campaign, suffix)


def test_load_cell_rejects_an_original_outside_the_repair(tmp_path: Path):
    with pytest.raises(ValueError, match="S3 repair"):
        figures.load_cell(tmp_path, "e0-test", "007")
