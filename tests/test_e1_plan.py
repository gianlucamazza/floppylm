"""Host plan for the specified 1/16 arms. Does not train."""

import importlib.util
from dataclasses import replace
from pathlib import Path

import pytest

from floppylm.e1_plan import (
    SEEDS,
    SELECTION_SHA256,
    TARGET_BYTES,
    TOKENS_PER_STORED_PARAM,
    VECTOR_LR,
    VECTOR_WD,
    BookSpec,
    MeanBpb,
    SolvedShape,
    book_specs,
    choose_shape,
    f1_abl,
    f1_holds,
    f1_separation,
    ff_bounds,
    init_pack,
    nominal_payload_bytes,
    pilot_tokens,
    scalar_arms,
    vector_books,
    vector_config,
    vector_recipe,
)
from floppylm.model import TinyGPT
from floppylm.pack import pack, pack_sections
from floppylm.parity import admissible
from floppylm.seed import seed_all
from floppylm.vq import VectorBook

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("e0_v2_e1_plan", ROOT / "experiments/e0_v2.py")
_e0 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_e0)


def test_plan_constants_copy_the_accepted_protocol():
    assert SEEDS == (0, 1, 2)
    assert TARGET_BYTES == 85937.5
    assert TOKENS_PER_STORED_PARAM == 20
    assert SELECTION_SHA256 == (
        "de80fff08e750702784e6efbcb583ca86de566965207212c1c6531822a05bbe4"
    )
    assert (VECTOR_LR, VECTOR_WD) == (0.003, 0.1)
    arms = {arm.name: arm for arm in scalar_arms()}
    ternary, two = arms["ternary"], arms["2bit"]
    assert (ternary.lr, ternary.wd) == (0.01, 0.1)
    assert (two.lr, two.wd) == (0.003, 0.1)
    assert (ternary.nominal.d, ternary.nominal.n_layers, ternary.nominal.d_ff) == (80, 4, 262)
    assert (two.nominal.d, two.nominal.n_layers, two.nominal.d_ff) == (96, 3, 193)
    for arm in (ternary, two):
        cfg = arm.nominal
        assert cfg.n_heads == cfg.d // 16
        assert (cfg.mlp, cfg.emb_fmt, cfg.scale_policy, cfg.delta, cfg.qk_norm, cfg.ctx) == (
            "swiglu",
            "4bit",
            "row8log",
            0.5,
            False,
            256,
        )


def test_seed0_init_pack_locks_the_measured_scalar_bytes():
    arms = {arm.name: arm for arm in scalar_arms()}
    ternary, record = init_pack(arms["ternary"].nominal, seed=0)
    assert ternary == arms["ternary"].nominal
    assert record["submitted_d_ff"] == 262
    assert record["init_model_bytes"] == 85223
    seed_all(0)
    ternary_bytes = len(pack(TinyGPT(ternary)))
    assert ternary_bytes == 85223
    ok, reasons = admissible({"ternary": ternary_bytes}, TARGET_BYTES)
    assert ok, reasons

    nominal = arms["2bit"].nominal
    two, record = init_pack(nominal, seed=0)
    assert nominal.d_ff == 193
    assert record["nominal_d_ff"] == 193
    assert record["init_model_bytes"] == 83274
    nominal_ok, _ = admissible({"nominal": record["init_model_bytes"]}, TARGET_BYTES)
    assert not nominal_ok
    assert two == replace(nominal, d_ff=205)
    assert record["submitted_d_ff"] == 205
    seed_all(0)
    submitted = len(pack(TinyGPT(two)))
    assert submitted == 85878
    ok, reasons = admissible({"2bit": submitted}, TARGET_BYTES)
    assert ok, reasons


def test_init_pack_matches_the_e0_host_adjustment():
    for arm in scalar_arms():
        seed_all(0)
        expected_cfg, expected = _e0.host_pack_adjustment(arm.nominal, TARGET_BYTES)
        got_cfg, got = init_pack(arm.nominal, seed=0)
        assert got_cfg == expected_cfg
        assert got["init_model_bytes"] == expected["init_model_bytes"]
        assert got["init_fill"] == expected["init_fill"]
        assert got["host_ratio"] == expected["host_ratio"]
        assert got["submitted_d_ff"] == expected["submitted_d_ff"]


def test_four_g8_books_lock_header_and_entry_bytes():
    specs = book_specs()
    assert [(s.dimension, s.rate, s.learned) for s in specs] == [
        (8, 0.5, False),
        (8, 0.5, True),
        (8, 0.75, False),
        (8, 0.75, True),
    ]
    assert [s.shared_bytes for s in specs] == [16, 272, 16, 1040]
    for seed in SEEDS:
        books = vector_books(seed)
        assert [len(book.to_bytes()) for book in books] == [16, 272, 16, 1040]
        assert [book.seed for book in books] == [seed, seed, seed, seed]


def test_g16_needs_an_adr_edit_before_the_first_attempt():
    with pytest.raises(ValueError, match="edit of that ADR"):
        BookSpec(16, 0.5, False)


