"""Accepted E0 protocol shared by execution and read-only preparation."""

from . import shapes

PROTOCOL_ADR = "0015"


def protocol_spec() -> dict:
    """Return fresh values for the campaign to freeze."""
    return {
        "budget_frac": 1 / 16,
        "neutral_width": 96,
        "neutral_layers": 3,
        "neutral_seeds": [0, 1],
        "tuning_seed": 0,
        "grid_seed": 0,
        "paired_seeds": list(range(5)),
        "batch": 32,
        "ctx": 256,
        "scale_order": ["row16", "row8log"],
        "mlp_order": ["gelu", "swiglu", "relu2"],
        "lr": [0.001, 0.003, 0.01],
        "ternary_delta": [0.5, 0.7],
        "ternary_wd": 0.1,
        "2bit_wd": [0, 0.1],
        "grid_widths": list(range(64, 257, 16)),
        "grid_layers": list(range(1, 17)),
        "grid_ff_range": [2.0, 6.0],
        "grid_embedding_share": [0.08, 0.20],
        "grid_min_nominal_fill": 0.995,
        "selection": "minimum mean 4T val bpb; declared enumeration order breaks ties",
        "eligibility": ("actual individual and reciprocal byte parity; saturation recorded"),
        "rank_stability": "4T winner is a minimizer of mean val bpb at T and 2T",
        "byte_repair": "at most one fresh attempt per trial, preserving recipe",
    }


def grid_configs(base, budget, protocol):
    return shapes.grid(
        base,
        budget,
        widths=protocol["grid_widths"],
        layers=protocol["grid_layers"],
        ff_range=protocol["grid_ff_range"],
        emb_share=protocol["grid_embedding_share"],
        fill_min=protocol["grid_min_nominal_fill"],
    )
