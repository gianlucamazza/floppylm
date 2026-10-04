"""Host death and signal tests use real process identity, locks, and child lifetimes."""

import fcntl
import importlib.util
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest

from floppylm import runlog

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments"))
spec = importlib.util.spec_from_file_location(
    "campaign_liveness", ROOT / "experiments/e0_campaign.py"
)
campaign_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(campaign_module)


def test_process_identity_and_live_lock_required(tmp_path):
    runlog.set_status(tmp_path, "running")
    status = json.loads((tmp_path / "status.json").read_text())
    assert status["process_identity"]["pid"] == os.getpid()
    lock_path = tmp_path / "worker.lock"
    with lock_path.open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert runlog.host_liveness(status, lock_path) == "live"
        reused = {**status, "process_identity": {**status["process_identity"], "start_ticks": 0}}
        assert runlog.host_liveness(reused, lock_path) == "identity_mismatch"
        legacy = {"state": "running", "pid": os.getpid()}
        assert runlog.host_liveness(legacy, lock_path) == "unverified"
    assert runlog.host_liveness(status, lock_path) == "lock_abandoned"


def test_flock_fdinfo_owner_is_the_pid_after_the_mode():
    info = (
        "pos:\t0\nflags:\t02100001\nmnt_id:\t163\nino:\t48573\n"
        "lock:\t1: FLOCK  ADVISORY  WRITE 1284565 00:37:48573 0 EOF\n"
    )
    assert runlog._flock_owner(info) == 1284565
    assert runlog._flock_owner("lock:\t2: POSIX  ADVISORY  WRITE 9 00:01:2 0 EOF\n") is None


def test_held_lock_is_live_without_proc_locks_device_identity(tmp_path):
    """Btrfs stat devices do not match /proc/locks. The open descriptor is the proof."""
    parents = [tmp_path]
    workspace = ROOT / "runs"
    if workspace.is_dir():
        parents.append(workspace)
    for parent in parents:
        directory = Path(tempfile.mkdtemp(prefix="lock-identity-", dir=parent))
        try:
            runlog.set_status(directory, "running")
            status = json.loads((directory / "status.json").read_text())
            lock_path = directory / "worker.lock"
            with lock_path.open("w") as lock:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                assert runlog.host_liveness(status, lock_path) == "live"
                assert runlog.legacy_lock_liveness(lock_path) == "owned_or_waiting"
            assert runlog.legacy_lock_liveness(lock_path) == "unowned_verified"
        finally:
            for child in directory.iterdir():
                child.unlink()
            directory.rmdir()


def test_reaped_host_is_dead_despite_running_snapshot(tmp_path):
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    identity = runlog.process_identity(child.pid)
    child.kill()
    child.wait(timeout=5)
    status = {"state": "running", "pid": child.pid, "process_identity": identity}
    assert runlog.host_liveness(status, tmp_path / "worker.lock") == "dead"


def wait_file(path, process):
    deadline = time.monotonic() + 20
    while not path.exists():
        assert process.poll() is None, "host exited before child startup"
        assert time.monotonic() < deadline, "child startup timed out"
        time.sleep(0.02)


