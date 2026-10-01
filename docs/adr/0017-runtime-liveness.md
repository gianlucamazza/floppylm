# ADR 0017: Bounded GPU waits and explicit runtime recovery

## Status

`accepted` — 2026-10-01. The owner approved the implementation plan, selected
hardware validation after E0, and selected explicit recovery rather than automatic
restart. ADR 0016 is reserved by the isolated E1 diagnostics branch.

## Context

A bound E0 job retained a running report and unchanged checkpoint beyond ten
minutes. Diagnosis found an infinite unchecked GPU wait, no distinction between
an active worker and an orphaned running record, and missing host liveness checks.
The initiating GPU/lifecycle cause was not established. ADR 0014 intentionally
makes no-progress diagnostic only; that authority boundary remains in force.

## Decision

- Implement in isolated worktrees; deploy/test on Xbox only after the current E0
  campaign closes. Preserve the existing campaign's package, sources and final-test
  reservation. Do not launch another scientific campaign as part of this fix.
- Native fence waits poll at 250 ms with a 600-second limit per fence, verify the
  wait result and completed fence, and diagnose device loss. A fault invalidates
  the GPU context: no buffer/allocator/queue reuse or destructor re-wait; preserve
  the last published checkpoint and stop the worker until explicit app restart.
- Add `floppylm.worker.v1` and `floppylm.claim.v1` sidecar contracts owned here,
  pinned by the backend. A worker has a new UUID per process start, an exclusive
  process-lifetime lock, a five-second heartbeat sequence, active job/hash and
  separate completed-work progress. A claim stores immutable submitted job bytes
  and their hash so a pending replacement upload cannot erase the old binding.
- Before advertising readiness, a new worker reconciles old claims with matching
  running reports. Only hash-verified checkpoints, job fields and published branch
  artifacts permit `interrupted` recovery. Completed jobs remain untouched;
  missing/inconsistent evidence is a specific failure. No automatic execution.
- Explicit recovery requires live worker evidence and original package/assets.
  Reattach only when that worker owns the exact job/hash; resume an interrupted
  job only from a new idle worker or the original idle worker after cooperative
  interruption. Generic failed/numerically invalid jobs remain refused. Runtime
  faults become recoverable only after a new worker validates the saved checkpoint.
- Host PID liveness is bound to process start identity and boot identity, never
  PID alone. Handle SIGINT/SIGTERM and record the result atomically. SIGKILL is
  detected from abandoned identity/lock state rather than a signal handler.
- Heartbeat unchanged for 30 seconds signals unavailable liveness. Network failure
  is unknown transport state, not proof of death. Completed work unchanged for 600
  seconds records a durable stalled event. Heartbeats do not reset progress time.
  No automatic cancel, restart or retraining follows either alert.
- Update the status CLI to distinguish process identity, provenance, worker
  liveness and observed progress. One snapshot cannot prove progress. Add temporal
  watch mode and durable observations; old timestamps are not themselves failures.
- Keep model bytes, shaders, optimizer and numerical schedule unchanged. Inject
  wait/lifecycle faults only through explicitly functional test fixtures; reject
  them in scientific jobs. Test mock fault paths locally and real lifecycle after E0.

## Consequences

New recovery requires the new worker contract; historical v1 model/job evidence
remains valid without adding speculative runtime compatibility. New optional
runtime-fault result metadata is descriptive, not a scientific quality verdict.
No-progress remains diagnostic as required by ADR 0014. Successful CI does not
establish Xbox fault recovery. Release requires exact-package hardware evidence.

## Alternatives

Automatic app restart, treating any running snapshot as live, changing the frozen
campaign, and resubmitting from step zero were rejected. A training-duration cap
would change the experiment; only individual GPU waits are bounded.
