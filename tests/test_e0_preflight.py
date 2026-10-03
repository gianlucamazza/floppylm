"""Readiness must fail closed and never consume campaign or final-test authority."""

import builtins
import fcntl
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def preflight():
    spec = importlib.util.spec_from_file_location("preflight", ROOT / "scripts/e0_preflight.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Console:
    package = "pkg"
    cert_sha256 = "a" * 64

    def __init__(self):
        self.device = {"package": "pkg", "commit": "source", "hardware_gpu": True, "state": "ready"}
        self.record = {"state": "ready", "active_job": None, "pid": 42}
        self.pending = {}
        self.failure = None

    def get(self, name, directory):
        assert (name, directory) == ("device.json", "")
        return json.dumps(self.device)

    def request(self, method, path, **kwargs):
        assert method == "GET" and path == "/api/resourcemanager/processes"
        return {"Processes": [{"PackageFullName": "pkg", "ProcessId": 42}]}

    def live_worker(self, *, commit):
        assert commit == "source"
        if self.failure:
            raise self.failure
        return self.record

    def files(self):
        return self.pending


@pytest.fixture
def inputs(tmp_path, preflight):
    (tmp_path / "src/floppylm").mkdir(parents=True)
    (tmp_path / "src/floppylm/a.py").write_text("# source\n")
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts/e0_preflight.py").write_text("# test preflight\n")
    for args in (
        ["init", "-q"],
        ["add", "src", "scripts"],
        [
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-qm",
            "fixture",
        ],
    ):
        subprocess.run(["git", *args], cwd=tmp_path, check=True)
    data = tmp_path / "data/tinystories"
    data.mkdir(parents=True)
    (data / "train.bin").write_bytes(b"a" * 1024)
    (data / "val.bin").write_bytes(b"b" * (1 << 20))
    (data / "test.bin").write_bytes(b"DO NOT OPEN")
    prepared = {
        s: {
            "bytes": (data / (s + ".bin")).stat().st_size,
            "sha256": preflight.runlog.sha256_file(data / (s + ".bin")),
        }
        for s in ("train", "val")
    }
    proof = tmp_path / "acceptance.json"
    proof.write_text(
        json.dumps(
            {
                "schema": "floppylm.xbox.acceptance.v1",
                "ok": True,
                "kernels": {"ok": True},
                "package": "pkg",
                "commit": "source",
            }
        )
    )
    speed = tmp_path / "benchmark.json"
    speed.write_text(
        json.dumps(
            {
                "purpose": "functional",
                "package": "pkg",
                "commit": "source",
                "tokens_per_second": 10000,
            }
        )
    )
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"data": {"verified": {"prepared": prepared}}}))
    return tmp_path, proof, speed, manifest


