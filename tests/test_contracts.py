"""floppylm.*.v1 JSON Schemas against golden fixtures, measured evidence and live producers."""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from floppylm.model import GPTConfig, TinyGPT
from floppylm.seed import seed_all
from floppylm.train import TrainSpec
from floppylm.xbox import prepare_job, tensors

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
FIXTURES = ROOT / "tests/fixtures/contracts"
EVIDENCE = ROOT / "docs/evidence"


def load(path: Path) -> dict:
    return json.loads(path.read_text())


SCHEMA_FILES = sorted(SCHEMAS.glob("*.json"))
REGISTRY = Registry().with_resources(
    (load(p)["$id"], Resource.from_contents(load(p))) for p in SCHEMA_FILES
)


def validator(name: str) -> Draft202012Validator:
    return Draft202012Validator(load(SCHEMAS / f"{name}.json"), registry=REGISTRY)


def fixtures(kind: str) -> list[Path]:
    return sorted((FIXTURES / kind).glob("*.json"))


@pytest.mark.parametrize("path", SCHEMA_FILES, ids=lambda p: p.stem)
def test_schemas_are_valid_draft_2020_12(path):
    Draft202012Validator.check_schema(load(path))
    assert load(path)["$id"].endswith("/" + path.name)


@pytest.mark.parametrize("path", fixtures("valid"), ids=lambda p: p.stem)
def test_valid_fixture(path):
    validator(path.stem.split("--")[0]).validate(load(path))


@pytest.mark.parametrize("path", fixtures("invalid"), ids=lambda p: p.stem)
def test_invalid_fixture(path):
    assert not validator(path.stem.split("--")[0]).is_valid(load(path))


def test_every_contract_has_a_valid_fixture():
    contracts = {p.stem for p in SCHEMA_FILES} - {"floppylm.e0.common.v1"}
    assert contracts == {p.stem.split("--")[0] for p in fixtures("valid")}


def test_measured_native_reports_match_the_contract():
    results, devices = validator("floppylm.e0.result.v1"), validator("floppylm.device.v1")
    checked = 0
    for summary in EVIDENCE.glob("e0-v2/runs/*/summary.json"):
        if "backend" in load(summary):
            results.validate(load(summary)["backend"])
            checked += 1
    for acceptance in EVIDENCE.glob("xbox-e0-*/acceptance.json"):
        if "device" in load(acceptance):
            devices.validate(load(acceptance)["device"])
            checked += 1
    for lifecycle in EVIDENCE.glob("xbox-e0-*/lifecycle*.json"):
        for value in load(lifecycle).values():
            if isinstance(value, dict) and value.get("schema") == "floppylm.e0.result.v1":
                results.validate(value)
                checked += 1
    assert checked >= 3


def test_live_producers_match_the_contract(tmp_path):
    seed_all(0)
    model = TinyGPT(GPTConfig(vocab=16, d=8, n_layers=1, n_heads=2, d_ff=8, ctx=8))
    corpus = tmp_path / "corpus.bin"
    corpus.write_bytes(bytes(range(16)) * 64)
    job = prepare_job(tmp_path / "job", model, corpus, TrainSpec(tokens=64, batch=2), "tiny")
    validator("floppylm.e0.job.v1").validate(job)
    validator("floppylm.e0.initialization.v1").validate(load(tmp_path / "job/initial.json"))
    weights = {"schema": "floppylm.e0.weights.v1", "config": model.cfg.to_dict()}
    validator("floppylm.e0.weights.v1").validate(weights | {"tensors": tensors(model)})
