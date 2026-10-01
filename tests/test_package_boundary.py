"""The core floppylm package must not depend on the Xbox execution package (ADR 0012)."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_core_package_never_imports_floppylm_xbox():
    code = (
        "import importlib, pkgutil, sys, floppylm\n"
        "for m in pkgutil.iter_modules(floppylm.__path__):\n"
        "    importlib.import_module('floppylm.' + m.name)\n"
        "print(sorted(k for k in sys.modules if k.startswith('floppylm_xbox')))\n"
    )
    out = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        env={"PYTHONPATH": str(ROOT / "src")},
        capture_output=True,
        text=True,
        check=True,
    )
    assert out.stdout.strip() == "[]"


def test_frozen_sources_cover_every_execution_package():
    from floppylm.runlog import SOURCE_DIRS

    packages = {p.parent.relative_to(ROOT).as_posix() for p in (ROOT / "src").glob("*/__init__.py")}
    assert packages <= set(SOURCE_DIRS)
