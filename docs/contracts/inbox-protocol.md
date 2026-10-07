# E0 console inbox protocol

Normative. floppylm owns this protocol together with the [`schemas/`](../../schemas/README.md) it
carries (ADR 0012); the backend implements it, `floppylm_xbox.portal` is the client. A change
here comes first and is pinned by the backend like the schemas.

## Locations

The backend app keeps two locations in its local application data, reached through Device Portal:

| Path | Content |
| --- | --- |
| `device.json` | `floppylm.device.v1`, written once when the GPU worker starts |
| `worker.json` | `floppylm.worker.v1`, atomic worker identity, heartbeat and completed work |
| `inbox/<job_id>.owner.json` | `floppylm.claim.v1`, immutable claimed payload and owner |
| `inbox/` | Everything a job exchanges; all paths in descriptors are relative to it |
| `inbox/results/<job_id>/` | `status.json` (`floppylm.e0.result.v1`), `checkpoint.json` (`floppylm.checkpoint.v1`), `branch-<end_step>.json` (`floppylm.e0.weights.v1`) |

Absolute paths, `..` and links that leave `inbox/` are rejected.

## Submitting a job

1. Upload every asset named by the descriptors of the job (`initialization`, `data`, `indices`,
   and `resume` when resuming). An asset may be sent as content-addressed chunks
   `<sha256>.chunk`; the descriptor then lists them in `chunks`, in order, and the backend
   assembles, size-checks and hashes the file before use. An asset already present with the same
   name and size is not re-sent.
2. Upload `<job_id>.job.json`: `floppylm.e0.job.v1`, or a fixture schema
   (`floppylm.e0.fixture.v1`, `floppylm.e0.kernels.v1`, `floppylm.e0.optimizer.v1`). `job_id` must
   equal the file stem.
3. Upload `<job_id>.ready` last. The backend claims a job by renaming it to `<job_id>.claimed`,
   runs one job at a time, and polls the inbox about once per second.

The client binds what it submitted (job SHA-256 and package) and checks every report against that
binding and against the device's `capabilities`, when reported, before uploading.

## Outputs

- Training jobs write `results/<job_id>/status.json` at start, every 64 optimizer steps of the
  trunk and of each cooldown, at the end of each branch and at the end; the trunk checkpoint at the
  same trunk cadence and before each cooldown; and one weights file per finished branch.
  Optional `loss_series` is a bounded trail of `{step, loss}` trunk samples (capacity 512, halved
  when full). The on-console chart is a view of that field: after resume the dashboard replaces
  RAM history from it. A status without the field remains valid; the viewer then plots
  `last_loss` at `trunk_step` only. The series is display-only and is not a numerical identity
  field.
- Fixtures write `<job_id>.actual.json`: `floppylm.e0.fixture.report.v1`,
  `floppylm.e0.kernels.result.v1` or `floppylm.e0.optimizer.report.v1`.
- A job that fails before training starts gets a `status.json` with only `job_id`,
  `state: failed` and `error`.

## Interruption and resume

- **Request.** The client uploads `<job_id>.cancel`. At the next trunk step the backend writes a
  checkpoint and `state: interrupted`; during a cooldown it stops and the trunk checkpoint taken
  before that cooldown stands.
- **Suspension.** When the app is suspended it writes `<job_id>.cancel` with the body `suspend` and
  stops the active job the same way.
- **Resume.** The client deletes `<job_id>.cancel`, re-uploads `<job_id>.job.json` with `resume`
  set to the checkpoint descriptor (and without `stop_after`), then `<job_id>.ready` with the body
  `resume`. The backend verifies that the checkpoint repeats the bound job fields and that branch
  artifacts already reported still verify; finished branches are not recomputed.


## Runtime ownership (ADR 0017)

The new runtime holds an exclusive process-lifetime worker lock and publishes a fresh
worker ID per process, package/source, heartbeat sequence every five seconds, active
job/hash and completed-work counters. A single snapshot proves neither liveness nor
progress. The client observes an advancing heartbeat before submission or recovery;
30 seconds with no heartbeat advance is unavailable, while transport failure is unknown.
600 seconds without completed work emits a durable alarm and does not cancel a job.

Before execution, the worker atomically persists the exact claimed payload and its hash
in the ownership sidecar. At startup, before scanning ready jobs, it reconciles orphan
claims. A valid checkpoint must restore the bound model/optimizer/stream state, and
published branch descriptors must verify. Only then may an orphan running report or a
recognized operational GPU failure become interrupted. Completed results remain intact;
missing or inconsistent evidence becomes a specific failure. Reconciliation never queues
execution. Leftover ready markers beside reconciled claims are quarantined; pre-admission
rejection preserves existing results and writes `<job_id>.rejected.json` with the submitted
hash. An explicit host recovery command may attach to a live exact owner or resume
an interrupted job on an idle live worker; generic failures remain refused.

Each GPU fence wait has a 600-second deadline with 250 ms checks. Failed waits, device
removal and deadline expiry poison the GPU context and stop job dispatch until explicit
app restart. Results may carry `runtime_fault`; the last published checkpoint is retained.
A kernel fixture may request `runtime_fault_probe` for functional validation only. This
field is not allowed in scientific training jobs.

This protocol revision requires a newly accepted package. It must not be deployed over
the frozen running E0 campaign. Historical result/model contracts remain valid.

## Later (2026-10-07)

Campaign `e0-20261004T103838Z-c58a86` stopped on 2026-10-07. That stop does not
authorize a package deploy.
