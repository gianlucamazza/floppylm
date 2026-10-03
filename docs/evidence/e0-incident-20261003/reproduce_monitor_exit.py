"""Reproduce termination between observations using the unchanged watch function."""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="incident-monitor-") as name:
        scratch = Path(name)
        state = scratch / "state.json"
        state.write_text(json.dumps({"state": "running", "issues": []}))
        child_code = """
import importlib.util,json,sys
from pathlib import Path
root,scratch=map(Path,sys.argv[1:])
spec=importlib.util.spec_from_file_location('observer',root/'scripts/e0_status.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.report=lambda *a,**k:json.loads((scratch/'state.json').read_text())
m.watch(scratch,interval=30,emit=lambda _:print('observed',flush=True))
"""
        child = subprocess.Popen(
            [sys.executable, "-u", "-c", child_code, str(args.root), name],
            stdout=subprocess.PIPE,
            text=True,
            env=os.environ.copy(),
        )
        try:
            assert child.stdout.readline().strip() == "observed"
            state.write_text(json.dumps({"state": "stopped", "issues": ["fault"]}))
            # The live BindsTo unit sent SIGTERM at campaign exit, before next poll.
            child.terminate()
            child.wait(timeout=10)
            snapshot = json.loads((scratch / "monitor.json").read_text())
            lines = (scratch / "monitor.jsonl").read_text().splitlines()
            assert snapshot["state"] == "running" and len(lines) == 1
            print(
                json.dumps(
                    {
                        "actual_state": "stopped",
                        "last_snapshot": snapshot["state"],
                        "observations": len(lines),
                        "terminal_observation_present": False,
                        "child_returncode": child.returncode,
                        "scope": "actual watch plus SIGTERM; live unit linkage proven by journal",
                    },
                    indent=2,
                )
            )
        finally:
            if child.poll() is None:
                child.terminate()
                child.wait(timeout=10)
            child.stdout.close()


if __name__ == "__main__":
    main()
