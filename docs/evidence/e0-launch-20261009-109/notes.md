# E0 campaign launch on package 0.1.0.109

The owner approved one new paired campaign after ADR 0022. This record is that
campaign. It is not a resume of `87686a` or of `766d4b`, and it is not a result.

## Frozen identity

- Campaign: `e0-20261009T174028Z-94847b`, created 2026-10-09T17:40:28Z.
- Directory: `runs/e0-campaign-20261009-109`.
- Unit: `floppylm-e0-campaign-20261009T174006Z.service`, active at launch.
- Host source: `96a3054a2b0a0f8478abd4cd961b524c7b49cfdd`, clean. Python sources
  match the paired-seed harness frozen for `87686a`; the commits since
  `46f316d` are documentation.
- Package: `GianlucaMazza.XgpuE0_0.1.0.109_x64__g0p5dcfz4t9z4`.
- Backend source: `961ccc2ab2e800eb25ea1ea33c1af1a46389ee59`.
- [Preflight](preflight.json) was positive immediately before launch. A 26214400-byte
  throwaway upload succeeded and was deleted. Acceptance and benchmark are the
  published [0.1.0.109 proofs](../xbox-e0-20261009-109/notes.md).

Trial `e0-20261009T174028Z-94847b-000` is reserved as ternary, `row8log`, `d` 80,
4 layers, nominal `d_ff` 262, seed 0, lr 0.01, wd 0.1. It starts fresh. Run
`87686a-000` is not an input. The stored 2-bit width remains nominal `d_ff` 193.

## Supervision

Linger was already enabled. The campaign unit uses `background.slice`, `bg`,
`Restart=no`, `KillMode=mixed`, and an unlimited stop timeout. No status
observer is bound with `BindsTo` or `PartOf`. The unit environment is the
package name and the two thread caps. Failed units, including
`floppylm-e0-campaign-20261009T150327Z`, were left failed and were not restarted.

`87686a`, `766d4b`, `c58a86`, and every earlier campaign stay on their original
packages. No recovery of those campaigns is running.

## Later (2026-10-10)

Eight paired cells are eligible and indexed. Ternary seeds 0, 1 and 3 were
outside ±1% on the first pack and eligible after one S3 repair (`d_ff` 266,
266 and 268). Ternary seeds 2 and 4 were eligible at submitted `d_ff` 262.
2-bit seeds 0, 1 and 2 were eligible at submitted `d_ff` 205; the stored
nominal width remains 193. Run `94847b-008`, 2-bit seed 3, is in progress and
is not a result. 2-bit seed 4 has not started. The paired comparison, the
ten-hash freeze and the final test have not run. This is not a scalar recipe.

## Later (2026-10-10, cell 008)

Run `94847b-008`, 2-bit seed 3, is eligible at submitted `d_ff` 205. Val bpb
1.4925/1.3665/1.2801, Δ(2T→4T) = −0.086. The stored nominal width remains 193.
Nine paired cells are eligible. Run `94847b-009`, 2-bit seed 4, is in progress
and is not a result. The paired comparison, the ten-hash freeze and the final
test have not run. This is not a scalar recipe.

## Later (2026-10-10, cell 009)

Run `94847b-009`, 2-bit seed 4, is eligible at submitted `d_ff` 205. Val bpb
1.5142/1.3858/1.2927, Δ(2T→4T) = −0.093. The stored nominal width remains 193.
All ten paired cells are eligible. The ten counted hashes are frozen in
[`e0-20261009T174028Z-94847b.json`](../e0-v2/selections/e0-20261009T174028Z-94847b.json).
Byte parity and rank stability passed. The final test is in progress. This is
not a scalar recipe.

## Later (2026-10-10, completed)

The campaign completed at 2026-10-10T10:02:53Z. The unit exited 0. The final
test records ternary minus 2-bit −0.023838 bpb, sample SD 0.013733, frozen
gate 0.026322. That difference is inside the gate. The
[report](../e0-v2/campaigns/e0-20261009T174028Z-94847b/notes.md) marks the
baseline complete and keeps both stored arms.
