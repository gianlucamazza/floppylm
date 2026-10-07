import pytest

from floppylm.parity import admissible, paired_sigma


def test_accepts_pair_inside_the_shared_target_window() -> None:
    # -0.8% and +0.8% of the target. Their mutual spread is 1.61%.
    assert admissible({"a": 9920, "b": 10080}, 10_000)[0]
    # Published c58a86 4T endpoints, both inside ±1% of 85937.5.
    assert admissible({"small": 85098, "large": 85982}, 85937.5)[0]


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
