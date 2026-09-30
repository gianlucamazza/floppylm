import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_e0_lite_without_flags_exits_2() -> None:
    r = subprocess.run(
        [sys.executable, str(ROOT / "experiments" / "e0_lite.py")],
        check=False,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 2
    assert "usage" in (r.stdout + r.stderr).lower()
