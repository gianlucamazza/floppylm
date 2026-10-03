"""Publish a separate, hash-bound correction of historical campaign projections."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from floppylm import runlog  # noqa: E402
from floppylm.campaign_report import attempt_record  # noqa: E402


def correction(evidence: Path, campaign: Path) -> dict:
    inputs = {}

    def read(path):
        inputs[str(path.relative_to(evidence))] = runlog.sha256_file(path)
        return json.loads(path.read_text())

    state = read(campaign / "campaign.json")
    original = read(campaign / "summary.json")
    attempts = []
    for key, record in state["trials"].items():
        for run_id in (record["run_id"], record.get("repair_id")):
            if run_id is None:
                continue
            path = evidence / "runs" / run_id / "summary.json"
            summary = read(path) if path.exists() else {}
            attempts.append(attempt_record(key, record, run_id, summary))
    if state["status"] != "stopped":
        raise ValueError("this historical correction only covers stopped campaigns")
    return {
        "campaign": state["id"],
        "purpose": "historical reporting correction, not new scientific evidence",
        "input_sha256": inputs,
        "original_status": original["status"],
        "baseline_complete": False,
        "comparisons": state.get("comparisons", {}),
        "comparisons_scope": "only recorded group gates; absent gates remain unknown",
        "trials": attempts,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, default=ROOT / "docs/evidence/e0-v2")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    reports = [
        correction(args.evidence, path.parent)
        for path in sorted((args.evidence / "campaigns").glob("*/campaign.json"))
    ]
    args.out.mkdir(parents=True, exist_ok=False)
    for report in reports:
        runlog.write_json(args.out / (report["campaign"] + ".json"), report)
    runlog.write_atomic(
        args.out / "notes.md",
        "\n".join(
            [
                "# Historical E0 report corrections — 2026-10-03",
                "",
                "These additive corrections preserve the original evidence. Each JSON binds",
                "its input campaign, original report and available run summaries by SHA-256.",
                "Original and repaired attempts have separate effective recipes and individual",
                "4T byte eligibility. Trial outcome is not inherited as attempt eligibility.",
                "Missing summaries remain unknown; unrecorded group gates are not reconstructed.",
                "All covered campaigns are stopped: none establishes a completed E0 baseline.",
                "",
                *[f"- [{r['campaign']}]({r['campaign']}.json)" for r in reports],
                "",
            ]
        ),
    )


if __name__ == "__main__":
    main()
