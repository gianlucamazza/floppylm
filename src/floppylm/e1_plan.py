"""Specified 1/16 host plan from ADR 0023.

Materializes the two stored scalar arms, their ADR 0019 init-pack, and the
four shared G=8 books. Computes the F1 separation. Does not train, does not
freeze a selection, and does not open the test split.

ADR 0023 does not name the vector width, depth, d_ff, learning rate, or
weight decay. T is 20 times the stored-parameter count of the largest arm.
The vector arms have no shape, so this module does not name a pilot token count.
"""

from __future__ import annotations

from dataclasses import dataclass

from .model import GPTConfig, TinyGPT
from .pack import pack_sections
from .parity import admissible
from .seed import seed_all
from .shapes import fill_d_ff
from .vq import VectorBook

SEEDS = (0, 1, 2)
TARGET_BYTES = 11_000_000 / 16 / 8
TOKENS_PER_STORED_PARAM = 20
SELECTION_SHA256 = "de80fff08e750702784e6efbcb583ca86de566965207212c1c6531822a05bbe4"
_VECTOR_SHAPE = (
    "ADR 0023 does not name the vector width, depth, d_ff, learning rate, or weight decay"
)


@dataclass(frozen=True)
class ScalarArm:
    """One stored 94847b arm. ``nominal`` is the decision, not a submitted repair."""

    name: str
    nominal: GPTConfig
    lr: float
    wd: float


@dataclass(frozen=True)
class BookSpec:
    """One shared VQB1 identity. The book seed is the arm seed, not a new seed."""

    dimension: int
    rate: float
    learned: bool

    def __post_init__(self) -> None:
        if self.dimension != 8 or self.rate not in (0.5, 0.75) or type(self.learned) is not bool:
            raise ValueError(
                "ADR 0023 trains shared G=8 at rates 0.5 and 0.75; "
                "shared G=16 at rate 0.5 needs an edit of that ADR before the first attempt"
            )

    @property
    def shared_bytes(self) -> int:
        if not self.learned:
            return 16
        levels = 1 << int(self.dimension * self.rate)
        return 16 + levels * self.dimension * 2


@dataclass(frozen=True)
class MeanBpb:
    """Mean validation bits per byte at the three cooldowns."""

    t: float
    t2: float
    t4: float


def _scalar_config(core_fmt: str, d: int, n_layers: int, d_ff: int) -> GPTConfig:
    return GPTConfig(
        vocab=256,
        d=d,
        n_layers=n_layers,
        n_heads=d // 16,
        d_ff=d_ff,
        mlp="swiglu",
        core_fmt=core_fmt,
        emb_fmt="4bit",
        scale_policy="row8log",
        delta=0.5,
        qk_norm=False,
        ctx=256,
    )


def scalar_arms() -> tuple[ScalarArm, ScalarArm]:
    """Ternary and 2-bit recipes copied from the stored 94847b decisions."""
    return (
        ScalarArm("ternary", _scalar_config("ternary", 80, 4, 262), 0.01, 0.1),
        ScalarArm("2bit", _scalar_config("2bit", 96, 3, 193), 0.003, 0.1),
    )


def book_specs() -> tuple[BookSpec, ...]:
    """Shared G=8 at both rates, seed book and learned book. Not G=16."""
    return tuple(
        BookSpec(dimension=8, rate=rate, learned=learned)
        for rate in (0.5, 0.75)
        for learned in (False, True)
    )


def vector_books(seed: int) -> tuple[VectorBook, ...]:
    """Four books at one arm seed. Does not build a vector transformer."""
    if type(seed) is not int or seed not in SEEDS:
        raise ValueError("ADR 0023 arm seeds are 0, 1 and 2")
    return tuple(
        VectorBook(spec.dimension, spec.rate, seed, learned=spec.learned) for spec in book_specs()
    )


def init_pack(
    cfg: GPTConfig, *, seed: int, target_bytes: float = TARGET_BYTES
) -> tuple[GPTConfig, dict]:
    """One ADR 0019 d_ff adjustment of a scalar solver shape. Not an S3 repair.

    Same steps as ``experiments/e0_v2.py`` ``host_pack_adjustment``: pack the
    nominal shape, and call ``fill_d_ff`` only when that pack is outside ±1%.
    The record is the nominal pack. ``submitted_d_ff`` changes only when the
    repair is a different in-range shape. A vq config is rejected.
    """
    if cfg.core_fmt == "vq":
        raise ValueError("init-pack does not resize a vq core; nominal_bits includes the book")
    if type(seed) is not int or seed not in SEEDS:
        raise ValueError("ADR 0023 arm seeds are 0, 1 and 2")
    seed_all(seed)
    nbytes = len(pack_sections(TinyGPT(cfg))[0])
    ratio = nbytes * 8 / cfg.nominal_bits()
    record = {
        "nominal_d_ff": cfg.d_ff,
        "init_model_bytes": nbytes,
        "init_fill": nbytes / target_bytes,
        "host_ratio": ratio,
        "submitted_d_ff": cfg.d_ff,
    }
    if admissible({"init": nbytes}, target_bytes)[0]:
        return cfg, record
    repaired = fill_d_ff(cfg, target_bytes * 8, ratio=ratio)
    k = 2 / 3 if cfg.mlp == "swiglu" else 1
    if (
        repaired is None
        or repaired == cfg
        or not 2 * k * cfg.d <= repaired.d_ff <= 6 * k * cfg.d
    ):
        return cfg, record
    record["submitted_d_ff"] = repaired.d_ff
    return repaired, record


def vector_recipe(**_ignored: object) -> None:
    """Refuse a vector width, depth, d_ff, learning rate, or weight decay.

    Copying a scalar shape is not a vector recipe. Searching those fields is
    not a step this ADR authorizes.
    """
    raise ValueError(_VECTOR_SHAPE)


def pilot_tokens(**_ignored: object) -> int:
    """Refuse a token count computed from the scalar arms alone."""
    raise ValueError(
        "ADR 0023 sets T to 20 times the largest arm and does not name the "
        "vector width, depth, d_ff, learning rate, or weight decay"
    )


def f1_separation(sd: float) -> float:
    """max(0.02, 2σ) from ADR 0023 decision 11."""
    if sd < 0:
        raise ValueError("F1 sample sd must be non-negative")
    return max(0.02, 2 * sd)


def f1_holds(vector: MeanBpb, scalar: MeanBpb, sd: float) -> bool:
    """Best vector mean is lower at T and at 2T, and lower at 4T by the separation."""
    return (
        vector.t < scalar.t
        and vector.t2 < scalar.t2
        and scalar.t4 - vector.t4 >= f1_separation(sd)
    )


def f1_abl(learned_bpb: float, seed_bpb: float) -> float:
    """Learned minus seed at the same G and rate.

    The prior is that the seed arm is at least as good. The difference is the
    report. It is not a kill threshold.
    """
    return learned_bpb - seed_bpb
