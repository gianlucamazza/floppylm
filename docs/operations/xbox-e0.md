# Xbox E0 runbook

How to inspect, launch and recover E0 on the Series S backend. This page owns procedure only:
the installed package and running campaign are in [STATUS](../STATUS.md), measured results in
[evidence](../evidence/README.md), the contract in the ADRs below.

## Contract

- [ADR 0008](../adr/0008-e0-numeric-protocol.md) accepts S1–S10.
- [ADR 0009](../adr/0009-xbox-e0-backend.md) selects the separate trainer.
- [ADR 0010](../adr/0010-independent-numerical-gates.md) fixes the numerical gates.
- [ADR 0011](../adr/0011-e0-row-scale-selection.md) selects row16/row8log for scientific E0.
- [ADR 0012](../adr/0012-repo-boundaries.md) assigns repository ownership.

Python owns corpus preparation, ordered samples, initial weights, canonical FLP2 and sliding
evaluation. The app owns GPU training and verified checkpoints. Acceptance and benchmark proofs
must bind the exact installed package and source commit.

Device Portal settings come from the environment, or from an env file read without a shell
(`$FLOPPYLM_XBOX_ENV`, default `~/.config/floppylm/xbox.env`); the environment wins:

```bash
XBOX_IP=192.0.2.10        # console address shown in Dev Home
XBOX_PORT=11443           # optional, Device Portal default
XBOX_USER=...
XBOX_PASS=...
XGPU_E0_PACKAGE_NAME=XgpuE0   # optional, package identity name used for discovery
XBOX_CERT_SHA256=...      # SHA-256 of the console's self-signed Device Portal certificate
```

Device Portal uses a self-signed certificate, so trust is a pinned fingerprint checked on every
connection before credentials are sent. Read it once from the console on a trusted network:

```bash
openssl s_client -connect "$XBOX_IP:11443" </dev/null 2>/dev/null \
  | openssl x509 -outform DER | sha256sum
```

A mismatch stops every request; re-pin only after confirming the console regenerated its certificate.

Never print or commit these values.

Without `XGPU_E0_PACKAGE`, discovery picks the single installed package whose identity name is
`XGPU_E0_PACKAGE_NAME`, whatever its publisher. When several versions are installed, set the explicit
full name from the acceptance proof; ambiguous discovery fails instead of choosing an unvalidated version:

```bash
export XGPU_E0_PACKAGE=<package full name from STATUS>
```

## Inspect a campaign

```bash
# Local manifest, source drift, trial reservation and host state; no network.
python scripts/e0_status.py --campaign runs/<campaign-dir>
# Also verify the live package/source and the bound console job hash.
python scripts/e0_status.py --campaign runs/<campaign-dir> --xbox
```

Both commands only read state. A reservation is not proof of GPU progress; the `console` report
supplies actual dispatches, trunk step, checkpoint, memory and wall time. Nonempty `issues` returns
exit code 1. Network failures surface as errors rather than a cached claim of progress.

Durable state is `runs/<campaign-dir>/campaign.json`, with the launcher log and one log per trial
in the same directory. Trial manifests, jobs and artifacts are in `runs/<run_id>/`; tracked
summaries are in `docs/evidence/e0-v2/runs/<run_id>/` and remain partial until host retrieval and
evaluation complete.

## Validate a package

Each script writes an exclusive output directory; see the [code map](code-map.md) for flags.

```bash
python experiments/xbox_acceptance.py --out runs/xbox-acceptance-<date>-ci<run>
python experiments/xbox_benchmark.py --out runs/xbox-benchmark-<date>-ci<run> \
  --acceptance runs/xbox-acceptance-<date>-ci<run>/acceptance.json
python experiments/xbox_worker_acceptance.py --out runs/xbox-worker-<date>-ci<run>
python experiments/xbox_recovery_acceptance.py --out runs/xbox-recovery-<date>-ci<run> \
  --acceptance runs/xbox-acceptance-<date>-ci<run>/acceptance.json
python experiments/xbox_lifecycle_acceptance.py --out runs/xbox-lifecycle-<date>-ci<run> \
  --acceptance runs/xbox-acceptance-<date>-ci<run>/acceptance.json
```