def test_read_only_ready_and_local_is_not_console_ready(inputs, preflight, monkeypatch):
    root, *args = inputs
    before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
    original_open, path_open = builtins.open, Path.open

    def guard(path, mode):
        assert Path(path).name != "test.bin"
        assert not any(flag in mode for flag in "wax+")

    def checked_open(path, mode="r", *args, **kwargs):
        guard(path, mode)
        return original_open(path, mode, *args, **kwargs)

    def checked_path_open(path, mode="r", *args, **kwargs):
        guard(path, mode)
        return path_open(path, mode, *args, **kwargs)

    with monkeypatch.context() as m:
        m.setattr(builtins, "open", checked_open)
        m.setattr(Path, "open", checked_path_open)
        report = preflight.report(root, *args, portal=Console())
        assert report["ready"], report
        local = preflight.report(root, *args)
        assert local["local_ok"] and not local["ready"] and not local["xbox_checked"]
    assert before == {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
    assert not (root / "runs").exists()


@pytest.mark.parametrize(
    "failure",
    [
        "source",
        "untracked_source",
        "package",
        "rate",
        "missing_data",
        "corrupt_data",
        "reservation",
        "active_host",
        "busy",
        "heartbeat",
        "transport",
        "pending",
        "device",
        "pid",
    ],
)
def test_preflight_refuses_unsafe_or_unknown_state(inputs, preflight, failure):
    root, proof, speed, manifest = inputs
    portal = Console()
    if failure == "source":
        (root / "src/floppylm/a.py").write_text("# drift")
    elif failure == "untracked_source":
        (root / "src/floppylm/new.py").write_text("# new")
    elif failure in ("package", "rate"):
        value = json.loads(speed.read_text())
        value["package" if failure == "package" else "tokens_per_second"] = (
            "other" if failure == "package" else 0
        )
        speed.write_text(json.dumps(value))
    elif failure == "missing_data":
        (root / "data/tinystories/train.bin").unlink()
    elif failure == "corrupt_data":
        (root / "data/tinystories/train.bin").write_bytes(b"c" * 1024)
    elif failure == "reservation":
        p = root / "docs/evidence/e0-v2/selections/old.test.reservation.json"
        p.parent.mkdir(parents=True)
        p.write_text('{"state":"running"}')
    elif failure == "active_host":
        p = root / "runs/existing/campaign.json"
        p.parent.mkdir(parents=True)
        p.write_text('{"status":"running"}')
    elif failure == "busy":
        portal.record["active_job"] = {"job_id": "science"}
    elif failure == "heartbeat":
        portal.failure = TimeoutError("worker heartbeat did not advance")
    elif failure == "transport":
        portal.failure = OSError("transport unavailable")
    elif failure == "pending":
        portal.pending = {"old.ready": 1}
    elif failure == "device":
        portal.device["commit"] = "other"
    elif failure == "pid":
        portal.record["pid"] = 99
    result = preflight.report(root, proof, speed, manifest, portal=portal)
    assert not result["ready"]
    assert any(not check["ok"] for check in result["checks"].values())


@pytest.mark.parametrize("response", [[], {"Processes": None}, {"Processes": [1]}, "device"])
def test_malformed_portal_responses_produce_failure_json(
    inputs, preflight, monkeypatch, capsys, response
):
    root, proof, speed, manifest = inputs
    portal = Console()
    if response == "device":
        portal.device = []
    else:
        monkeypatch.setattr(portal, "request", lambda *a, **kw: response)
    monkeypatch.setattr(preflight, "ROOT", root)
    monkeypatch.setattr(preflight.Portal, "configured", lambda: portal)
    monkeypatch.setattr(
        preflight.sys,
        "argv",
        [
            "preflight",
            "--xbox",
            "--acceptance",
            str(proof),
            "--benchmark",
            str(speed),
            "--data-manifest",
            str(manifest),
        ],
    )
    assert preflight.main() == 1
    result = json.loads(capsys.readouterr().out)
    assert not result["ready"] and not result["checks"]["xbox"]["ok"]


def test_legacy_campaign_requires_an_existing_unowned_lock(inputs, preflight):
    root, *args = inputs
    folder = root / "runs/legacy"
    folder.mkdir(parents=True)
    manifest = folder / "campaign.json"
    manifest.write_text('{"status":"running"}')
    before = manifest.read_bytes()
    with (folder / "worker.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert not preflight.report(root, *args, portal=Console())["ready"]
    result = preflight.report(root, *args, portal=Console())
    assert result["ready"], result
    evidence = result["checks"]["campaign_hosts"]["evidence"]
    assert evidence[0]["liveness"] == "unowned_legacy_lock"
    assert manifest.read_bytes() == before


def test_protocol_copy_and_grid_match_accepted_defaults(preflight):
    p = preflight.protocol_spec()
    q = preflight.protocol_spec()
    historical = json.loads(
        (
            ROOT / "docs/evidence/e0-v2/campaigns/e0-20261002T191632Z-ca781f/campaign.json"
        ).read_text()
    )
    assert q == historical["protocol"]
    p["paired_seeds"].clear()
    assert q["paired_seeds"] == list(range(5))
    base = preflight.GPTConfig(d=96, n_layers=3, n_heads=6, ctx=256)
    for scale in q["scale_order"]:
        for mlp in q["mlp_order"]:
            for fmt in ("ternary", "2bit"):
                cfg = preflight.replace(base, scale_policy=scale, mlp=mlp, core_fmt=fmt)
                assert preflight.grid_configs(cfg, 11_000_000 / 16, q) == preflight.shapes.grid(
                    cfg, 11_000_000 / 16
                )
