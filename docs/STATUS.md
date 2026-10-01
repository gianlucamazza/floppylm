# Status

The only page that states live project state. Update it — and nothing else — on every package
bump or campaign start/stop. Last updated: **2026-10-01**.

| Item                 | State                                                                                                                                                                                   |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Thesis               | [concept v0.2](concept.md), **specified**                                                                                                                                               |
| E0 v2 software       | **measured**: harness, gates and smoke ([evidence](evidence/README.md))                                                                                                                 |
| S1–S10, scale policy | accepted ([ADR 0008](adr/0008-e0-numeric-protocol.md), [ADR 0011](adr/0011-e0-row-scale-selection.md))                                                                                  |
| Xbox package         | `GianlucaMazza.XgpuE0_0.1.0.28_x64__g0p5dcfz4t9z4` (E0.1), CI run 36839565773, source `25f8bc3966ffae940658be94161d31edd83492c9` — [acceptance](evidence/xbox-e0-20261001-e01/notes.md) |
| E0 campaign          | `e0-20261001T090514Z-4236fd` (0.1.0.28), **stopped** 2026-10-01 13:44 CEST at `neutral-scale`: both row16 seeds not saturated — [record](evidence/e0-v2/campaigns/e0-20261001T090514Z-4236fd/notes.md) |
| Previous campaign    | `e0-20261001T074326Z-503df0` (0.1.0.24), **stopped**, [record](evidence/e0-v2/campaigns/e0-20261001T074326Z-503df0/notes.md)                                                            |
| E0 saturation gate   | not met at 1/16 (Δ 2T→4T ≈ −0.08 vs 0.01, three trials); no new campaign until the owner decides the [proposal](adr/proposals/e0-saturation-proposal.md) |
| E0 quality results   | pending                                                                                                                                                                                 |
| E1 qualification     | CPU functional qualification **measured** ([ADR 0013](adr/0013-e1-functional-qualification.md), [evidence](evidence/e1-qualification-20261001/notes.md)); Xbox vector qualification pending; code on branch `research/e1-qualification` |
| Scientific E1–E4     | **specified**, gated by E0 and an accepted E1 protocol ([roadmap](roadmap.md), [completion plan](completion-plan.md)) |

The console is idle. Inspect the stopped campaign record (read-only):

```bash
python scripts/e0_status.py --campaign runs/e0-campaign-20261001-e01
```

## Next (the campaign has stopped)

Done since the stop: Xbox execution moved to `floppylm_xbox` with generic Device Portal settings
and a pinned certificate (`~/.config/floppylm/xbox.env`, see the [runbook](operations/xbox-e0.md));
English run notes; no `bg` instruction left in the harness.

1. Merge the code of `research/e1-qualification` (its docs are already on `main`; keep `main`'s
   versions on conflict) and move its `floppylm.xbox` import (`scripts/e1_cpu_profile.py`) to
   `floppylm_xbox.jobs`.
2. Publish the remaining interface contracts (checkpoint, fixture, kernels, optimizer, acceptance,
   constants, inbox protocol, device capabilities) and have xbox-gpu-training consume them.
3. Install the package from xbox-gpu-training PR #20 (on-console dashboard; `run_job` also
   publishes schedule and phase), rerun acceptance and the bit-identity comparison, record the
   evidence, then mark the PR ready.
4. Decide the [saturation proposal](adr/proposals/e0-saturation-proposal.md) before any new
   campaign.
5. Rename the local working directory to `floppylm` at a session boundary (it is this session's
   working directory), then `git worktree repair` and move the Claude project memory path.

Status vocabulary: **specified** (written, not executed), **stub**, **running**, **stopped** (halted
deliberately, kept as a record), **measured**
(an evidence file owns the number), **killed** (an F\* fired), **won't run**.
