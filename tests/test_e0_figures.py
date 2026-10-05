"""The c58a86 evidence figures quote the published eligible means."""

import ast
import importlib.util
import sys
from pathlib import Path

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


def test_swiglu_seed_0_is_one_eligible_seed():
    gelu, swiglu = figures.mlp_groups(RUNS)
    assert swiglu["single"]
    assert swiglu["cells"][0]["seed"] == 0
    assert swiglu["cells"][0]["suffix"] == "006-repair"
    assert figures.label(swiglu["cells"][0]["val_bpb"]) == "1.4568/1.3403/1.2615"
    assert all(a < b for a, b in zip(swiglu["cells"][0]["val_bpb"], gelu["mean"], strict=True))


def test_closed_cells_omit_trial_007():
    used = [cell for series in (*figures.SCALE, *figures.MLP) for cell in series.cells]
    assert all(not cell.startswith("007") for cell in used)


def test_committed_svgs_quote_those_labels():
    scale = (ROOT / "docs/evidence/e0-v2/neutral-scale-c58a86.svg").read_text(encoding="utf-8")
    mlp = (ROOT / "docs/evidence/e0-v2/neutral-mlp-c58a86.svg").read_text(encoding="utf-8")
    for text in ("1.5127", "1.3933", "1.3121", "1.5076", "1.3856", "1.3059"):
        assert text in scale
    assert "row8log mean is lower at T, 2T and 4T." in scale
    for text in ("1.4568", "1.3403", "1.2615", "Not an activation decision."):
        assert text in mlp
    assert "One seed is not a selection." in mlp
