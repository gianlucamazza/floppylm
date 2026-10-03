"""Reproduce lock observations on tmpfs and Btrfs using disposable processes/files."""

import argparse
import fcntl
import importlib.util
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
    sys.path.insert(0, str(args.root / "src"))
    from floppylm import runlog

    spec = importlib.util.spec_from_file_location(
        "preflight", args.root / "scripts/e0_preflight.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    results = []
    for parent in (Path("/tmp"), args.root / "runs"):
        with tempfile.TemporaryDirectory(prefix="incident-lock-", dir=parent) as scratch:
            lock_path = Path(scratch) / "worker.lock"
            child = subprocess.Popen(
                [
                    sys.executable,
                    "-c",
                    "import fcntl,sys; f=open(sys.argv[1],'w'); "
                    "fcntl.flock(f,fcntl.LOCK_EX); print('ready',flush=True); "
                    "sys.stdin.read()",
                    str(lock_path),
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True,
            )
            try:
                assert child.stdout.readline().strip() == "ready"
                st = lock_path.stat()
                status = {
                    "state": "running",
                    "pid": child.pid,
                    "process_identity": runlog.process_identity(child.pid),
                }
                fd_records = []
                for fd in Path(f"/proc/{child.pid}/fd").iterdir():
                    if fd.resolve() == lock_path.resolve():
                        info = Path(f"/proc/{child.pid}/fdinfo/{fd.name}").read_text()
                        assert f"WRITE {child.pid} " in info
                        fd_records.append(info)
                assert fd_records
                with lock_path.open() as contender:
                    try:
                        fcntl.flock(contender, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    except BlockingIOError:
                        contention = True
                    else:
                        raise AssertionError("fixture lock was not held")
                wrong = {
                    "state": "running",
                    "pid": os.getpid(),
                    "process_identity": runlog.process_identity(),
                }
                row = {
                    "filesystem": subprocess.check_output(
                        ["stat", "-f", "-c", "%T", scratch], text=True
                    ).strip(),
                    "stat_device": [os.major(st.st_dev), os.minor(st.st_dev)],
                    "inode": st.st_ino,
                    "kernel_fdinfo": fd_records,
                    "independent_contention_proves_held": contention,
                    "held_current": runlog.host_liveness(status, lock_path),
                    "held_legacy": module.legacy_lock_liveness(lock_path),
                    "wrong_owner": runlog.host_liveness(wrong, lock_path),
                    "identity_mismatch": runlog.host_liveness(
                        {**status, "process_identity": {}}, lock_path
                    ),
                }
            finally:
                child.stdin.close()
                child.wait(timeout=10)
                child.stdout.close()
            row["dead_owner"] = runlog.host_liveness(status, lock_path)
            row["released_current"] = runlog.host_liveness(wrong, lock_path)
            row["released_legacy"] = module.legacy_lock_liveness(lock_path)
            results.append(row)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