Copy the resulting JSON proofs into a new `docs/evidence/xbox-e0-<date>[-tag]/` with a
`notes.md`. Acceptance and benchmarks share the GPU queue with scientific training: run them
only when no campaign is training.

## Launch a campaign

A campaign freezes source hashes, recipes, two neutral seeds, the tuning budget, solver grids and
five paired seeds before any scientific result. Its lock permits one worker, and stable exclusive
run identities prevent silent retraining when the campaign is reopened. A failed comparison gate
stops the campaign. While it runs, keep the
frozen `src/floppylm/*.py`, `experiments/*.py` and the installed trainer unchanged; scripts, tests
and docs may change.

```bash
nohup python experiments/e0_campaign.py \
  --out runs/e0-campaign-<unique> \
  --acceptance runs/xbox-acceptance-<date>-ci<run>/acceptance.json \
  --benchmark runs/xbox-benchmark-<date>-ci<run>/summary.json \
  > runs/e0-campaign-<unique>.launch.log 2>&1 &
```

Never wrap campaign or training jobs in `bg`: it moves them into `background.slice`, capped at one
core. Long jobs run under `nohup` outside that slice ([stack](../stack.md), ADR 0003 amendment).

## Recover

If a campaign stops, diagnose the recorded error first. Explicit recovery reconnects to running or
completed work, or resumes a verified interrupted checkpoint. Failed native jobs require a fix and a
new acceptance decision before scientific continuation.

```bash
# Only after the previous campaign worker has exited; same acceptance and benchmark:
python experiments/e0_campaign.py --out runs/<campaign-dir> --recover \
  --acceptance <acceptance.json> --benchmark <summary.json>
# Standalone bound run, when no campaign worker owns it:
python experiments/e0_v2.py --resume RUN_ID --xbox-acceptance <acceptance.json>
```

Recovery verifies package, acceptance, recipe and asset hashes. Existing evaluated branches are
hash-checked and reused; completed recovery leaves the summary unchanged. A byte repair is a
separate, bounded S3 attempt and is recorded as such. There is no implicit migration or fresh
retraining on recovery.

## Data, transport and completion

Prepared corpora are immutable hard links on the same filesystem. Chunk transfers and returned
artifacts are SHA-256 verified. Transport loss is logged and retried up to five consecutive
failures without cancelling GPU work. An explicit interrupt writes a cancel marker; real suspension
publishes a verified checkpoint.

The campaign enforces actual-byte parity and rank stability before comparison; saturation is
recorded ([ADR 0015](../adr/0015-e0-fixed-data-frontier.md)). It freezes ten selected
artifact hashes and makes an exclusive durable reservation before opening the held-out test; that
reservation is never reset automatically. Final reports under
`docs/evidence/e0-v2/campaigns/<campaign_id>/` include paired statistics, recipes, exclusions,
measured costs and unavailable costs. The [roadmap](../roadmap.md) owns the completion gates.

## Package installation

Installation repacks the unsigned CI payload with OpenAppx and signs it with the existing
development certificate. Every executable, shader, resource and manifest entry is checked byte for
byte against the downloaded CI package; ZIP metadata, block map and signature hashes are recorded
separately (`package-lineage.json` in the evidence). Neither installation nor CI success is a
scientific result.


### Interrupted publication

[ADR 0014](../adr/0014-durable-xbox-publication.md) governs upload recovery.
`publication.json` is the durable pending transaction; `submitted.json` is the last
console-acknowledged binding. Preserve both files after a transport failure. Explicit
`--recover` validates the package, recipe and assets, then reconciles the pending hash.
Acknowledged jobs are reattached; an unacknowledged upload is replayed only with proof
that previous work has stopped. Do not delete the journal or edit hashes to force recovery.
Initial acknowledgment and missing/mismatched statuses are bounded to 300 seconds.
Ten minutes without numerical progress emits a diagnostic and keeps valid work running.
