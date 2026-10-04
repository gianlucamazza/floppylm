"""Run bookkeeping: unique ids, exclusive directories, atomic writes, status, manifests."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import platform
import subprocess
import uuid
from pathlib import Path

import numpy as np
import torch

STATES = ("running", "completed", "failed", "interrupted")


def now() -> str:
    return dt.datetime.now(dt.UTC).isoformat(timespec="seconds")


def new_run_id(tag: str) -> str:
    return f"{tag}-{dt.datetime.now(dt.UTC):%Y%m%dT%H%M%SZ}-{uuid.uuid4().hex[:6]}"


def make_exclusive_dir(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.mkdir(exist_ok=False)  # never reuse a run directory
    return path


def write_atomic(path: Path, data: bytes | str) -> None:
    tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex[:8]}.tmp")
    try:
        with tmp.open("wb") as file:
            file.write(data.encode() if isinstance(data, str) else data)
            file.flush()
            os.fsync(file.fileno())
        os.replace(tmp, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        tmp.unlink(missing_ok=True)


def write_json(path: Path, obj: dict) -> None:
    write_atomic(path, json.dumps(obj, indent=1, sort_keys=True, default=str) + "\n")


def process_identity(pid: int | None = None) -> dict | None:
    """Bind Linux PID to its boot and start tick; a reused PID is a different owner."""
    pid = os.getpid() if pid is None else pid
    if type(pid) is not int or pid <= 0:
        return None
    try:
        fields = Path(f"/proc/{pid}/stat").read_text().rpartition(")")[2].split()
        if fields[0] == "Z":
            return None
        return {
            "pid": pid,
            "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
            "start_ticks": int(fields[19]),
        }
    except (OSError, ValueError, IndexError):
        return None


def _flock_owner(fdinfo: str) -> int | None:
    """Owner pid from an flock fdinfo line. The kernel device field is not an identity.

    Linux prints ``lock:\\t<id>: FLOCK  ADVISORY  WRITE <pid> <dev> ...``.
    ``split()`` therefore puts the id in its own field. The device after the pid
    is not compared.
    """
    for line in fdinfo.splitlines():
        fields = line.split()
        if not fields or not fields[0].startswith("lock:"):
            continue
        try:
            kind = fields.index("FLOCK")
        except ValueError:
            continue
        if len(fields) <= kind + 3 or fields[kind + 2] != "WRITE":
            continue
        try:
            return int(fields[kind + 3])
        except ValueError:
            return None
    return None


def _pid_holds_flock(pid: int, target: Path) -> bool | None:
    """True when this pid's open descriptor holds the flock. None if that pid cannot be read."""
    fd_dir = Path(f"/proc/{pid}/fd")
    try:
        descriptors = list(fd_dir.iterdir())
    except FileNotFoundError:
        return False
    except OSError:
        return None
    for descriptor in descriptors:
        try:
            if descriptor.resolve() != target:
                continue
            info = Path(f"/proc/{pid}/fdinfo/{descriptor.name}").read_text()
        except OSError:
            continue
        if _flock_owner(info) == pid:
            return True
    return False


def lock_holders(lock_path: Path) -> tuple[str, list[int]]:
    """Prove holders from the descriptor they have open.

    Btrfs reports a different device in stat than in /proc/locks for the same file.
    Matching those devices, or matching an inode alone, is not identity. A same-user
    process whose descriptors cannot be read makes the result unknown. Absence of a
    readable holder is free only when every same-user process was readable.
    """
    try:
        target = lock_path.resolve()
    except OSError:
        return "unknown", []
    if not target.exists():
        return "unknown", []
    holders: list[int] = []
    unknown = False
    try:
        entries = list(Path("/proc").iterdir())
    except OSError:
        return "unknown", []
    for entry in entries:
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        try:
            if entry.stat().st_uid != os.getuid():
                continue
        except OSError:
            unknown = True
            continue
        held = _pid_holds_flock(pid, target)
        if held is None:
            unknown = True
        elif held:
            holders.append(pid)
    if holders:
        return "held", holders
    if unknown:
        return "unknown", []
    return "free", []


def legacy_lock_liveness(lock_path: Path) -> str:
    """Pre-PID campaigns. Free means the kernel granted the lock, not a /proc scan.

    ssh-agent and similar same-user processes hide their descriptors. A scan that
    cannot read them must not be called free, and must not block a lock the kernel
    has already granted. A contended lock whose holder cannot be read stays unknown.
    """
    if not lock_path.exists():
        return "unknown"
    try:
        import fcntl

        with lock_path.open("r") as file:
            try:
                fcntl.flock(file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                state, _holders = lock_holders(lock_path)
                return "owned_or_waiting" if state == "held" else "unknown"
            fcntl.flock(file, fcntl.LOCK_UN)
        return "unowned_verified"
    except OSError:
        return "unknown"


def host_liveness(status: dict, lock_path: Path) -> str:
    """A snapshot's timestamp is not a heartbeat. Verify process identity and lock."""
    if status.get("state") != "running":
        return status.get("state", "unknown")
    pid = status.get("pid")
    if type(pid) is not int or pid <= 0:
        return "unknown"
    actual = process_identity(pid)
    if actual is None:
        return "dead"
    expected = status.get("process_identity")
    if expected is None:
        return "unverified"
    if actual != expected:
        return "identity_mismatch"
    try:
        import fcntl

        with lock_path.open("r") as file:
            try:
                fcntl.flock(file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                state, holders = lock_holders(lock_path)
                if pid in holders:
                    return "live"
                if state == "held":
                    return "lock_owner_mismatch"
                return "lock_unverified"
            fcntl.flock(file, fcntl.LOCK_UN)
        return "lock_abandoned"
    except OSError:
        return "lock_unavailable"


def set_status(run_dir: Path, state: str, **extra) -> None:
    assert state in STATES
    if state == "running":
        extra.setdefault("pid", os.getpid())
        extra["process_identity"] = process_identity(extra["pid"])
    write_json(run_dir / "status.json", {"state": state, "updated": now(), **extra})


def sha256_file(path: Path, chunk: int = 1 << 24) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while b := f.read(chunk):
            h.update(b)
    return h.hexdigest()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def git_state(root: Path) -> dict:
    def run(*args: str) -> str:
        r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)
        return r.stdout.strip() if r.returncode == 0 else ""

    return {
        "commit": run("rev-parse", "HEAD") or None,
        "dirty": bool(run("status", "--porcelain", "--untracked-files=no")),
    }


# Everything that defines an E0 run; a campaign freezes these hashes before its first result.
SOURCE_DIRS = ("src/floppylm", "src/floppylm_xbox", "experiments")


def source_files(root: Path) -> dict[str, str]:
    files = [p for d in SOURCE_DIRS for p in sorted((root / d).glob("*.py"))]
    return {str(p.relative_to(root)): sha256_file(p) for p in files}


def sources(root: Path) -> dict:
    return {"git": git_state(root), "files": source_files(root)}


def environment(threads: int) -> dict:
    cpu = ""
    try:
        cpu = next(
            line.split(":", 1)[1].strip()
            for line in open("/proc/cpuinfo")
            if line.startswith("model name")
        )
    except (OSError, StopIteration):
        pass
    return {
        "python": platform.python_version(),
        "torch": torch.__version__,
        "numpy": np.__version__,
        "platform": platform.platform(),
        "cpu": cpu,
        "torch_threads": threads,
    }
