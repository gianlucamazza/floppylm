import pytest

from floppylm.parity import admissible, paired_sigma


def test_rejects_pair_inside_target_band_but_apart() -> None:
    ok, reasons = admissible({"a": 9920, "b": 10080}, 10_000)  # -0.8% and +0.8%
    assert not ok and any("spread" in r for r in reasons)


def test_accepts_close_pair_and_rejects_far_from_target() -> None:
    assert admissible({"a": 9990, "b": 10040}, 10_000)[0]
    ok, reasons = admissible({"a": 10150}, 10_000)
    assert not ok and "target" in reasons[0]


def test_paired_sigma_uses_differences() -> None:
    r = paired_sigma({0: 2.0, 1: 2.2, 2: 2.4}, {0: 1.9, 1: 2.1, 2: 2.3})
    assert r["n"] == 3 and abs(r["mean"] - 0.1) < 1e-12 and r["sd"] < 1e-12
    with pytest.raises(ValueError):
        paired_sigma({0: 1.0, 1: 2.0}, {0: 1.0, 2: 2.0})
    with pytest.raises(ValueError):
        paired_sigma({0: 1.0}, {0: 1.0})
