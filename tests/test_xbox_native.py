"""Independent native gates; no Windows/GPU result is inferred from these tests."""

import json
import os
import subprocess

import numpy as np
import pytest
import torch

from floppylm.model import GPTConfig, TinyGPT
from floppylm.seed import seed_all
from floppylm.train import TrainSpec
from floppylm_xbox.jobs import (
    compare,
    descriptor,
    prepare_job,
    restore_tensors,
    tensors,
    verify_optimizer,
)


def test_mixed_gate_rejects_nonfinite_shape_and_outlier():
    assert compare([1.00005], [1.0])["ok"]
    assert not compare([0.001], [0.0])["ok"]
    assert not compare([float("nan")], [0.0])["ok"]
    assert not compare([0.0, 0.0], [0.0])["ok"]


def test_tensor_exchange_preserves_order_and_values():
    seed_all(19)
    model = TinyGPT(GPTConfig(d=32, n_layers=1, n_heads=2, d_ff=48, ctx=8))
    records = tensors(model)
    restored = TinyGPT(model.cfg)
    restore_tensors(restored, records)
    assert all(
        torch.equal(a, b) for a, b in zip(model.parameters(), restored.parameters(), strict=True)
    )
    records[0]["name"] = "wrong"
    with pytest.raises(ValueError, match="metadata"):
        restore_tensors(restored, records)


@pytest.mark.native
def test_optimizer_has_independent_pytorch_oracle(tmp_path, native_binary):
    assert verify_optimizer(
        native_binary,
        tmp_path / "optimizer",
        GPTConfig(d=32, n_layers=1, n_heads=2, d_ff=48, ctx=8),
    )["ok"]


@pytest.mark.native
def test_native_resume_preserves_all_branch_weights_and_moments(tmp_path, native_binary):
    seed_all(19)
    cfg = GPTConfig(d=32, n_layers=1, n_heads=2, d_ff=48, ctx=8)
    model = TinyGPT(cfg)
    corpus = tmp_path / "corpus.bin"
    corpus.write_bytes(b"the cat sat on the mat. " * 100)
    spec = TrainSpec(tokens=128, batch=2, seed=19)
    full, interrupted = tmp_path / "full", tmp_path / "interrupted"
    prepare_job(full, model, corpus, spec, "full")
    prepare_job(interrupted, model, corpus, spec, "interrupted")
    subprocess.run(
        [str(native_binary), "--job", str(full / "job.json"), "--reference"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            str(native_binary),
            "--job",
            str(interrupted / "job.json"),
            "--reference",
            "--stop-after",
            "9",
        ],
        check=True,
        capture_output=True,
    )
    result = interrupted / "results/interrupted"
    assert json.loads((result / "status.json").read_text())["state"] == "interrupted"
    job = json.loads((interrupted / "job.json").read_text())
    job["resume"] = descriptor(result / "checkpoint.json", interrupted)
    (interrupted / "job.json").write_text(json.dumps(job))
    subprocess.run(
        [str(native_binary), "--job", str(interrupted / "job.json"), "--reference"],
        check=True,
        capture_output=True,
    )
    for end in (8, 16, 32):
        assert (full / f"results/full/branch-{end}.json").read_bytes() == (
            result / f"branch-{end}.json"
        ).read_bytes()
    a = json.loads((full / "results/full/checkpoint.json").read_text())
    b = json.loads((result / "checkpoint.json").read_text())
    assert all(a[k] == b[k] for k in ("step", "stream_position", "tensors", "moments"))
    assert json.loads((result / "status.json").read_text())["state"] == "completed"


@pytest.mark.native
def test_native_never_silently_falls_back_to_cpu(tmp_path, native_binary):
    if os.name == "nt":
        pytest.skip("Linux no-device gate")
    fake = tmp_path / "job.json"
    fake.write_text("{}")
    result = subprocess.run(
        [str(native_binary), "--job", str(fake)], capture_output=True, text=True
    )
    assert result.returncode != 0
    assert "no D3D12 device" in result.stderr


def test_prepared_indices_match_numpy_stream(tmp_path):
    corpus = tmp_path / "corpus.bin"
    corpus.write_bytes(b"the cat sat on the mat. " * 20)
    cfg = GPTConfig(d=32, n_layers=1, n_heads=2, d_ff=48, ctx=8)
    spec = TrainSpec(tokens=128, batch=2, seed=19)
    root = tmp_path / "job"
    prepare_job(root, TinyGPT(cfg), corpus, spec, "indices")
    assert (root / "train.bin").stat().st_ino == corpus.stat().st_ino
    indices = np.fromfile(root / "indices.bin", dtype="<u8").reshape(-1, 2)
    rng = np.random.default_rng(19)
    for actual in indices:
        assert np.array_equal(actual, rng.integers(0, corpus.stat().st_size - cfg.ctx - 1, size=2))


@pytest.mark.parametrize("fmt", ["ternary", "2bit"])
def test_scientific_zero_row_gate_is_independent_of_backend_parity(fmt):
    from floppylm_xbox.jobs import zero_row_gate

    assert zero_row_gate("row16", fmt)["ok"]
    assert zero_row_gate("row8log", fmt)["ok"]
    # A matching native implementation cannot make this oracle invariant true.
    assert not zero_row_gate("tensor16", fmt)["ok"]


@pytest.mark.native
def test_every_kernel_matches_independent_autograd_including_hidden_boundaries(
    tmp_path, native_binary
):
    from floppylm_xbox.kernels import verify

    report = verify(tmp_path / "kernels", binary=native_binary, hardware=False)
    assert report["case_count"] == 52
    assert report["gates"]["causal-weighted:1"]["ok"]
    assert report["gates"]["cross-entropy-shift:0"]["ok"]
    assert report["ok"], {k: v for k, v in report["gates"].items() if not v["ok"]}