def test_shape_rule_orders_candidates_and_matches_nominal_bits():
    assert ff_bounds(96) == (128, 384)
    assert ff_bounds(80) == (107, 320)
    far = SolvedShape(64, 2, 100, 0.5, False, 87000, 10)
    close_big = SolvedShape(128, 4, 200, 0.5, False, 85940, 500)
    close_small = SolvedShape(96, 3, 150, 0.5, False, 85940, 400)
    wider = SolvedShape(112, 2, 150, 0.5, False, 85940, 400)
    assert choose_shape([far, close_big, close_small, wider]) == close_small
    assert choose_shape([]) is None
    spec = book_specs()[0]
    cfg = vector_config(64, 1, ff_bounds(64)[0])
    book = VectorBook(spec.dimension, spec.rate, 0, learned=spec.learned)
    seed_all(0)
    model = TinyGPT(cfg, book)
    assert nominal_payload_bytes(64, 1, cfg.d_ff, spec) == model.nominal_bits() / 8


def test_seed0_fixed_rate_05_shape_repacks():
    """Closed book from the 2026-10-11 solver. Does not walk the grid."""
    spec = book_specs()[0]
    assert (spec.rate, spec.learned) == (0.5, False)
    book = VectorBook(spec.dimension, spec.rate, 0, learned=False)
    cfg = vector_config(80, 12, 247)
    assert ff_bounds(80)[0] <= cfg.d_ff <= ff_bounds(80)[1]
    seed_all(0)
    model = TinyGPT(cfg, book)
    assert len(pack_sections(model)[0]) == 85934
    assert model.stored_params() == 1_039_040
    ok, reasons = admissible({spec.rate: 85934}, TARGET_BYTES)
    assert ok, reasons
    for d_ff, nbytes in ((246, 85785), (248, 86031)):
        seed_all(0)
        neighbor = TinyGPT(vector_config(80, 12, d_ff), book)
        packed = len(pack_sections(neighbor)[0])
        assert packed == nbytes
        assert abs(packed - TARGET_BYTES) > abs(85934 - TARGET_BYTES)


def test_seed0_learned_rate_05_shape_repacks():
    """Closed book from the 2026-10-11 solver. Does not walk the grid."""
    spec = book_specs()[1]
    assert (spec.rate, spec.learned) == (0.5, True)
    book = VectorBook(spec.dimension, spec.rate, 0, learned=True)
    cfg = vector_config(256, 1, 801)
    assert ff_bounds(256)[0] <= cfg.d_ff <= ff_bounds(256)[1]
    seed_all(0)
    model = TinyGPT(cfg, book)
    assert len(pack_sections(model)[0]) == 85935
    assert model.stored_params() == 942_976
    ok, reasons = admissible({spec.rate: 85935}, TARGET_BYTES)
    assert ok, reasons
    for d_ff, nbytes in ((800, 85809), (802, 85972)):
        seed_all(0)
        neighbor = TinyGPT(vector_config(256, 1, d_ff), book)
        packed = len(pack_sections(neighbor)[0])
        assert packed == nbytes
        assert abs(packed - TARGET_BYTES) > abs(85935 - TARGET_BYTES)


def test_vector_recipe_rejects_a_hand_specified_shape():
    with pytest.raises(ValueError, match="caller-supplied width"):
        vector_recipe(d=80, n_layers=4, d_ff=320, lr=0.01, wd=0.1)
    with pytest.raises(ValueError, match="four G=8 books"):
        pilot_tokens((), (1, 1))
    with pytest.raises(ValueError, match="vq core"):
        init_pack(replace(scalar_arms()[0].nominal, core_fmt="vq"), seed=0)


def test_copied_scalar_shapes_are_not_an_eligible_vector_pack():
    for arm in scalar_arms():
        cfg = replace(arm.nominal, core_fmt="vq")
        with pytest.raises(ValueError, match="shared book"):
            cfg.nominal_bits()
        for spec in book_specs():
            book = VectorBook(spec.dimension, spec.rate, 0, learned=spec.learned)
            seed_all(0)
            nbytes = len(pack(TinyGPT(cfg, book)))
            ok, _reasons = admissible({arm.name: nbytes}, TARGET_BYTES)
            assert not ok, (
                f"{arm.name} rate {spec.rate} learned {spec.learned} packed {nbytes} B"
            )


def test_f1_holds_only_for_the_named_separation():
    assert f1_separation(0.0) == 0.02
    assert f1_separation(0.005) == 0.02
    assert f1_separation(0.02) == 0.04
    with pytest.raises(ValueError, match="non-negative"):
        f1_separation(-0.01)
    scalar = MeanBpb(1.20, 1.10, 1.00)
    assert f1_holds(MeanBpb(1.10, 1.00, 0.97), scalar, sd=0.005)
    assert f1_holds(MeanBpb(1.10, 1.00, 0.96), scalar, sd=0.02)
    assert not f1_holds(MeanBpb(1.10, 1.00, 0.981), scalar, sd=0.005)
    assert not f1_holds(MeanBpb(1.20, 1.00, 0.90), scalar, sd=0.005)
    assert not f1_holds(MeanBpb(1.10, 1.10, 0.90), scalar, sd=0.005)
    assert not f1_holds(MeanBpb(1.10, 1.00, 0.97), scalar, sd=0.02)


def test_f1_abl_reports_learned_minus_seed():
    assert f1_abl(1.30, 1.20) == pytest.approx(0.10)
    assert f1_abl(1.20, 1.30) == pytest.approx(-0.10)
