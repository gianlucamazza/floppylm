# Status

The only page that states live project state. Update it — and nothing else — on every package
bump or campaign start/stop. Last updated: **2026-10-10**.

## Where this stands

E0 campaign `e0-20261009T174028Z-94847b` completed at 2026-10-10T10:02:53Z on
the accepted Xbox package 0.1.0.109. Host freeze `96a3054`, unit
`floppylm-e0-campaign-20261009T174006Z` exited 0, under
[ADR 0020](adr/0020-target-window-parity.md) and
[ADR 0022](adr/0022-paired-campaign-on-109.md). Ten paired cells are eligible.
Ternary seeds 0, 1 and 3 needed one S3 repair; seeds 2 and 4 were eligible on
the first pack. 2-bit seeds 0–4 were eligible on the first pack, with submitted
`d_ff` 205 and the stored nominal width still 193. The ten counted cells are
frozen in
[the selection](evidence/e0-v2/selections/e0-20261009T174028Z-94847b.json).
Byte parity and rank stability passed. The
[final test](evidence/e0-v2/selections/e0-20261009T174028Z-94847b.test.json)
records ternary minus 2-bit −0.023838 bpb, sample SD 0.013733, frozen gate
0.026322. That difference is inside the gate. The
[report](evidence/e0-v2/campaigns/e0-20261009T174028Z-94847b/notes.md) marks
the baseline complete and keeps both stored arms. Roadmap gate 4 is recorded
in the [review](evidence/e0-review-20261010-94847b/notes.md). The 1/16 pilot
proposal stays unaccepted. Campaign
`e0-20261009T150330Z-87686a` stays stopped on 0.1.0.105.
Run `87686a-000` failed at trunk step 64 with `JSON write failed`, wrote no
branch, and is not recovered. `766d4b` cell `031` stays closed.

Campaign `766d4b` stays stopped at 2026-10-09T12:07:22Z. It opened at `grid-ternary` under
ADR 0020, host freeze `11d608a`, unit `floppylm-e0-campaign-20261008T063808Z`. Cell `031`,
paired ternary seed 1, failed on the console at trunk step 128 with `JSON write failed`
and is not a result. Do not recover it. Do not start `floppylm-e0-campaign-20261008T063808Z`
or `floppylm-e0-campaign-20261007T164709Z`. Its ternary grid is byte-comparable and
rank-stable at `d` 80, 4 layers, `d_ff` 262 (1.4599/1.3375/1.2522). Its 2-bit grid is
byte-comparable and rank-stable at nominal `d_ff` 193; trained cell 027 submitted `d_ff` 205
and reached 1.4914/1.3663/1.2766. Paired ternary seed 0 repeated the ternary selection.
Cells 000–007 repeat the `c58a86` cooldown artifacts. Cell 010 repeats `c58a86-104-repair`.
Cells 008, 009, 011 and 012 do not repeat the earlier nominal or repaired artifacts.
Campaign `e0-20261004T103838Z-c58a86` stays stopped. Its ternary set was refused
and is not a decision.

The scale choice is closed. `row8log` is lower than `row16` at T, 2T and 4T: mean val bpb
1.5076/1.3856/1.3059 against 1.5127/1.3933/1.3121. The activation choice is closed. Both gelu
seeds are eligible only after the S3 repair (`d_ff` 424) and repeat the `row8log` repairs:
seed 0 is 1.5039/1.3837/1.3047, seed 1 is 1.5112/1.3876/1.3070. Both SwiGLU seeds are
eligible only after the S3 repair (`d_ff` 280). Seed 0 is 1.4568/1.3403/1.2615, seed 1 is
1.4694/1.3544/1.2793, and the mean is 1.4631/1.3473/1.2704. Both ReLU² seeds are eligible
only after the S3 repair. Seed 0 is 1.4749/1.3597/1.2807 at `d_ff` 424. Seed 1 is
1.4790/1.3679/1.2837 at `d_ff` 423. The ReLU² mean is 1.4770/1.3638/1.2822, below gelu and
above SwiGLU at T, 2T and 4T. The recorded choice is SwiGLU at nominal `d_ff` 274.

Ternary tuning is closed, seed 0, on that nominal shape. The eligible repairs at lr 0.01
are delta 0.5 at `d_ff` 281 (val bpb 1.4602/1.3481/1.2720) and delta 0.7 at `d_ff` 288
(1.4619/1.3533/1.2792). The delta 0.5 repair is the lowest of the six tuning cells at T,
2T and 4T, and the grid used lr 0.01, delta 0.5, wd 0.1. It stays above the neutral
SwiGLU seed 0 repair (1.4568/1.3403/1.2615) at all three horizons.

