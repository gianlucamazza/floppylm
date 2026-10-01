# Xbox E0 operating guide

The separate DX12/UWP trainer is validated on retail Series S. Scientific campaign
`e0-20261001T090514Z-4236fd` is running on the GPU-resident E0.1 package; selection and
quality results remain pending. The first campaign `e0-20261001T074326Z-503df0`
(package 0.1.0.24) was stopped cleanly at trunk step 455 for E0.1 and is kept as a record.
[Current evidence](evidence/xbox-e0-20261001/notes.md) owns measured results and lineage.
[Validation history](xbox-e0-history.md) preserves earlier packages and failed baselines.

## Accepted contract

[ADR 0008](adr/0008-e0-numeric-protocol.md) accepts S1–S10;
[ADR 0009](adr/0009-xbox-e0-backend.md) selects the separate trainer;
[ADR 0010](adr/0010-independent-numerical-gates.md) fixes numerical gates;
[ADR 0011](adr/0011-e0-row-scale-selection.md) selects row16/row8log for scientific E0.
Python owns corpus preparation, ordered samples, initial weights, canonical FLP2
and sliding evaluation. The app owns GPU training and verified checkpoints.

Current package: `GianlucaMazza.XgpuE0_0.1.0.28_x64__g0p5dcfz4t9z4` (E0.1, CI run
36839565773). Its exact source is `25f8bc3966ffae940658be94161d31edd83492c9`. It is
bit-identical to 0.1.0.24 on every acceptance case, trained weight and benchmark artifact,
and runs the representative benchmark at 10224 token/s instead of 963.6
([xbox-gpu-training evidence](https://github.com/gianlucamazza/xbox-gpu-training/tree/main/docs/evidence/e0-20261001-resident)). Acceptance and benchmark must bind this package/source.
Set the explicit package when several versions are installed:

```bash
export XGPU_E0_PACKAGE=GianlucaMazza.XgpuE0_0.1.0.28_x64__g0p5dcfz4t9z4
```

## Inspect the running campaign

```bash
# Local manifest, source drift, trial reservation and host state; no network.
python scripts/e0_status.py --campaign runs/e0-campaign-20261001-e01
# Also verify live package/source and the bound console job hash.
python scripts/e0_status.py --campaign runs/e0-campaign-20261001-e01 --xbox
```

Both commands read state only. A reservation is not proof of GPU progress; the
`console` report supplies actual dispatches, trunk step, checkpoint, memory and
wall time. Nonempty `issues` returns exit code 1. Network failures surface as
errors rather than a cached claim of current progress.

Durable state: `runs/e0-campaign-20261001-e01/campaign.json`. The launcher log and one
log per trial are in the same directory. Trial manifests, jobs and artifacts are
in `runs/<run_id>/`; tracked summaries are in `docs/evidence/e0-v2/runs/<run_id>/`.
These summaries remain partial until host retrieval and evaluation complete.

## Scientific execution and recovery (2026-10-01)

The campaign freezes source hashes, recipes, two neutral seeds, tuning budget,
solver grids and five paired seeds before scientific results. Its lock permits
one worker. Keep frozen `src/floppylm/*.py`, `experiments/*.py` and the installed
trainer unchanged during execution. Scripts, tests and prose can be polished
without changing those scientific inputs.

For a new campaign, use an exclusive output directory and the current proofs:

```bash
/home/gianluca/.local/bin/bg python experiments/e0_campaign.py \
  --out runs/e0-campaign-UNIQUE \
  --acceptance runs/xbox-acceptance-20261001-ci36839565773/acceptance.json \
  --benchmark runs/xbox-benchmark-20261001-ci36839565773/summary.json
```

The running campaign already has its worker. If it stops, diagnose the recorded
error first. Explicit recovery reconnects to running/completed work or resumes a
verified interrupted checkpoint. Failed native jobs require a fix and a new
acceptance decision before scientific continuation.

```bash
# Only after the prior campaign worker has exited:
/home/gianluca/.local/bin/bg python experiments/e0_campaign.py \
  --out runs/e0-campaign-20261001-e01 --recover \
  --acceptance runs/xbox-acceptance-20261001-ci36839565773/acceptance.json \
  --benchmark runs/xbox-benchmark-20261001-ci36839565773/summary.json
# Standalone bound run, when no campaign worker owns it:
/home/gianluca/.local/bin/bg python experiments/e0_v2.py --resume RUN_ID \
  --xbox-acceptance runs/xbox-acceptance-20261001-ci36839565773/acceptance.json
```

Recovery verifies package, acceptance, recipe and asset hashes. Existing evaluated
branches are hash-checked and reused; completed recovery leaves the summary
unchanged. A byte repair is a separate, bounded S3 attempt and is recorded as such.
There is no implicit migration or fresh retraining on recovery.

## Data, transport and completion

Prepared corpora are immutable hard links on the same filesystem. Chunk transfers
and returned artifacts are SHA-256 verified. Transport loss is logged and retried
up to five consecutive failures without cancelling GPU work. An explicit interrupt
writes a cancel marker; real suspension publishes a verified checkpoint.

The campaign enforces actual-byte parity and saturation before comparison. It
freezes ten selected artifact hashes and makes an exclusive durable reservation
before opening the held-out test. That reservation is never reset automatically.
Final reports under `docs/evidence/e0-v2/campaigns/<campaign_id>/` include paired
statistics, recipes, exclusions, measured costs and unavailable costs.
[The roadmap](experiments-roadmap.md) owns scientific completion gates.

Hardware fixtures, smoke and representative synthetic throughput remain functional
proofs. Run acceptance or benchmarks when the console is available for isolated
validation; they share the same GPU queue as scientific training.
