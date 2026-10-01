"""Shared fixtures. Tool requirements fail loudly instead of skipping silently."""

import os
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
NATIVE_BINARY = Path(
    os.environ.get(
        "XGPU_E0_BINARY",
        ROOT.parents[1] / "tooling/xbox-gpu-training/build/xgpu_e0_train",
    )
)


@pytest.fixture(scope="session")
def native_binary() -> Path:
    """The xbox-gpu-training CLI, run in --reference mode on the host CPU."""
    if not NATIVE_BINARY.is_file():
        pytest.fail(
            f"native binary not found at {NATIVE_BINARY}: build xgpu_e0_train in "
            "xbox-gpu-training (cmake --build build --target xgpu_e0_train), set "
            "XGPU_E0_BINARY, or deselect these tests with -m 'not native'"
        )
    return NATIVE_BINARY


@pytest.fixture(scope="session")
def c_compiler() -> str:
    compiler = shutil.which("cc")
    if compiler is None:
        pytest.fail("a C compiler (cc) is required by the generator interoperability test")
    return compiler
