"""The recovery harness accepts the recorded interrupt return, not only a raise."""

import importlib.util
from pathlib import Path

import pytest


@pytest.fixture
def recovery():
    path = Path(__file__).resolve().parents[1] / "experiments/xbox_recovery_acceptance.py"
    spec = importlib.util.spec_from_file_location("xbox_recovery_acceptance", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_interrupted_return_is_the_runner_proof(recovery):
    recovery.require_runner_interruption(130, "interrupted")


@pytest.mark.parametrize(
    ("code", "status"),
    [(0, "completed"), (0, "interrupted"), (130, "failed"), (130, "running"), (1, "interrupted")],
)
def test_other_runner_results_are_not_an_interruption(recovery, code, status):
    with pytest.raises(RuntimeError, match="runner interruption did not occur"):
        recovery.require_runner_interruption(code, status)
