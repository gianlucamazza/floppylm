# Status

The only page that states live project state. Update it — and nothing else — on every package
bump or campaign start/stop. Last updated: **2026-10-01**.

| Item                 | State                                                                                                                                                                                   |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Thesis               | [concept v0.2](concept.md), **specified**                                                                                                                                               |
| E0 v2 software       | **measured**: harness, gates and smoke ([evidence](evidence/README.md))                                                                                                                 |
| S1–S10, scale policy | accepted ([ADR 0008](adr/0008-e0-numeric-protocol.md), [ADR 0011](adr/0011-e0-row-scale-selection.md))                                                                                  |
| Xbox package         | **installed** `GianlucaMazza.XgpuE0_0.1.0.66_x64__g0p5dcfz4t9z4`, `device.json` ready, GPU true, source `f8c9f69d`. 0.1.0.65 numerical gates passed (36 fixtures/kernels/optimizer/resume); throughput interrupted when 0.1.0.66 replaced it. 0.1.0.66 acceptance pending. fdab67 stays bound to 0.1.0.56. |
| E0 campaign          | `e0-20261001T163456Z-fdab67` host **stopped**; 001 native interrupt at trunk 1583 (checkpoint `afcc2c98`, branch 879); `--recover` not launched. Do not resume fdab67 onto 0.1.0.65. |
| Previous campaign    | `e0-20261001T090514Z-4236fd` (0.1.0.28), **stopped** 2026-10-01 13:44 CEST at `neutral-scale`: both row16 seeds not saturated — [record](evidence/e0-v2/campaigns/e0-20261001T090514Z-4236fd/notes.md) |
| E0 saturation gate   | recorded, not an eligibility gate ([ADR 0015](adr/0015-e0-fixed-data-frontier.md)); campaign `fdab67` launched |
| E0 quality results   | pending                                                                                                                                                                                 |
| E1 qualification     | CPU functional qualification **measured** ([ADR 0013](adr/0013-e1-functional-qualification.md), [evidence](evidence/e1-qualification-20261001/notes.md)); Xbox vector qualification pending |
| Scientific E1–E4     | **specified**, gated by E0 and an accepted E1 protocol ([roadmap](roadmap.md), [completion plan](completion-plan.md)) |

Campaign host is stopped. Inspect (read-only):

```bash
python scripts/e0_status.py --campaign runs/e0-campaign-20261001-0015
python scripts/e0_status.py --campaign runs/e0-campaign-20261001-0015 --xbox
```

Do not resume `fdab67` onto 0.1.0.65. Do not edit `src/` or `experiments/` until a new accepted package and campaign decision.

## Next (campaign `fdab67` host stopped; package 0.1.0.65 installed, acceptance pending)

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

1. Do not resume `fdab67` onto 0.1.0.65. Accept the new package before any new scientific campaign.
2. Obtain independent GPU attribution: the global idle counter stayed high in twelve
   controlled modes, including CoreWindow without XAML/D3D12. GPU reduction is **unvalidated**.
3. Rename the local working directory to `floppylm` at a session boundary, then
   `git worktree repair` and move the Claude project memory path.

Status vocabulary: **specified** (written, not executed), **stub**, **running**, **stopped** (halted
deliberately, kept as a record), **measured**
(an evidence file owns the number), **killed** (an F\* fired), **won't run**.