On `c58a86` the ternary grid is closed. All thirteen shapes are individually inside ±1% of 85937.5
bytes. Selection refused the set under the rule then in force: 4T size runs from 85098
to 85982 bytes, and `max/min − 1` is 1.0388% ([ADR 0005](adr/0005-e0v2-protocol.md) §1).
No ternary shape is selected. The diagnostic minimum at T, 2T and 4T is `d` 80, 4 layers,
`d_ff` 262 (1.4599/1.3375/1.2522) and is not a decision. 2-bit did not start. The
shared-target window is accepted as [ADR 0020](adr/0020-target-window-parity.md).
The successor trained a new ternary grid under that rule and under
[ADR 0019](adr/0019-host-init-pack.md). It does not resume `c58a86`.
All thirteen cells are eligible and indexed. The comparison is byte-comparable.
The stored ternary phase selection is `d` 80, 4 layers, `d_ff` 262
(1.4599/1.3375/1.2522), also the minimum at T and 2T. The gap to the neutral
SwiGLU seed 0 repair at 4T (1.2615) is 0.009. The two SwiGLU seeds differ by
0.018. The 2-bit grid later closed byte-comparable and rank-stable. Its stored
phase selection is the neutral shape, `d` 96, 3 layers, nominal `d_ff` 193,
lr 0.003, wd 0.1, at 1.4914/1.3663/1.2766. The campaign then stopped in
`paired-seeds`: cell `031`, ternary seed 1, failed at trunk step 128 with
`JSON write failed`. Do not recover that failed job.
Campaign `e0-20261009T150330Z-87686a` stopped on its first fresh seed and is not a result.
It does not resume `c58a86` or `766d4b`. Campaign `e0-20261009T174028Z-94847b`
is the [ADR 0022](adr/0022-paired-campaign-on-109.md) successor. It completed
at 2026-10-10T10:02:53Z. All ten paired cells are eligible, the ten hashes are
frozen, and the final test difference is inside the frozen gate. Both stored
arms remain in the baseline. Roadmap gate 4 is recorded in the
[review](evidence/e0-review-20261010-94847b/notes.md).
The generated report records 29 trials and 21 byte repairs, and no completed
baseline: [campaign report](evidence/e0-v2/campaigns/e0-20261004T103838Z-c58a86/notes.md).

