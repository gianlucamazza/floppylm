"""The CPU qualification profile must reject altered inputs before training."""

import importlib.util
import json
import sys
from pathlib import Path

import pytest
import torch

from floppylm import runlog
from floppylm.model import GPTConfig, TinyGPT
from floppylm.train import TrainSpec
from floppylm.xbox import prepare_job

ROOT = Path(__file__).resolve().parents[1]
module_spec = importlib.util.spec_from_file_location(
    "e1_cpu_profile", ROOT / "scripts/e1_cpu_profile.py"
)
profile = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(profile)


@pytest.fixture
def job(tmp_path):
    corpus = tmp_path / "corpus.bin"
    corpus.write_bytes(b"the cat sat. " * 16)
    torch.manual_seed(19)
    model = TinyGPT(GPTConfig(d=8, n_heads=2, n_layers=1, d_ff=16, ctx=8))
    root = tmp_path / "job"
    prepare_job(root, model, corpus, TrainSpec(tokens=32, batch=2), "functional-profile")
    return root


def invoke(job, out, monkeypatch, repeats="1"):
    monkeypatch.setattr(
        sys,
        "argv",
        ["profile", "--job", str(job), "--out", str(out), "--repeats", repeats, "--threads", "1"],
    )
    return profile.main()


def test_changed_data_rejected_before_output_creation(job, tmp_path, monkeypatch):
    (job / "train.bin").write_bytes(b"changed")
    out = tmp_path / "out"
    with pytest.raises(RuntimeError, match="asset differs: data"):
        invoke(job, out, monkeypatch)
    assert not out.exists()


def test_rehashed_wrong_indices_rejected_before_training(job, tmp_path, monkeypatch):
    path = job / "indices.bin"
    data = bytearray(path.read_bytes())
    data[:8] = (0).to_bytes(8, "little")
    path.write_bytes(data)
    manifest_path = job / "job.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["indices"]["sha256"] = runlog.sha256_file(path)
    runlog.write_json(manifest_path, manifest)
    out = tmp_path / "out"
    with pytest.raises(RuntimeError, match="ordered sample indices differ"):
        invoke(job, out, monkeypatch)
    assert not out.exists()


def test_actual_cpu_repeats_publish_equal_artifacts(job, tmp_path, monkeypatch):
    out = tmp_path / "out"
    assert invoke(job, out, monkeypatch, repeats="2") == 0
    summary = json.loads((out / "summary.json").read_text())
    assert summary["purpose"] == "functional"
    assert summary["repeat_artifacts_exact"]
    assert len(summary["attempts"][0]["branches"]) == 3
    assert summary["attempts"][0]["branches"] == summary["attempts"][1]["branches"]
    assert all(a["tokens"] == 160 for a in summary["attempts"])
