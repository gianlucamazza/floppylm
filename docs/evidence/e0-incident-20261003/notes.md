# E0 incident analysis: a8d8b9, 2026-10-03

Diagnosis is complete within the available evidence. The initial blocking function
is **not established**. The strongest localization is the checkpoint publication
path after completed training step 3008, not a demonstrated pending GPU fence.
Recovery has not been executed. No scientific conclusion follows from this stop.

## Preserved evidence and scope

Raw evidence is retained in `runs/e0-incident-20261003T113647Z/`: 34 original files,
2,178,761,987 bytes, copied before analysis with [SHA-256 inventory](inventory.json).
A final [preservation check](preservation-check.json) confirms all 34 original files
are unchanged. Remote GETs additionally saved the owner/job, result, checkpoint, two branches and
an empty checkpoint temporary file. No Xbox writes, restart, deployment, trial,
reconciliation or final-test access occurred. The original runtime sources remain
unchanged; the examined backend runtime/UWP tree equals qualified source `cc134fe4`.

The [integrity checks](integrity.json) bind campaign `e0-20261003T104407Z-a8d8b9`,
trial `000`, host source `8867ec6`, package `0.1.0.98`, job SHA-256
`25b53e33d60b1f972d6e2beac848b5a4778c9228605497baf9b3ff962d1ae9f9` and its acceptance.
The actual submitted scientific job contains no functional fault probe.

## Timeline (UTC)

| Time | Evidence |
| --- | --- |
| 10:44:07 | Campaign starts, one reserved neutral-scale trial. |
| 11:25:58 | Last host job-progress event: published checkpoint/result at step 2944. |
| 11:26:32–11:27:03 | Monitor still observes changing completed-work markers. Raw worker inputs were not retained. |
| 11:27:33–11:36:39 | Progress age grows from 30.30 to 576.16 seconds; heartbeat continues advancing. |
| 11:36:47 | Host receives native `interrupted` result: published-fence watchdog, fence 113834 unchanged for 600806 ms. Host trial becomes `failed`; campaign records `stopped`. |
| 11:36:48 | Campaign service exits 1. `BindsTo` stops the monitor before another observation. |
| 13:59:27 and 14:02:02 | Read-only Portal observations list PID 952 and the same worker UUID; heartbeat remains 1514, state `failed`, completed worker step 3008. |

[Timeline reconstruction](timeline.json) accounts for all 104 monitor snapshots;
[campaign](campaign-journal.txt), [monitor](monitor-journal.txt) and
[tunnel](tunnel-journal.txt) journals independently bind supervision events.
The monitor contains derived runtime ages but not the raw worker samples, so a
bit-for-bit replay of the original temporal inputs is impossible. This is a
telemetry gap, not evidence that the original inputs were invalid.

## Findings and priority

| Priority | Finding | Evidence and limit |
| --- | --- | --- |
| P0 | Checkpoint publication stall is the leading location. | Worker progress is 3008; committed checkpoint is 2944; `checkpoint.json.tmp` is zero bytes. The trainer publishes progress after `Model::step`, then every 64 steps writes its checkpoint. `atomic_json` opens/truncates the temporary before `value.dump()` and output. This localizes the pending path to encoding/output/publication, but cannot identify a function or thread wait without a stack/phase trace. |
| P0 | Watchdog metadata overstates GPU attribution. | `PublishedFenceWatch` observes active job plus an unchanged published fence, not an in-flight GPU request. [Native reproducer](watchdog-classification.json) emits the same `gpu_wait_timeout` with zero GPU calls; `requested_fence=0` is a sentinel. CPU serialization or I/O can trigger this classification. |
| P0 | Runtime exit postcondition is not observed. | Same process and failed worker remain listed hours after fault. This does not establish whether `ExitProcess` blocked, the process is suspended, or Portal retains a process object. A process/thread inspection is required. The lock-free synthetic stall used in acceptance does not cover all blocked-thread states. |
| P0 | Legacy readiness can report a held Btrfs lock as free. | [Real lock reproduction](lock-reproduction.json): `stat` device 0:51 differs from kernel lock device 00:24 for the same resolved file/inode. Current liveness returns `lock_unverified`; legacy returns `unowned_legacy_lock` despite independently proven contention. This is a launch-safety defect, not the cause of this native stop. |
| P1 | Last monitor snapshot hides terminal failure. | Actual journal plus [isolated reproduction](monitor-exit-reproduction.json) show SIGTERM between polls leaves `running` in the latest JSON. No final observation is persisted. |
| P1 | Status loses useful distinctions. | Host labels the recoverable native interruption `failed`; native fault remains preserved in `xbox/result.json`. CLI does not classify `lock_unverified` as an issue and does not fetch failed worker metadata for terminal native results. |

The watchdog did interrupt the published result and preserve the checkpoint. That
containment evidence does not prove the original stall was fixed by package 0.1.0.98.
The original release evidence remains immutable; its scope is now explicitly limited.

### Competing causes

