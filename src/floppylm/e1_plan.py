"""Specified 1/16 host plan from ADR 0023 and the ADR 0024 shape rule.

Materializes the two stored scalar arms, their ADR 0019 init-pack, the four
shared G=8 books, and the one seed-0 vector shape per book. Computes the F1
separation. Does not train, does not freeze a selection, and does not open
the test split.
"""

from __future__ import annotations

import math
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
# Copied from the stored 2-bit arm. The vector scales are that row8log codec.
VECTOR_LR = 0.003
VECTOR_WD = 0.1
_HAND_SHAPE = (
    "ADR 0024 names one seed-0 shape per G=8 book by the packed-byte solver; "
    "a caller-supplied width, depth, d_ff, learning rate, or weight decay is not a shape"
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


def ff_bounds(d: int) -> tuple[int, int]:
    """Integer d_ff inside the E0 SwiGLU interval 2·(2/3)·d … 6·(2/3)·d."""
    if type(d) is not int or d < 1:
        raise ValueError("width must be a positive int")
    return (4 * d + 2) // 3, 4 * d


def vector_config(d: int, n_layers: int, d_ff: int) -> GPTConfig:
    """One vector core in the stored scalar family. The book is not a field."""
    if d % 16:
        raise ValueError("ADR 0024 widths are multiples of 16 so n_heads = d/16")
    return GPTConfig(
        vocab=256,
        d=d,
        n_layers=n_layers,
        n_heads=d // 16,
        d_ff=d_ff,
        mlp="swiglu",
        core_fmt="vq",
        emb_fmt="4bit",
        scale_policy="row8log",
        delta=0.5,
        qk_norm=False,
        ctx=256,
    )


def nominal_payload_bytes(d: int, n_layers: int, d_ff: int, spec: BookSpec) -> float:
    """Model nominal bytes for a vector shape. Not the FLP2 size parity reads."""
    bits = int(spec.dimension * spec.rate)

    def core(rows: int, cols: int) -> int:
        groups = math.ceil(cols / spec.dimension)
        return rows * groups * bits + 16 + 8 * rows

    emb = 256 * d * 4 + 16 + 8 * 256
    body = n_layers * (core(3 * d, d) + core(d, d) + core(2 * d_ff, d) + core(d, d_ff))
    norms = (2 * n_layers + 1) * 16 * d
    return (8 * spec.shared_bytes + emb + body + norms) / 8


@dataclass(frozen=True)
class SolvedShape:
    """One seed-0 vector arm. ``d_ff`` is the init pack chosen for that book."""

    d: int
    n_layers: int
    d_ff: int
    rate: float
    learned: bool
    init_bytes: int
    stored_params: int

    def rank(self) -> tuple[float, int, int, int, int]:
        distance = abs(self.init_bytes - TARGET_BYTES)
        return (distance, self.stored_params, self.d, self.n_layers, self.d_ff)


def choose_shape(candidates: list[SolvedShape]) -> SolvedShape | None:
    """Closest packed file, then fewer stored parameters, then the smaller grid point."""
    if not candidates:
        return None
    return min(candidates, key=lambda shape: shape.rank())


def _pack_shape(cfg: GPTConfig, book: VectorBook) -> tuple[int, int]:
    seed_all(0)
    model = TinyGPT(cfg, book)
    return len(pack_sections(model)[0]), model.stored_params()


def _best_d_ff(d: int, n_layers: int, spec: BookSpec, book: VectorBook) -> SolvedShape | None:
    """Seed-0 d_ff in the SwiGLU interval whose pack is closest to the target.

    Pack size increases with d_ff on this init. The two integers around the
    crossing are the only closest candidates. A local decrease scans the interval.
    """
    lo, hi = ff_bounds(d)
    cache: dict[int, tuple[int, int]] = {}

    def measure(d_ff: int) -> tuple[int, int]:
        if d_ff not in cache:
            cache[d_ff] = _pack_shape(vector_config(d, n_layers, d_ff), book)
        return cache[d_ff]

    lo_bytes = measure(lo)[0]
    hi_bytes = measure(hi)[0]
    if hi_bytes < lo_bytes:
        scan = range(lo, hi + 1)
    else:
        left, right = lo, hi
        while left < right:
            mid = (left + right) // 2
            if measure(mid)[0] < TARGET_BYTES:
                left = mid + 1
            else:
                right = mid
        if left > lo and measure(left)[0] < measure(left - 1)[0]:
            scan = range(lo, hi + 1)
        else:
            scan = range(max(lo, left - 1), min(hi, left + 1) + 1)
    found: list[SolvedShape] = []
    for d_ff in scan:
        nbytes, params = measure(d_ff)
        if not admissible({spec.rate: nbytes}, TARGET_BYTES)[0]:
            continue
        found.append(
            SolvedShape(d, n_layers, d_ff, spec.rate, spec.learned, nbytes, params)
        )
    return choose_shape(found)


def solve_vector_shapes() -> tuple[SolvedShape | None, ...]:
    """One seed-0 shape per G=8 book, or None where the grid has no admissible pack.

    Order is book_specs(): rate 0.5 fixed, 0.5 learned, 0.75 fixed, 0.75 learned.
    Does not train and does not read a validation loss.
    """
    found: list[SolvedShape | None] = []
    for spec in book_specs():
        book = VectorBook(spec.dimension, spec.rate, 0, learned=spec.learned)
        best: SolvedShape | None = None
        for d in range(64, 257, 16):
            for n_layers in range(1, 17):
                shape = _best_d_ff(d, n_layers, spec, book)
                if shape is not None and (best is None or shape.rank() < best.rank()):
                    best = shape
        found.append(best)
    return tuple(found)


def vector_recipe(**_ignored: object) -> None:
    """Refuse a hand-specified vector width, depth, d_ff, learning rate, or weight decay."""
    raise ValueError(_HAND_SHAPE)


def pilot_tokens(shapes: tuple[SolvedShape, ...], scalar_params: tuple[int, ...]) -> int:
    """T from the seed-0 submitted shapes. The same count for every seed."""
    if len(shapes) != 4 or any(shape is None for shape in shapes):
        raise ValueError("pilot T needs one admissible shape for each of the four G=8 books")
    if len(scalar_params) != 2 or any(type(n) is not int or n < 1 for n in scalar_params):
        raise ValueError("pilot T needs the two scalar seed-0 stored-parameter counts")
    largest = max([*(shape.stored_params for shape in shapes), *scalar_params])
    return TOKENS_PER_STORED_PARAM * largest


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
