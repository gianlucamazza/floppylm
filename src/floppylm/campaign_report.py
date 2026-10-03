"""Attempt-level evidence projection; never infer a repair's recipe from its parent."""

from __future__ import annotations

from . import parity


def attempt_record(key: str, record: dict, run_id: str, summary: dict) -> dict:
    status = summary.get("status", "unknown")
    eligibility, reasons = "unknown", []
    branches = summary.get("branches", [])
    if status == "completed" and len(branches) == 3 and summary.get("target_bytes"):
        ok, reasons = parity.admissible(
            {run_id: branches[-1]["model_bytes"]}, summary["target_bytes"]
        )
        eligibility = "eligible" if ok else "excluded"
    spec = summary.get("spec", {})
    effective = None
    if "config" in summary and all(k in spec for k in ("seed", "lr", "wd")):
        effective = {"config": summary["config"], **{k: spec[k] for k in ("seed", "lr", "wd")}}
    return {
        "key": key,
        "run_id": run_id,
        "attempt": "original" if run_id == record["run_id"] else "repair",
        "status": status,
        "eligibility": eligibility,
        "eligibility_scope": "individual 4T serialized-byte parity; group gates are separate",
        "exclusion_reasons": reasons,
        "trial_outcome": record["status"],
        "selected": run_id == record.get("result"),
        "requested_recipe": record["recipe"],
        "recipe": effective,
        "compute": summary.get("compute"),
        "saturation": summary.get("saturation"),
    }


def baseline_complete(state: dict, selection: dict | None, final: dict | None) -> bool:
    """A report may claim completion only for the campaign's bound final selection."""
    if not (
        state.get("status") == "completed"
        and state.get("phase") == "completed"
        and state.get("paired")
        and selection
        and final
        and selection.get("purpose") == final.get("purpose") == "scientific"
        and selection.get("name") == final.get("selection") == state.get("selection")
    ):
        return False
    selected = selection.get("items", [])
    results = final.get("results", [])
    if len(selected) != 10 or len(results) != 10:
        return False
    keys = ("run_id", "artifact", "sha256", "model_bytes")
    expected = {tuple(item.get(k) for k in keys) for item in selected}
    actual = {tuple(item.get(k) for k in keys) for item in results}
    return (
        len(expected) == 10
        and all(None not in item for item in expected)
        and expected == actual
        and all("test_bpb" in item for item in results)
    )
