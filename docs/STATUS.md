# Status

The only page that states live project state. Update it — and nothing else — on every package
bump or campaign start/stop. Last updated: **2026-10-04**.

| Item                 | State                                                                                                                                                                                   |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Thesis               | [concept v0.2](concept.md), **specified**                                                                                                                                               |
| E0 v2 software       | **measured**: harness, gates and smoke ([evidence](evidence/README.md))                                                                                                                 |
| S1–S10, scale policy | accepted ([ADR 0008](adr/0008-e0-numeric-protocol.md), [ADR 0011](adr/0011-e0-row-scale-selection.md))                                                                                  |
| Xbox package | **installed, qualification running** `GianlucaMazza.XgpuE0_0.1.0.102_x64__g0p5dcfz4t9z4`, source `4b8f51c3a5ee985ce8fcb71327f0ffc88e487545`, CI [37186655285](https://github.com/gianlucamazza/xbox-gpu-training/actions/runs/37186655285). Acceptance, watchdog (`progress_stall`, requested fence 0, 600819 ms) and worker passed. Recovery, lifecycle, benchmark and bit identity are still open. Shader CSO unchanged versus 0.1.0.98. The last accepted package remains [0.1.0.98](evidence/xbox-e0-20261003-098/notes.md) until those gates close. |
| E0 campaign | **stopped** `e0-20261003T104407Z-a8d8b9` at 2026-10-03T11:36:47Z; first trial interrupted by the published-fence watchdog. Checkpoint 2944 and two branches verified; worker reached 3008 before checkpoint publication stalled. Frozen host source `8867ec6`, package `0.1.0.98`. [Incident analysis](evidence/e0-incident-20261003/notes.md). |
| Previous E0 campaign | **stopped** `e0-20261002T191632Z-ca781f` on 0.1.0.93 (2026-10-03T00:04:51Z). Trial `000` **eligible** (fill 0.9990/0.9998/1.0012, val bpb 1.5155/1.3951/1.3160). Trial `001` **eligible** after S3 `d_ff` 400 (fill 0.9996/1.0007/1.0009, val bpb 1.5100/1.3916/1.3082, bytes 85904/86000/86015). Trial `002` row8log **interrupted** at stop, not a result. Do not resume `ca781f` onto 0.1.0.95. Frozen FloppyLM `3c3c79d`. |
| Previous campaign    | `e0-20261001T163456Z-fdab67` (0.1.0.56) **stopped**, 001 incomplete; do not resume. Before that, `e0-20261001T090514Z-4236fd` (0.1.0.28) stopped unsaturated — [record](evidence/e0-v2/campaigns/e0-20261001T090514Z-4236fd/notes.md) |
| E0 saturation gate   | recorded, not an eligibility gate ([ADR 0015](adr/0015-e0-fixed-data-frontier.md)) |
| Host recovery        | [ADR 0017](adr/0017-runtime-liveness.md) merged ([PR #7](https://github.com/gianlucamazza/floppylm/pull/7)); paired with accepted 0.1.0.93. |
| E0 quality results   | pending                                                                                                                                                                                 |
| E1 qualification     | CPU functional qualification **measured** ([ADR 0013](adr/0013-e1-functional-qualification.md), [evidence](evidence/e1-qualification-20261001/notes.md)); Xbox vector qualification pending |
| Scientific E1–E4     | **specified**, gated by E0 and an accepted E1 protocol ([roadmap](roadmap.md), [completion plan](completion-plan.md)) |

Package `0.1.0.102` is installed. Qualification resumed from recovery after the host harness accepted an interrupted runner return (`555a865`). Acceptance, the published-fence probe and the worker gate stand. Lifecycle, benchmark and bit identity have not closed. Campaign `a8d8b9` stays stopped on `0.1.0.98` and is not migrated. The next scientific campaign needs this package's closed gates and a new source freeze. Campaign `ca781f` remains stopped and published. Architecture notes stay proposals: [S3 fill](adr/proposals/e0-fill-aware-solver.md), [E1 book budget](adr/proposals/e1-1-16-book-budget.md).

```bash
python scripts/e0_status.py --campaign runs/e0-campaign-20261003-098
python scripts/e0_status.py --campaign runs/e0-campaign-20261003-098 --xbox
```

Do not resume `fdab67` onto 0.1.0.65, 0.1.0.66, 0.1.0.68, 0.1.0.76, 0.1.0.80, 0.1.0.84, 0.1.0.86, 0.1.0.93, or 0.1.0.95.
Do not continue `40a67c` onto a later package. Do not recover `2fe64f` or `ca781f` onto 0.1.0.95.

## Next (E0 stopped; diagnosis complete, recovery not executed)

Done since the stop: xbox-gpu-training consumes the whole published contract set (PR #22, #20);
Xbox execution moved to `floppylm_xbox` with generic Device Portal settings
and a pinned certificate (`~/.config/floppylm/xbox.env`, see the [runbook](operations/xbox-e0.md));
English run notes; no `bg` instruction left in the harness; E1 qualification code merged;
protected final-test / recovery audit; [ADR 0014](adr/0014-durable-xbox-publication.md)
publication journal; [ADR 0015](adr/0015-e0-fixed-data-frontier.md) fixed-data frontier.

Completed release: dashboard package signed and installed with pinned TLS; full acceptance,
worker/recovery/suspension tests, exact numerical comparison and screenshot recorded in
[both-repository release evidence](evidence/xbox-e0-20261001-dashboard/notes.md).
Backend ADR 0005 and canonical documentation links were merged in PR #27.

1. Review the [incident findings and correction gates](evidence/e0-incident-20261003/notes.md).
   Preserve `a8d8b9` sources, package and artifacts. Recovery requires an explicitly
   restored live idle worker on the same package; no automatic resume or new trial.
   The [observability proposal](adr/proposals/e0-incident-observability.md) is not accepted.
   Historical campaigns remain retired; E1 and solver proposals remain separate.
2. Obtain independent GPU attribution: the global idle counter stayed high in twelve
   controlled modes, including CoreWindow without XAML/D3D12. GPU reduction is **unvalidated**.
3. Rename the local working directory to `floppylm` at a session boundary, then
   `git worktree repair` and move the Claude project memory path.

Status vocabulary: **specified** (written, not executed), **stub**, **running**, **stopped** (halted
deliberately, kept as a record), **measured**
(an evidence file owns the number), **killed** (an F\* fired), **won't run**.

## ADR 0018 qualification work

Selection/reporting corrections and bounded host observation are integrated
(PRs #13 and #14). Merged backend PR #39 supplies the functional probe
and verified resume normalization. Package `0.1.0.98` passed the complete
[hardware qualification](evidence/xbox-e0-20261003-098/notes.md) through Odroid.
The [incomplete 0.1.0.96 attempt](evidence/xbox-e0-20261003-096-incomplete/notes.md)
is retained: it exposed the native resume-binding defect, repaired before final
qualification. No historical campaign may be resumed onto this package. No new
scientific campaign is authorized by this work. The original stall's initiating
cause remains unproven.

## New E0 preparation

The read-only preflight and [launch packet](operations/e0-launch-packet.md) prepare a new
source freeze under the existing scientific protocol. Readiness is timestamped and
must be rechecked at launch; preparation does not authorize or start a campaign.

The [2026-10-03 readiness observation](evidence/e0-readiness-20261003/notes.md) passed
through Odroid on the unchanged accepted package. It is preparation evidence, not
a campaign start or final-test reservation.

## Authorized E0 launch

On 2026-10-03 the owner explicitly confirmed the new E0 campaign, including the
reserved final test conditional on passing gates. The [launch record](evidence/e0-launch-20261003/notes.md)
binds preflight, source freeze, exact package, supervised services and observed
GPU progress. This authorization supersedes the preparation-only scope above;
it does not authorize an E1 protocol or continuation after a failed scientific gate.

## Incident observation (2026-10-03)

The campaign stopped at 11:36:47Z. The monitor was stopped by its systemd dependency
9 seconds after its last `running` observation; `monitor.json` is historical, not
live status. Read-only observations at 13:59:27Z and 14:02:02Z found the same failed
worker, unchanged heartbeat and still-listed PID 952. Checkpoint/branch integrity
and native offline restore passed. No restart, resume, deployment or final-test
evaluation was performed during diagnosis. The initiating function is not proven;
the checkpoint serialization/write path is the leading localized hypothesis.
