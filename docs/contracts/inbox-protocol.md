# E0 console inbox protocol

Normative. floppylm owns this protocol together with the [`schemas/`](../../schemas/README.md) it
carries (ADR 0012); the backend implements it, `floppylm_xbox.portal` is the client. A change
here comes first and is pinned by the backend like the schemas.

## Locations

The backend app keeps two locations in its local application data, reached through Device Portal:

| Path | Content |
| --- | --- |
| `device.json` | `floppylm.device.v1`, written once when the GPU worker starts |
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
