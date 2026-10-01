# Status

The only page that states live project state. Update it — and nothing else — on every package
bump or campaign start/stop. Last updated: **2026-10-01**.

| Item                 | State                                                                                                                                                                                   |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Thesis               | [concept v0.2](concept.md), **specified**                                                                                                                                               |
| E0 v2 software       | **measured**: harness, gates and smoke ([evidence](evidence/README.md))                                                                                                                 |
| S1–S10, scale policy | accepted ([ADR 0008](adr/0008-e0-numeric-protocol.md), [ADR 0011](adr/0011-e0-row-scale-selection.md))                                                                                  |
| Xbox package         | `GianlucaMazza.XgpuE0_0.1.0.28_x64__g0p5dcfz4t9z4` (E0.1), CI run 36839565773, source `25f8bc3966ffae940658be94161d31edd83492c9` — [acceptance](evidence/xbox-e0-20261001-e01/notes.md) |
| E0 campaign          | `e0-20261001T090514Z-4236fd`, **running**, phase `neutral-scale`; state in `runs/e0-campaign-20261001-e01/`; launched with `bg`, moved live at 11:59 CEST to `app.slice/floppy-e0-campaign-e01.scope` (no CPU quota); wall times before that ran under the 1-core cap                                                                             |
| Previous campaign    | `e0-20261001T074326Z-503df0` (0.1.0.24), **stopped**, [record](evidence/e0-v2/campaigns/e0-20261001T074326Z-503df0/notes.md)                                                            |
| E0 quality results   | pending                                                                                                                                                                                 |
| E1 qualification     | CPU functional qualification **measured** ([ADR 0013](adr/0013-e1-functional-qualification.md), [evidence](evidence/e1-qualification-20261001/notes.md)); Xbox vector qualification pending; code on branch `research/e1-qualification` |
| Scientific E1–E4     | **specified**, gated by E0 and an accepted E1 protocol ([roadmap](roadmap.md), [completion plan](completion-plan.md)) |

Check the live campaign (read-only):

```bash
python scripts/e0_status.py --campaign runs/e0-campaign-20261001-e01 --xbox
```

Bound proofs: `runs/xbox-acceptance-20261001-ci36839565773/acceptance.json` and
`runs/xbox-benchmark-20261001-ci36839565773/summary.json`.

## Pending after the campaign

- Frozen sources must stay untouched while the campaign runs. Afterwards:
  - translate the generated run-note template in `experiments/e0_v2.py` (`notes_md`) to English;
  - drop the "host `bg` wrapper" instruction from the `experiments/e0_v2.py` docstring (jobs run
    under `nohup` outside `background.slice`);
  - apply the [ADR 0012](adr/0012-repo-boundaries.md) follow-ups;
  - rename the local working directory to `floppylm` (the running campaign holds absolute paths to
    the current one), then repair the `research/e1-qualification` worktree with `git worktree repair`
    and move the Claude project memory to the new path;
  - merge branch `chore/generic-config` (generic Device Portal settings) and copy the console
    credentials to `~/.config/floppylm/xbox.env` before the next Xbox job;
  - merge the code of branch `research/e1-qualification` (its docs are already on `main`; keep `main`'s versions on conflict).

Status vocabulary: **specified** (written, not executed), **stub**, **running**, **stopped** (halted
deliberately, kept as a record), **measured**
(an evidence file owns the number), **killed** (an F\* fired), **won't run**.
