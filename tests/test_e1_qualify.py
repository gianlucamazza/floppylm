"""Qualification must reject unbound or undersized train inputs before writing."""

import hashlib
import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "e1_qualify", Path(__file__).resolve().parents[1] / "scripts/e1_qualify.py"
)
QUALIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(QUALIFY)


def test_reject_unfrozen_train_before_output(tmp_path):
    train = tmp_path / "train.bin"
    train.write_bytes(b"train only")
    out = tmp_path / "qualification"
    with pytest.raises(RuntimeError, match="differs from frozen"):
        QUALIFY.qualify(train, "0" * 64, out, 1)
    assert not out.exists()


def test_require_declared_train_prefix_before_output(tmp_path):
    train = tmp_path / "train.bin"
    train.write_bytes(b"train only")
    out = tmp_path / "qualification"
    with pytest.raises(RuntimeError, match="2 MiB"):
        QUALIFY.qualify(train, hashlib.sha256(train.read_bytes()).hexdigest(), out, 1)
    assert not out.exists()
