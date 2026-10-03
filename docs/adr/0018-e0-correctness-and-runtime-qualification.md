# ADR 0018: E0 reporting and bounded runtime qualification

## Status

`accepted` — 2026-10-03. The owner approved the host-and-Xbox implementation
plan. Completes ADR 0015 selection enforcement and ADR 0017 runtime qualification;
does not change scientific recipes, byte gates or automatic-recovery authority.

## Context

Tuning and shape grids bypassed ADR 0015 rank stability. Campaign reports copied
trial-level eligibility and requested configuration onto each original/repair attempt.
Worker transport failures retried indefinitely although status failures were bounded.
Package acceptance had not exercised the published-fence watchdog on hardware.

## Decision

- Share the rank-stable selection path across neutral, tuning and grid phases.
  Record all branch scores on instability before stopping; keep paired-sign checks.
- Report requested recipes, effective attempt recipes, individual byte eligibility,
  group comparability and trial outcome separately. Unknown evidence remains unknown.
  A baseline claim requires a completed campaign and bound selection/final-test evidence.
- Publish hash-bound corrections separately from frozen historical evidence, with
  dated pointers in its notes. Never regenerate history over the original record.
- Bound status and worker transport failures independently to five consecutive
  failures, with the existing exponential backoff. Only a successful read of the same
  resource resets its counter. Persist transition/count telemetry; exhaustion stops
  host observation without cancelling, restarting or requeuing the device job.
- Add an optional functional training probe, `runtime_fault_probe`, with kind
  `published_fence_stall` and `after_checkpoint_step` (positive integer). Reject it
  unless purpose is explicitly functional, reject it on resumed submissions, and
  reject an unreachable checkpoint step. The backend parks the execution thread after
  a durable checkpoint, without holding publication locks. The normal heartbeat and
  real 600-second watchdog remain active; the probe never invokes the fault handler.
- Explicit resume removes the probe through the existing journaled publication path.
  Scientific jobs cannot carry the probe. Normal numerical execution is unchanged.
- Qualify the exact CI package with a synthetic uninterrupted control and probe run:
  advancing heartbeat, frozen work, watchdog publication and process exit, explicit
  restart, verified checkpoint recovery and exact final-artifact comparison. Preserve
  existing scientific files. Hardware unavailability remains an open qualification.

## Consequences

Contracts remain owned here and are pinned by the native backend. The additive probe
requires an updated backend; old jobs remain valid. Local tests and successful builds
do not certify the hardware fault path. No scientific campaign is launched by this work.
The fill-aware solver and scientific E1 protocol remain separate proposals.

## Alternatives

Unbounded polling hides persistent loss of observation. Automatic restart changes
the operator authority boundary. Mock-only timeout tests cannot establish console
recovery. Rewriting old evidence destroys the audit trail.
