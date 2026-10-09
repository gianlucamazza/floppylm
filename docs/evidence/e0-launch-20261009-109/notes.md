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