- **Checkpoint encoding/allocation/output:** strongest location, from completed
  step 3008 and the empty temporary. Missing: before/after phase markers and thread
  stack. Neither the serializer nor filesystem can yet be blamed individually.
- **D3D call blocked:** not demonstrated by the fault classification. The last
  completed model step and checkpoint temporary weaken attribution to an active
  GPU wait at the stop. Missing: submitted/requested/completed fence and API-entry
  markers independent of the published progress callback.
- **Whole-app suspension:** advancing heartbeat during the approximately ten-minute
  stall weighs against continuous whole-process suspension in that interval.
  Lifecycle transitions or later suspension remain unproven because event records
  are absent; the current process list is not a lifecycle trace.
- **Host quota, transport or observer failure:** no transport alarms or tunnel exit
  in the incident interval; the host received heartbeat/progress and the terminal
  result. Campaign CPU consumption was 21.070 seconds over 52m42s. Host quota can
  affect evaluation duration, but it does not explain the native checkpoint stall.
- **Exit deadlock:** plausible, unconfirmed. The registered callback calls
  `ExitProcess(1)` after publication. Microsoft documents a potential deadlock if
  DLL detach needs a lock held by a terminated thread; it also notes that a process
  object can outlive exit. Neither mechanism is distinguished by Portal listing
  alone ([official reference](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-exitprocess)).

## Recovery assessment

[All three remote descriptors](remote-assets.json) match downloaded bytes and
SHA-256: checkpoint plus branches ending at 879 and 1758. Owner payload, submitted
job, acceptance and initialization/data/index assets match. No final-test selection
or reservation exists for this campaign.

[Offline native restore](native-checkpoint-validation.json) passes: step **2944**,
stream position **94208**, 20 tensors, exact checkpoint reconstruction including
optimizer moments. Both branch models load. Altered stream, recipe and negative
second moment are rejected. This validates admissibility, not a resumed trajectory.
The uncommitted step 3008 and empty temporary are not recovery sources.

The host `failed` label does not itself prevent explicit recovery: `cmd_resume`
allows non-completed bound Xbox trials and `Portal.recover` checks the native
result and idle worker. It does not automatically requeue this trial. The current
failed/stale worker blocks recovery. A future explicit operation must first
establish the same-package live idle replacement and native reconciliation, then
reverify bindings before resuming the committed checkpoint. No recovery is ready
to execute on the current worker.

## Validation and reproducibility

- [100 targeted tests pass](targeted-tests.txt): runtime observation, transport
  failure, heartbeat without work, recovery ownership, preflight and status.
- The existing live-lock unit test [passes on tmpfs](lock-unit-tmpfs.txt) and
  [fails on this Btrfs workspace](lock-unit-btrfs.txt). The failure is the measured
  baseline defect. The previous passing tmpfs/CI tests did not cover this mount.
- `diagnose_locks.py --root <host-repo>` runs isolated held/released/wrong-owner,
  stale-identity and dead-owner cases on both filesystems. No campaign lock changes.
- `reproduce_monitor_exit.py --root <host-repo>` exercises the existing watch loop
  with a disposable child process and files; no campaign service is stopped.
- Build `check_checkpoint.cpp` with C++17, backend `src/cpp/e0` and `vendor` include
  paths, and the matching `libxgpu_e0.a -lcrypto -pthread`. Arguments are the saved
  job, original initialization, checkpoint and two branches. This only restores;
  it never calls a training or GPU kernel. Heavy commands ran through `bg`.
- Build `check_watchdog.cpp` with C++17 and backend `src/cpp` include path. It tests
  only the existing published-fence classification.

## Corrections and discriminating experiment

The [architecture proposal](../../adr/proposals/e0-incident-observability.md) is
unaccepted. No runtime fix or changed experiment is included in this analysis.

1. Correct lock authority in the shared host layer and make legacy readiness
   fail closed when ownership cannot be proven. Acceptance: real Btrfs/tmpfs
   held/free/wrong-owner tests; unknown observations never permit a new campaign.
2. Capture terminal monitor state independently of campaign service lifetime;
   persist raw worker inputs and distinguish snapshot age from live observation.
   Acceptance: exit between polls, transport loss at exit, terminal fault, bounded
   observer shutdown and no recovery/control side effects.
3. Instrument native checkpoint encode/write/replace and GPU API entry/exit with
   independent phase, monotonic timestamps and actual in-flight fence identity.
   Separate lack of job progress from a proven GPU wait; test CPU-only pauses and
   GPU waits separately. Require durable fault evidence and actual termination
   proof, including a functional fault with held runtime locks.
4. Before another scientific attempt, qualify instrumentation and exit behavior in
   an isolated functional package. A controlled checkpoint-publication test is the
   first discriminator: same model/state size and checkpoint cadence; one changed
   variable per trial. Capture thread stacks where supported and hash artifacts
   against the accepted CPU/reference result. A changed package cannot resume
   this frozen campaign; any retirement/new freeze must be explicit.

Analysis closes with a localized path, confirmed host defects, verified recovery
assets and explicit missing evidence. It does not close E0 or claim a root-cause fix.
