# Status

The only page that states live project state. Update it — and nothing else — on every package
bump or campaign start/stop. Last updated: **2026-10-02**.

| Item                 | State                                                                                                                                                                                   |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Thesis               | [concept v0.2](concept.md), **specified**                                                                                                                                               |
| E0 v2 software       | **measured**: harness, gates and smoke ([evidence](evidence/README.md))                                                                                                                 |
| S1–S10, scale policy | accepted ([ADR 0008](adr/0008-e0-numeric-protocol.md), [ADR 0011](adr/0011-e0-row-scale-selection.md))                                                                                  |
| Xbox package         | **started, acceptance running** `GianlucaMazza.XgpuE0_0.1.0.84_x64__g0p5dcfz4t9z4` source `b638f0c` CI [36983478736](https://github.com/gianlucamazza/xbox-gpu-training/actions/runs/36983478736) ([PR #33](https://github.com/gianlucamazza/xbox-gpu-training/pull/33) stay-alive). Replaced 0.1.0.80. Shader CSO unchanged. `worker.json` `extended_execution=allowed`. |
| E0 campaign          | `e0-20261002T072408Z-40a67c` host **stopped**; trial `000` native **interrupted** at trunk 796 (checkpoint `f1668f86`). Bound to 0.1.0.80; do not continue onto 0.1.0.84. Explicit `--recover` stays on 0.1.0.80 only. |
| Previous campaign    | `e0-20261001T163456Z-fdab67` (0.1.0.56) **stopped**, 001 incomplete; do not resume. Before that, `e0-20261001T090514Z-4236fd` (0.1.0.28) stopped unsaturated — [record](evidence/e0-v2/campaigns/e0-20261001T090514Z-4236fd/notes.md) |
| E0 saturation gate   | recorded, not an eligibility gate ([ADR 0015](adr/0015-e0-fixed-data-frontier.md)) |
| Host recovery        | [ADR 0017](adr/0017-runtime-liveness.md) merged ([PR #7](https://github.com/gianlucamazza/floppylm/pull/7)); paired with accepted 0.1.0.80. |
| E0 quality results   | pending                                                                                                                                                                                 |
| E1 qualification     | CPU functional qualification **measured** ([ADR 0013](adr/0013-e1-functional-qualification.md), [evidence](evidence/e1-qualification-20261001/notes.md)); Xbox vector qualification pending |
| Scientific E1–E4     | **specified**, gated by E0 and an accepted E1 protocol ([roadmap](roadmap.md), [completion plan](completion-plan.md)) |

Campaign host is stopped. Inspect (read-only):

```bash
python scripts/e0_status.py --campaign runs/e0-campaign-20261002-0015
python scripts/e0_status.py --campaign runs/e0-campaign-20261002-0015 --xbox
```

Do not resume `fdab67` onto 0.1.0.65, 0.1.0.66, 0.1.0.68, 0.1.0.76, 0.1.0.80, or 0.1.0.84.
Do not continue `40a67c` onto 0.1.0.84.

## Next (campaign `40a67c` host stopped; 000 interrupted; 0.1.0.84 started)

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

1. Finish canonical acceptance of 0.1.0.84 including lifecycle. If lifecycle
   fails because Extended Execution blocked Dev Home suspend, drop EE and
   re-accept. A new ADR 0015 campaign binds 0.1.0.84 only after that gate.
   Explicit `--recover` of `40a67c` stays on 0.1.0.80 only. Do not resume `fdab67`.
2. Obtain independent GPU attribution: the global idle counter stayed high in twelve
   controlled modes, including CoreWindow without XAML/D3D12. GPU reduction is **unvalidated**.
3. Rename the local working directory to `floppylm` at a session boundary, then
   `git worktree repair` and move the Claude project memory path.

Status vocabulary: **specified** (written, not executed), **stub**, **running**, **stopped** (halted
deliberately, kept as a record), **measured**
(an evidence file owns the number), **killed** (an F\* fired), **won't run**.