@pytest.mark.parametrize("signum", [signal.SIGTERM, signal.SIGINT])
def test_signal_reaps_child_before_releasing_campaign_lock(tmp_path, signum):
    child_script = tmp_path / "child.py"
    child_script.write_text(
        "import os, pathlib, signal, time\n"
        "root = pathlib.Path(__file__).parent\n"
        "def stop(signum, frame):\n"
        "    (root / 'child-stopping').write_text(str(signum))\n"
        "    time.sleep(0.3)\n"
        "    (root / 'child-stopped').write_text('reaped')\n"
        "    raise SystemExit(0)\n"
        "signal.signal(signal.SIGTERM, stop)\n"
        "signal.signal(signal.SIGINT, stop)\n"
        "(root / 'child-ready').write_text(str(os.getpid()))\n"
        "while True: time.sleep(1)\n"
    )
    host_script = tmp_path / "host.py"
    host_script.write_text(
        "import fcntl, pathlib, sys\n"
        f"sys.path.insert(0, {str(ROOT / 'experiments')!r})\n"
        f"sys.path.insert(0, {str(ROOT / 'src')!r})\n"
        "from e0_campaign import Campaign\n"
        "root = pathlib.Path(__file__).parent\n"
        "c = Campaign.__new__(Campaign)\n"
        "c.root, c.path = root, root / 'campaign.json'\n"
        "c.state = {'status': 'running'}\n"
        "c.child = c.stop_signal = None\n"
        "c.launching = c.stopping = False\n"
        "c.lock = (root / 'worker.lock').open('a')\n"
        "fcntl.flock(c.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)\n"
        "c.report = lambda: None\n"
        "c.run = lambda: c.run_command([sys.executable, str(root / 'child.py')])\n"
        "try: c.run_managed()\n"
        "except KeyboardInterrupt: pass\n"
    )
    with (tmp_path / "host.log").open("w") as log:
        host = subprocess.Popen([sys.executable, str(host_script)], stdout=log, stderr=log)
        child_pid = None
        try:
            wait_file(tmp_path / "child-ready", host)
            child_pid = int((tmp_path / "child-ready").read_text())
            host.send_signal(signum)
            wait_file(tmp_path / "child-stopping", host)
            # Repeated operator signals must not tear down checkpoint/cancel cleanup.
            host.send_signal(signum)
            with (tmp_path / "worker.lock").open("r") as lock:
                with pytest.raises(BlockingIOError):
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            assert host.wait(timeout=10) == 0
            assert (tmp_path / "child-stopped").exists()
            with pytest.raises(ProcessLookupError):
                os.kill(child_pid, 0)
            state = json.loads((tmp_path / "campaign.json").read_text())
            assert state["status"] == "stopped"
            assert state["signal"] == signum
            assert state["process_identity"]["pid"] == host.pid
            events = [
                json.loads(line)["event"]
                for line in (tmp_path / "runtime-events.jsonl").read_text().splitlines()
            ]
            assert events == [
                "worker_started",
                "child_stop_requested",
                "child_reaped",
                "worker_stopped",
            ]
            with (tmp_path / "worker.lock").open("r") as lock:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        finally:
            if host.poll() is None:
                host.kill()
                host.wait(timeout=5)
            if child_pid is not None:
                try:
                    os.kill(child_pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass


def test_normal_child_failure_does_not_disable_later_signals(tmp_path):
    campaign = campaign_module.Campaign.__new__(campaign_module.Campaign)
    campaign.root = tmp_path
    campaign.child = campaign.stop_signal = None
    campaign.launching = campaign.stopping = False
    with pytest.raises(subprocess.CalledProcessError):
        campaign.run_command([sys.executable, "-c", "raise SystemExit(3)"])
    assert not campaign.stopping
    with pytest.raises(KeyboardInterrupt):
        campaign.on_signal(signal.SIGTERM, None)


def test_failed_stop_journal_still_signals_and_reaps_child(tmp_path, monkeypatch):
    from unittest.mock import Mock

    campaign = campaign_module.Campaign.__new__(campaign_module.Campaign)
    campaign.root = tmp_path
    campaign.state = {}
    campaign.child = campaign.stop_signal = None
    campaign.launching = campaign.stopping = False
    child = Mock(pid=123, returncode=0)
    child.wait.side_effect = [KeyboardInterrupt(), 0]
    child.poll.return_value = None
    monkeypatch.setattr(campaign_module.subprocess, "Popen", Mock(return_value=child))
    terminate = Mock()
    monkeypatch.setattr(campaign_module.os, "killpg", terminate)
    campaign.save = Mock(side_effect=OSError("disk full"))
    with pytest.raises(OSError, match="disk full"):
        campaign.run_command(["child"])
    terminate.assert_called_once_with(123, signal.SIGTERM)
    assert child.wait.call_count == 2
    assert campaign.child is None


def test_other_process_lock_does_not_validate_recorded_owner(tmp_path):
    runlog.set_status(tmp_path, "running")
    status = json.loads((tmp_path / "status.json").read_text())
    child = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "import fcntl, pathlib, sys, time; "
            "root=pathlib.Path(sys.argv[1]); lock=(root/'worker.lock').open('a'); "
            "fcntl.flock(lock, fcntl.LOCK_EX); (root/'locked').touch(); time.sleep(60)",
            str(tmp_path),
        ]
    )
    try:
        wait_file(tmp_path / "locked", child)
        assert runlog.host_liveness(status, tmp_path / "worker.lock") == "lock_owner_mismatch"
    finally:
        child.terminate()
        child.wait(timeout=5)
