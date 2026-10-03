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
- [ADR 0014](../adr/0014-durable-xbox-publication.md) journals publication until console acknowledgment.
- [ADR 0015](../adr/0015-e0-fixed-data-frontier.md) compares at equal tokens; saturation is recorded.

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
systemd-run --user --unit=floppylm-e0-campaign-<unique> \
  --working-directory="$PWD" --property=TimeoutStartSec=infinity \
  /bin/bash -c 'exec .venv/bin/python -u experiments/e0_campaign.py \
    --out runs/e0-campaign-<unique> \
    --acceptance runs/xbox-acceptance-<date>-ci<run>/acceptance.json \
    --benchmark runs/xbox-benchmark-<date>-ci<run>/summary.json \
    >> runs/e0-campaign-<unique>.launch.log 2>&1'
```

Enable linger (`loginctl enable-linger "$USER"`). Never wrap campaign or training jobs in `bg`:
it moves them into `background.slice`, capped at one core. Long jobs stay in `app.slice`
([stack](../stack.md), [ADR 0017](../adr/0017-runtime-liveness.md)).

## Recover

If a campaign stops, diagnose the recorded error first. Explicit recovery reconnects to running or
completed work, or resumes a verified interrupted checkpoint. Failed native jobs require a fix and a
new acceptance decision before scientific continuation.

Runtime recovery follows [ADR 0017](../adr/0017-runtime-liveness.md). Verify the exact
package/source and an advancing `worker.json` heartbeat before reattaching. A running
report alone is not a live execution: its job/hash must match the worker's active owner.
An interrupted result requires an idle live worker and a verified checkpoint. After a
runtime GPU fault, explicitly restart the same app and let native reconciliation verify
its immutable owner, checkpoint and branch hashes before requesting resume. Failed
numerical or integrity results remain refused.

A frozen trunk counter alone does not prove a hang: cooldown steps and completed GPU
fences are separate progress. Heartbeat unchanged for 30 seconds is unavailable liveness;
transport errors are unknown. No completed work for ten minutes records a durable alarm.
Neither alarm cancels, restarts or resubmits work. Device Portal CPU counters alone do not
establish the cause of a stall.

The runtime upgrade and its hardware fault probes are gated until the currently frozen
E0 campaign closes. That historical package does not have the new worker contract. Keep
its frozen source/package and recorded recovery procedure; do not run this branch's
recovery against it or install a new package mid-campaign.

```bash
# Operator recover: start the bound package if XgpuE0.exe is gone, wait for a
# live worker, then exec campaign --recover. Same acceptance and benchmark.
# Device Portal POST /api/taskmanager/app is not used (HTTP 400 running or missing).
python scripts/e0_recover.py --out runs/<campaign-dir> \
  --acceptance <acceptance.json> --benchmark <summary.json>
# Inner campaign command, only when the process is already live and idle:
python experiments/e0_campaign.py --out runs/<campaign-dir> --recover \
  --acceptance <acceptance.json> --benchmark <summary.json>
# Standalone bound run, when no campaign worker owns it:
python experiments/e0_v2.py --resume RUN_ID --xbox-acceptance <acceptance.json>
```

`scripts/e0_recover.py` starts the package once when the process list is empty,
then reads `device.json` (LocalState is 404 while the process is gone).
A present process with a stale heartbeat is refused: terminate, then recover.
Do not run a looping keep-alive sidecar (ADR 0017). Keep XgpuE0 in the foreground.

Recovery verifies package, acceptance, recipe and asset hashes. Existing evaluated branches are
hash-checked and reused; completed recovery leaves the summary unchanged. A byte repair is a
separate, bounded S3 attempt and is recorded as such. There is no implicit migration or fresh
retraining on recovery.

The on-console loss chart is a view of published `loss_series` on `status.json`. After
interrupt and relaunch the dashboard replaces its RAM history from that field, so the curve
continues from persisted samples rather than starting empty at the resume step. Packages that
do not publish the field stay valid: the viewer plots the single `last_loss` at `trunk_step`.
The series is optional, display-only, and never invented for steps that were not sampled. A
package that publishes it is a later operator install; do not install over a running campaign.

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


### Temporal monitoring

```bash
python scripts/e0_status.py --campaign runs/<campaign-dir> --xbox --watch 5 --duration 120
```

A single report labels progress unverified. Watch records atomic `monitor.json` and an
fsynced `monitor.jsonl` journal, with separate source/device provenance, host PID/start/boot
identity and lock ownership, worker heartbeat, and completed work. `--observations PATH`
selects the journal location. The trial writes `xbox/runtime.json` and
`xbox/runtime-events.jsonl`; campaign signal handling records `runtime-events.jsonl` and
waits for its child to finish cancellation before releasing `worker.lock`.

### Post-E0 hardware qualification

After E0 closes, preserve its manifest, final-test reservation and complete LocalState
snapshot. Use the exact candidate CI artifact, record package/file hashes, and restore the
snapshot afterward with a byte-verification report. Use only new functional job IDs.

Required evidence before runtime acceptance:

1. Healthy worker: unique instance, lock exclusion, advancing heartbeat and completed
   trunk/cooldown/fence progress; healthy training and checkpoint parity unchanged.
2. Functional kernel fixtures for each `runtime_fault_probe.kind`: `gpu_wait_timeout`,
   `gpu_wait_failed`, `gpu_device_removed`. Capture the failed result and worker fault,
   prove no next job is dispatched and app remains diagnosable until explicit restart.
3. Kill the app after a functional checkpoint, restart without submitting work, and prove
   the orphan becomes interrupted only after binding/checkpoint/branch verification.
   Resume explicitly; compare final artifacts and verify completed branches are reused.
4. Repeat with missing owner, corrupted checkpoint/branch and pending replacement upload:
   preserve evidence, refuse unsafe continuation, and quarantine any leftover ready marker.
5. Verify host SIGINT, SIGTERM and SIGKILL diagnostics; transport loss remains unknown,
   heartbeat freeze becomes unavailable, completed-work freeze produces one stall event.
   None of these observations may automatically restart or retrain.

Linux tests and Windows/UWP compilation establish only their own predicates. They do not
close these Xbox lifecycle gates or identify the cause of the original E0 stall.

## Published-fence watchdog qualification

After accepting an idle candidate package, run the explicitly functional probe:

```bash
python experiments/xbox_watchdog_acceptance.py --out runs/watchdog-new --acceptance runs/acceptance-new/acceptance.json
```

The runner refuses pending inbox work and scientific running records. It records
pre-existing inbox sizes, JSON hashes and scientific result descriptors before and
after; large content-addressed inputs are not rehashed. It retains uniquely named
functional jobs as evidence and does not restore stale worker identity files.
It observes the real 600-second watchdog, requires process exit, explicitly starts
that same package once, then compares recovered numerical artifacts and checkpoint
state with an uninterrupted synthetic control. The timeout never cancels GPU work.
Inspect `failure.json` and the observations after a failed qualification; do not
blindly rerun or restart an unobserved worker. CI and portable tests do not close
this hardware gate. See [ADR 0018](../adr/0018-e0-correctness-and-runtime-qualification.md).
