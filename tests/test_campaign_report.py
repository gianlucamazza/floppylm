"""Reports keep missing evidence unknown and bind completed baseline claims."""

from copy import deepcopy

import pytest

from floppylm.campaign_report import attempt_record, baseline_complete


def test_missing_or_interrupted_attempt_is_not_eligible():
    record = {"run_id": "original", "status": "eligible", "recipe": {}, "result": "repair"}
    for summary in ({}, {"status": "interrupted"}):
        result = attempt_record("trial", record, "repair", summary)
        assert result["eligibility"] == "unknown"
        assert result["recipe"] is None
        assert result["trial_outcome"] == "eligible"


def proof():
    state = {"status": "completed", "phase": "completed", "paired": {"n": 5}, "selection": "frozen"}
    items = [
        {"run_id": str(i), "artifact": f"{i}.flp", "sha256": str(i), "model_bytes": 1000}
        for i in range(10)
    ]
    selection = {"purpose": "scientific", "name": "frozen", "items": items}
    final = {
        "purpose": "scientific",
        "selection": "frozen",
        "results": [{**item, "test_bpb": 1.3} for item in items],
    }
    return state, selection, final


def test_baseline_requires_bound_complete_selection():
    assert baseline_complete(*proof())


@pytest.mark.parametrize("fault", ["stopped", "functional", "hash", "duplicate", "missing"])
def test_partial_or_mismatched_proof_cannot_claim_baseline(fault):
    state, selection, final = deepcopy(proof())
    if fault == "stopped":
        state["status"] = "stopped"
    elif fault == "functional":
        final["purpose"] = "functional"
    elif fault == "hash":
        final["results"][0]["sha256"] = "other"
    elif fault == "duplicate":
        final["results"][0] = final["results"][1]
    else:
        final = None
    assert not baseline_complete(state, selection, final)