E1–E4 stay specified. The gate 4 review of the completed E0 report is recorded.
They wait for an accepted E1 protocol.
The 1/16 pilot rules that do not name the scalar winner are proposed in
[the pilot proposal](adr/proposals/e1-1-16-pilot.md) and are not accepted.
Host init-pack is on main as [ADR 0019](adr/0019-host-init-pack.md)
([PR #22](https://github.com/gianlucamazza/floppylm/pull/22), `328c906`). It applies
to a future fresh attempt. It is not part of `c58a86` and does not apply to the cells
already measured. Run `87686a-000` failed before a branch.

The table is the operator record: package identity, campaign ids, and stopped jobs. The
paragraph above is the quality state. Measured cells are in the
[evidence index](evidence/README.md).

| Item                 | State                                                                                                                                                                                   |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Thesis               | [concept v0.2](concept.md), **specified**                                                                                                                                               |
| E0 v2 software       | **measured**: harness, gates and smoke ([evidence](evidence/README.md))                                                                                                                 |
| S1–S10, scale policy | accepted ([ADR 0008](adr/0008-e0-numeric-protocol.md), [ADR 0011](adr/0011-e0-row-scale-selection.md))                                                                                  |
| Xbox package | **accepted** `GianlucaMazza.XgpuE0_0.1.0.109_x64__g0p5dcfz4t9z4`, source `961ccc2ab2e800eb25ea1ea33c1af1a46389ee59`, CI [37959310043](https://github.com/gianlucamazza/xbox-gpu-training/actions/runs/37959310043). [Evidence](evidence/xbox-e0-20261009-109/notes.md): full gates, bit-identical 38/38 versus [0.1.0.105](evidence/xbox-e0-20261004-105/notes.md). Shader CSO unchanged. A failed JSON open reports the path and Win32 code and retries only sharing and lock violations. `87686a` and `766d4b` cell `031` stay stopped and are not resumed onto this package. |
| E0 campaign | **completed** `e0-20261009T174028Z-94847b` at 2026-10-10T10:02:53Z on `0.1.0.109`, host freeze `96a3054`, protocol ADR 0020, [ADR 0022](adr/0022-paired-campaign-on-109.md), unit `floppylm-e0-campaign-20261009T174006Z` exited 0. Ten paired cells are eligible: ternary seeds 0, 1 and 3 after one S3 repair, ternary seeds 2 and 4 and 2-bit seeds 0–4 on the first pack. 2-bit submitted `d_ff` is 205; the stored nominal width stays 193. The ten counted hashes are frozen. Byte parity and rank stability passed. Final test ternary minus 2-bit −0.023838 bpb, sample SD 0.013733, frozen gate 0.026322; the difference is inside the gate. The [report](evidence/e0-v2/campaigns/e0-20261009T174028Z-94847b/notes.md) marks the baseline complete and keeps both stored arms. [Gate 4 review](evidence/e0-review-20261010-94847b/notes.md) recorded; the 1/16 pilot proposal stays unaccepted. `87686a` stays stopped on `0.1.0.105`: run `87686a-000` failed at trunk step 64 with `JSON write failed`, wrote no branch, and is not recovered. Do not start `floppylm-e0-campaign-20261009T150327Z`, `floppylm-e0-campaign-20261008T063808Z`, or `floppylm-e0-campaign-20261007T164709Z`. `766d4b` cell `031` stays closed. `c58a86` stays stopped. [Launch record](evidence/e0-launch-20261009-109/notes.md). |
| Previous E0 campaign | **stopped** `e0-20261004T082243Z-31972d` at 2026-10-04T09:28:41Z on `0.1.0.102` (freeze `4de17b3`). `progress_stall` at published trunk 2112. Preserved checkpoint sha256 `3fb5d57cb03591afcbf90054c97544f6abcb6e075c1a297139335d6ae0c86483`, 23713680 bytes. Not resumed onto `0.1.0.105`. Before that, `e0-20261002T191632Z-ca781f` on 0.1.0.93 (2026-10-03T00:04:51Z). Trial `000` **eligible** (fill 0.9990/0.9998/1.0012, val bpb 1.5155/1.3951/1.3160). Trial `001` **eligible** after S3 `d_ff` 400 (fill 0.9996/1.0007/1.0009, val bpb 1.5100/1.3916/1.3082, bytes 85904/86000/86015). Trial `002` row8log **interrupted** at stop, not a result. Do not resume `ca781f` onto 0.1.0.95. Frozen FloppyLM `3c3c79d`. |
| Previous campaign    | `e0-20261001T163456Z-fdab67` (0.1.0.56) **stopped**, 001 incomplete; do not resume. Before that, `e0-20261001T090514Z-4236fd` (0.1.0.28) stopped unsaturated — [record](evidence/e0-v2/campaigns/e0-20261001T090514Z-4236fd/notes.md) |
| E0 saturation gate   | recorded, not an eligibility gate ([ADR 0015](adr/0015-e0-fixed-data-frontier.md)) |
| Host recovery        | [ADR 0017](adr/0017-runtime-liveness.md) merged ([PR #7](https://github.com/gianlucamazza/floppylm/pull/7)); paired with accepted 0.1.0.93. |
| E0 quality results   | scale selected `row8log`; MLP selected SwiGLU, nominal `d_ff` 274; ternary tuning closed at lr 0.01, delta 0.5; `c58a86` ternary grid refused; `766d4b` stopped in `paired-seeds` on 2026-10-09; ternary phase selection `d` 80, 4 layers, `d_ff` 262; 2-bit phase selection is the neutral shape at 4T val bpb 1.2766; `87686a` stopped on its first fresh seed with no branch; `94847b` completed at 2026-10-10T10:02:53Z with ten eligible paired cells, a ten-hash freeze, and a final-test difference inside the frozen gate; both stored arms remain in the baseline; roadmap gate 4 is recorded and the 1/16 pilot proposal stays unaccepted |
| E1 qualification     | CPU functional qualification **measured** ([ADR 0013](adr/0013-e1-functional-qualification.md), [evidence](evidence/e1-qualification-20261001/notes.md)); Xbox vector qualification has not started: no vector executor exists to compare with that oracle |
| Scientific E1–E4     | **specified**, gated by E0 and an accepted E1 protocol ([roadmap](roadmap.md), [completion plan](completion-plan.md)) |

`31972d` stays stopped on `0.1.0.102`. `a8d8b9` stays stopped on `0.1.0.98`. `ca781f` stays stopped on `0.1.0.93`. Completed 4T jobs on `0.1.0.105` passed trunk 896 and 2112 without a `progress_stall`. [E1 book budget](adr/proposals/e1-1-16-book-budget.md) stays a proposal.

```bash
python scripts/e0_status.py --campaign runs/e0-campaign-20261007-105
python scripts/e0_status.py --campaign runs/e0-campaign-20261007-105 --xbox
```

Do not resume `fdab67` onto 0.1.0.65, 0.1.0.66, 0.1.0.68, 0.1.0.76, 0.1.0.80, 0.1.0.84, 0.1.0.86, 0.1.0.93, or 0.1.0.95.
Do not continue `40a67c` onto a later package. Do not recover `2fe64f` or `ca781f` onto 0.1.0.95.

## Recorded stop (a8d8b9; recovery was not executed)

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
