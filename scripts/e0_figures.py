"""Draw the two published c58a86 evidence figures from run summaries.

The cell lists are the closed eligible repairs. An in-progress trial is not a
series. Matplotlib is imported only while writing SVG, so the default test run
does not need the plots extra.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = "e0-20261004T103838Z-c58a86"
HORIZONS = ("T", "2T", "4T")
PAPER = "#f6f3ec"
PANEL = "#fffdf9"
INK = "#1d1c19"
MUTED = "#5e5a53"
GRID = "#ece7de"
SPINE = "#e3ddd2"
W = 820.0
H = 460.0
AX_LEFT = 64.0
AX_BOTTOM = 58.0
AX_WIDTH = 528.0
AX_HEIGHT = 330.0


@dataclass(frozen=True)
class SeriesSpec:
    name: str
    color: str
    cells: tuple[str, ...]
    scale_policy: str
    mlp: str | None = None


SCALE = (
    SeriesSpec("row16", "#24556e", ("000-repair", "001-repair"), "row16"),
    SeriesSpec("row8log", "#0d6a43", ("002-repair", "003-repair"), "row8log"),
)
MLP = (
    SeriesSpec("gelu", "#0d6a43", ("004-repair", "005-repair"), "row8log", "gelu"),
    SeriesSpec("swiglu", "#9a3412", ("006-repair",), "row8log", "swiglu"),
)


def label(values: tuple[float, float, float]) -> str:
    return "/".join(f"{v:.4f}" for v in values)


def _mean(rows: list[tuple[float, float, float]]) -> tuple[float, float, float]:
    if not rows:
        raise ValueError("a figure series needs at least one cell")
    return tuple(statistics.fmean(row[i] for row in rows) for i in range(3))


def _require_lower(left: tuple[float, ...], right: tuple[float, ...], message: str) -> None:
    if not all(a < b for a, b in zip(left, right, strict=True)):
        raise ValueError(message)


def load_cell(runs: Path, campaign: str, suffix: str) -> dict:
    if not suffix.endswith("-repair"):
        raise ValueError(f"{suffix} is not an S3 repair")
    path = runs / f"{campaign}-{suffix}" / "summary.json"
    summary = json.loads(path.read_text(encoding="utf-8"))
    if summary.get("status") != "completed":
        raise ValueError(f"{suffix} is not a completed cell")
    if summary.get("parity_individual_ok") is not True:
        raise ValueError(f"{suffix} is outside byte parity and is not eligible")
    branches = sorted(summary["branches"], key=lambda branch: branch["end_step"])
    if len(branches) != 3:
        raise ValueError(f"{suffix} does not have T, 2T and 4T")
    ends = [int(step) for step in summary["backend"]["schedule"]["ends"]]
    got = [int(branch["end_step"]) for branch in branches]
    if got != ends:
        raise ValueError(f"{suffix} branches {got} are not the schedule ends {ends}")
    values = tuple(float(branch["val_bpb"]) for branch in branches)
    if not all(math.isfinite(value) for value in values):
        raise ValueError(f"{suffix} has a non-finite val bpb")
    return {
        "suffix": suffix,
        "seed": int(summary["spec"]["seed"]),
        "mlp": summary["config"]["mlp"],
        "scale_policy": summary["config"]["scale_policy"],
        "val_bpb": values,
    }


def _group(runs: Path, campaign: str, spec: SeriesSpec) -> dict:
    cells = [load_cell(runs, campaign, suffix) for suffix in spec.cells]
    for cell in cells:
        if cell["scale_policy"] != spec.scale_policy:
            raise ValueError(f"{cell['suffix']} scale_policy is {cell['scale_policy']}")
        if spec.mlp is not None and cell["mlp"] != spec.mlp:
            raise ValueError(f"{cell['suffix']} mlp is {cell['mlp']}")
    values = [cell["val_bpb"] for cell in cells]
    return {
        "name": spec.name,
        "color": spec.color,
        "cells": cells,
        "mean": _mean(values),
        "single": len(cells) == 1,
    }


def scale_groups(runs: Path, campaign: str = CAMPAIGN) -> list[dict]:
    return [_group(runs, campaign, spec) for spec in SCALE]


def mlp_groups(runs: Path, campaign: str = CAMPAIGN) -> list[dict]:
    return [_group(runs, campaign, spec) for spec in MLP]


def scale_description(groups: list[dict]) -> str:
    row16, row8 = groups
    _require_lower(row8["mean"], row16["mean"], "row8log is not lower at every horizon")
    return (
        "Eligible S3 repairs only. "
        f"row16 mean {label(row16['mean'])}. "
        f"row8log mean {label(row8['mean'])}. "
        "row8log mean is lower at T, 2T and 4T."
    )


def mlp_description(groups: list[dict]) -> str:
    gelu, swiglu = groups
    if not swiglu["single"]:
        raise ValueError("the MLP figure shows one SwiGLU seed")
    values = swiglu["cells"][0]["val_bpb"]
    _require_lower(values, gelu["mean"], "SwiGLU seed is not lower at every horizon")
    return (
        "Eligible S3 repairs. "
        f"GELU mean of two seeds {label(gelu['mean'])}. "
        f"SwiGLU seed {swiglu['cells'][0]['seed']} only, {label(values)}, "
        "below the gelu mean at T, 2T and 4T. Not an activation decision."
    )


def _panel_name(group: dict, *, mean_suffix: bool) -> str:
    if group["single"]:
        return f"{group['name']} seed {group['cells'][0]['seed']}"
    if mean_suffix:
        return f"{group['name']} mean"
    return group["name"]


def _panel_value(group: dict) -> str:
    if group["single"]:
        return label(group["cells"][0]["val_bpb"])
    return label(group["mean"])


def _pyplot():
    try:
        import matplotlib
    except ImportError as exc:
        raise SystemExit(
            "matplotlib is missing; install the plots extra: python -m pip install -e '.[plots]'"
        ) from exc
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.ticker import FormatStrFormatter

    matplotlib.rcParams.update(
        {
            "svg.fonttype": "none",
            "svg.hashsalt": "floppylm-e0-figures",
            "font.family": "sans-serif",
            "font.sans-serif": ["DejaVu Sans"],
            "font.size": 12,
            "axes.unicode_minus": False,
        }
    )
    return plt, Line2D, FormatStrFormatter


def _top(px: float) -> float:
    return (H - px) / H


def _plot_group(ax, group: dict) -> None:
    color = group["color"]
    xs = (0, 1, 2)
    if not group["single"]:
        for cell in group["cells"]:
            ax.plot(xs, cell["val_bpb"], color=color, lw=1.0, alpha=0.5, zorder=2)
            ax.scatter(
                xs,
                cell["val_bpb"],
                s=18,
                color=color,
                edgecolors=PANEL,
                linewidths=0.6,
                zorder=4,
            )
        ax.plot(xs, group["mean"], color=color, lw=2.4, solid_capstyle="round", zorder=3)
        return
    values = group["cells"][0]["val_bpb"]
    ax.plot(xs, values, color=color, lw=2.4, solid_capstyle="round", zorder=3)
    ax.scatter(xs, values, s=22, color=color, edgecolors=PANEL, linewidths=0.7, zorder=4)


def _draw(
    path: Path,
    *,
    title: str,
    subtitle: str,
    description: str,
    ylim: tuple[float, float],
    yticks: tuple[float, ...],
    groups: list[dict],
    header: str,
    notes: tuple[str, ...],
    reading: str,
    mean_suffix: bool,
) -> None:
    plt, line2d, formatter = _pyplot()
    fig = plt.figure(figsize=(W / 72, H / 72), dpi=72)
    fig.patch.set_facecolor(PAPER)
    ax = fig.add_axes(
        (AX_LEFT / W, AX_BOTTOM / H, AX_WIDTH / W, AX_HEIGHT / H), facecolor=PANEL
    )
    for spine in ax.spines.values():
        spine.set_color(SPINE)
        spine.set_linewidth(0.8)
    ax.set_xlim(-0.5, 2.5)
    ax.set_ylim(*ylim)
    ax.set_xticks([0, 1, 2], list(HORIZONS))
    ax.set_yticks(list(yticks))
    ax.set_xlabel("cooldown end", color=MUTED, fontsize=10, labelpad=6)
    ax.tick_params(axis="x", colors=INK, labelsize=13, length=0, pad=3)
    ax.tick_params(axis="y", colors=MUTED, labelsize=11, length=0, pad=2)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.yaxis.set_major_formatter(formatter("%.2f"))
    for group in groups:
        _plot_group(ax, group)
    fig.text(28 / W, _top(28), title, color=INK, fontsize=16, va="center")
    fig.text(28 / W, _top(50), subtitle, color=MUTED, fontsize=10, va="center")
    fig.text(
        16 / W,
        (AX_BOTTOM + AX_HEIGHT / 2) / H,
        "val bpb",
        rotation=90,
        color=MUTED,
        fontsize=11,
        ha="center",
        va="center",
    )
    fig.text(614 / W, _top(86), header, color=MUTED, fontsize=11, va="center")
    columns = (614, 674, 734)
    for column, horizon in zip(columns, HORIZONS, strict=True):
        fig.text(column / W, _top(108), horizon, color="#8a847a", fontsize=10, va="center")
    cursor = 136.0
    for group in groups:
        name_y = _top(cursor)
        fig.add_artist(
            line2d(
                (614 / W, 642 / W),
                (name_y, name_y),
                transform=fig.transFigure,
                color=group["color"],
                lw=2.4,
                solid_capstyle="round",
            )
        )
        fig.text(
            650 / W,
            name_y,
            _panel_name(group, mean_suffix=mean_suffix),
            color=INK,
            fontsize=12,
            va="center",
        )
        cursor += 22
        for column, part in zip(columns, _panel_value(group).split("/"), strict=True):
            fig.text(column / W, _top(cursor), part, color="#3f3c37", fontsize=11, va="center")
        cursor += 30
    for note in notes:
        fig.text(614 / W, _top(cursor), note, color="#3f3c37", fontsize=11, va="center")
        cursor += 16
    fig.text(614 / W, _top(376), reading, color="#8a847a", fontsize=10, va="center")
    fig.text(
        614 / W,
        _top(394),
        "Lines join measured ends only.",
        color="#8a847a",
        fontsize=10,
        va="center",
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        path,
        format="svg",
        facecolor=PAPER,
        metadata={"Date": None, "Title": title, "Description": description},
    )
    plt.close(fig)
    svg = _normalize(path.read_text(encoding="utf-8"), title=title, description=description)
    path.write_text(svg, encoding="utf-8")


def _xml(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _normalize(svg: str, *, title: str, description: str) -> str:
    svg = re.sub(r"\s*<dc:date>.*?</dc:date>\n?", "", svg)
    svg = re.sub(r'\swidth="[^"]+"', ' width="820"', svg, count=1)
    svg = re.sub(r'\sheight="[^"]+"', ' height="460"', svg, count=1)
    svg = re.sub(r'\sviewBox="[^"]+"', ' viewBox="0 0 820 460"', svg, count=1)
    svg = svg.replace("<svg ", '<svg role="img" ', 1)
    block = f"<title>{_xml(title)}</title>\n<desc>{_xml(description)}</desc>"
    if "<title>" in svg:
        svg = re.sub(r"<title>.*?</title>(\s*<desc>.*?</desc>)?", block, svg, count=1, flags=re.S)
    else:
        svg = svg.replace(">", f">\n{block}", 1)
    return svg


def write_figures(root: Path) -> tuple[Path, Path]:
    runs = root / "docs/evidence/e0-v2/runs"
    scale = scale_groups(runs)
    mlp = mlp_groups(runs)
    scale_path = root / "docs/evidence/e0-v2/neutral-scale-c58a86.svg"
    mlp_path = root / "docs/evidence/e0-v2/neutral-mlp-c58a86.svg"
    campaign = CAMPAIGN
    _draw(
        scale_path,
        title="Neutral scale, validation bpb",
        subtitle=f"{campaign} · eligible S3 repairs · means are the selection metric",
        description=scale_description(scale),
        ylim=(1.28, 1.54),
        yticks=(1.30, 1.35, 1.40, 1.45, 1.50),
        groups=scale,
        header="mean val bpb",
        notes=("row8log is lower", "at T, 2T and 4T."),
        reading="Thin lines are the two seeds.",
        mean_suffix=False,
    )
    _draw(
        mlp_path,
        title="Neutral MLP, validation bpb",
        subtitle=f"{campaign} · eligible S3 repairs · SwiGLU is one seed",
        description=mlp_description(mlp),
        ylim=(1.23, 1.53),
        yticks=(1.25, 1.30, 1.35, 1.40, 1.45, 1.50),
        groups=mlp,
        header="val bpb",
        notes=("Below the gelu mean", "at T, 2T and 4T.", "Not a selection."),
        reading="Thin lines are the two seeds.",
        mean_suffix=True,
    )
    return scale_path, mlp_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Draw the published c58a86 evidence figures.")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    for path in write_figures(args.root):
        print(path.relative_to(args.root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
