# Status

The only page that states live project state. Update it — and nothing else — on every package
bump or campaign start/stop. Last updated: **2026-10-02**.

| Item                 | State                                                                                                                                                                                   |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Thesis               | [concept v0.2](concept.md), **specified**                                                                                                                                               |
| E0 v2 software       | **measured**: harness, gates and smoke ([evidence](evidence/README.md))                                                                                                                 |
| S1–S10, scale policy | accepted ([ADR 0008](adr/0008-e0-numeric-protocol.md), [ADR 0011](adr/0011-e0-row-scale-selection.md))                                                                                  |
| Xbox package         | **accepted** `GianlucaMazza.XgpuE0_0.1.0.86_x64__g0p5dcfz4t9z4` source `12251a7` CI [36985816615](https://github.com/gianlucamazza/xbox-gpu-training/actions/runs/36985816615) ([PR #34](https://github.com/gianlucamazza/xbox-gpu-training/pull/34) drop EE, keep DisplayRequest). Evidence [xbox-e0-20261002-086](evidence/xbox-e0-20261002-086/notes.md). Shader CSO unchanged. Bit-identical to 0.1.0.56/0.1.0.68/0.1.0.80. |
| E0 campaign          | **running** `e0-20261002T090742Z-2fe64f` recovered on 0.1.0.86 (`scripts/e0_recover.py` → unit `floppylm-e0-campaign-20261002-086`). Trial `000` completed; S3 repair (`d_ff` 400) native running past trunk 2496 toward 4T (3568). Frozen FloppyLM `5106719`. Previous `40a67c` stays on 0.1.0.80. |
| Previous campaign    | `e0-20261001T163456Z-fdab67` (0.1.0.56) **stopped**, 001 incomplete; do not resume. Before that, `e0-20261001T090514Z-4236fd` (0.1.0.28) stopped unsaturated — [record](evidence/e0-v2/campaigns/e0-20261001T090514Z-4236fd/notes.md) |
| E0 saturation gate   | recorded, not an eligibility gate ([ADR 0015](adr/0015-e0-fixed-data-frontier.md)) |
| Host recovery        | [ADR 0017](adr/0017-runtime-liveness.md) merged ([PR #7](https://github.com/gianlucamazza/floppylm/pull/7)); paired with accepted 0.1.0.86. |
| E0 quality results   | pending                                                                                                                                                                                 |
| E1 qualification     | CPU functional qualification **measured** ([ADR 0013](adr/0013-e1-functional-qualification.md), [evidence](evidence/e1-qualification-20261001/notes.md)); Xbox vector qualification pending |
| Scientific E1–E4     | **specified**, gated by E0 and an accepted E1 protocol ([roadmap](roadmap.md), [completion plan](completion-plan.md)) |

Campaign host is running after explicit recover of the S3 repair from native checkpoint 2496 (GPU fence hang, then Xbox sign-in 80004005 on sandbox XDKS.1; sandbox set to RETAIL, DottorQ signed in, recover). Inspect (read-only). `src/` and `experiments/` are frozen at launch commit `5106719`. Companion `loss_series` (FloppyLM [PR #8](https://github.com/gianlucamazza/floppylm/pull/8), xbox [PR #35](https://github.com/gianlucamazza/xbox-gpu-training/pull/35)) is on main and **not installed**; 2fe64f stays on 0.1.0.86:

```bash
python scripts/e0_status.py --campaign runs/e0-campaign-20261002-086
python scripts/e0_status.py --campaign runs/e0-campaign-20261002-086 --xbox
```

Do not resume `fdab67` onto 0.1.0.65, 0.1.0.66, 0.1.0.68, 0.1.0.76, 0.1.0.80, 0.1.0.84, or 0.1.0.86.
Do not continue `40a67c` onto 0.1.0.84 or 0.1.0.86. Do not recover `2fe64f` onto a later package.

## Next (campaign `2fe64f` recovered on 0.1.0.86; `src/`/`experiments/` frozen)

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

1. Let campaign `2fe64f` run. Keep XgpuE0 in the foreground. Do not install a
   new Xbox package, edit `src/` or `experiments/`, resume `fdab67`, or
   continue `40a67c`. Explicit recover stays on 0.1.0.86 only. The reconstructed
   loss chart lands on the next package after this campaign.
2. Obtain independent GPU attribution: the global idle counter stayed high in twelve
   controlled modes, including CoreWindow without XAML/D3D12. GPU reduction is **unvalidated**.
3. Rename the local working directory to `floppylm` at a session boundary, then
   `git worktree repair` and move the Claude project memory path.

Status vocabulary: **specified** (written, not executed), **stub**, **running**, **stopped** (halted
deliberately, kept as a record), **measured**
(an evidence file owns the number), **killed** (an F\* fired), **won't run**.
