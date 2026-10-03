# Proposal: execution phases, terminal observations and lock authority

Status: **proposal**, 2026-10-03. Not accepted; no implementation or console
mutation is authorized by this document. It follows the
[a8d8b9 incident analysis](../../evidence/e0-incident-20261003/notes.md).
Accepted ADRs 0014 and 0017 remain unchanged pending an explicit superseding ADR.

## Context

The published-fence watchdog classified an active job without a moving fence as
`gpu_wait_timeout`. Evidence localizes the incident to the checkpoint publication
path after step 3008, with committed state still at 2944. The published worker
does not distinguish CPU serialization, filesystem activity and a pending GPU
request. The same failed process remains listed after its exit callback. The
synthetic lock-free stall qualified earlier does not settle this case.

Separately, host Btrfs identity checks misclassify held locks; the monitor's
service dependency suppresses the terminal snapshot. These are authority and
observation defects, not reasons to change model numerics or scientific gates.

## Proposed decision

1. **Native execution evidence.** Publish the current execution phase independently
   of the execution thread, with monotonic phase-entry time, sequence, active job
   hash and checkpoint step. Distinguish checkpoint construction/encoding, file
   output, replacement, GPU submission/wait and idle. Record entry/exit markers
   around potentially blocking calls; never depend on a blocked call returning
   to report where it blocked. Bound the event history and keep it outside tensors.

2. **Watchdog authority.** Preserve the existing bounded GPU wait. Only explicit
   in-flight GPU evidence may be classified as a GPU wait timeout. A job with
   unchanged published progress during CPU or filesystem work yields a separate
   diagnostic stall; it does not authorize automatic cancellation, restart or
   retraining. GPU-wait deadlines and scientific token schedules do not change.
   Qualification must prove that CPU serialization pauses cannot impersonate a
   pending GPU request.

3. **Terminal fault containment.** Persist the first fault and last committed
   checkpoint before invoking a platform-qualified termination path. Actual exit
   is a separate postcondition, not inferred from a `failed` document. Select the
   supported Xbox/UWP mechanism in the acceptance ADR only after qualification
   with both lock-free and held-lock functional faults. No cleanup path may reuse
   a poisoned GPU context. No automatic restart follows termination.

4. **Host lock authority.** Consolidate PID-bearing and legacy ownership checks
   behind one policy. Bind process boot/start identity to the exact lock file and
   its held descriptor using filesystem-aware identity; do not compare a Btrfs
   `stat` device directly with the different kernel lock device. Do not replace
   that comparison with inode-only matching. Missing access, ambiguity or unstable
   observations return unknown and prevent launch/recovery. For legacy records,
   absence of an unmatchable `/proc/locks` entry is never proof of a free lock.

5. **Terminal observation lifecycle.** Observation must outlive campaign exit long
   enough to record its terminal manifest and service exit status. Capture a final
   best-effort read-only console/worker snapshot with bounded transport retries;
   unavailable transport stays unknown. Persist raw worker inputs, observation
   time and provenance, and label old snapshots as historical. Then exit the
   observer explicitly. No direct `BindsTo` teardown before terminal capture.
   Preserve native interruption versus host execution error in diagnostic output.

## Consequences and acceptance

Additive worker/event metadata needs an explicit canonical contract decision and
backend pin before a new package is qualified. Existing job recipes, model bytes,
checkpoint semantics and reserved test remain unchanged. No metadata change can
migrate the frozen `a8d8b9` campaign to a different source/package.

Host acceptance includes real tmpfs and Btrfs held/free/wrong-owner tests, PID
reuse and unavailable-proc cases, exit between observations, terminal transport
failure, persisted raw input replay and bounded observer exit. Native acceptance
includes controlled checkpoint phase pauses, real GPU waits, lock-held exit
qualification, artifact identity and explicit exact recovery on the candidate.
Use isolated worktrees and functional jobs; preserve the incident package and
evidence until a deliberate disposition is chosen.

## Alternatives rejected

- Increasing deadlines or automatically retrying hides the failing phase and
  spends scientific budget without explaining the incident.
- Treating a published-fence stall as proof of a D3D fault ignores CPU/I/O phases.
- Restarting whenever a document looks stale crosses the explicit recovery boundary.
- Reporting every absent lock match as free makes incomplete observation authority.
- Rewriting the old acceptance record would erase valid but narrower evidence.

## Decision still requiring qualification

The exact process termination primitive is intentionally not selected from a
process-list snapshot. Thread/process-state evidence and platform support must
precede that part of the accepted ADR. This proposal is a correction agenda, not
a claim that the initiating stall has been fixed.
