# E0 campaign launch on package 0.1.0.105

The owner approved a new E0 campaign after `0.1.0.105` was qualified. This record
is that campaign. It is not a migration of `31972d` or `a8d8b9`, and it is not a
completed result.

## Frozen identity

- Campaign: `e0-20261004T103838Z-c58a86`, created 2026-10-04T10:38:38Z.
- Directory: `runs/e0-campaign-20261004-105`.
- Unit: `floppylm-e0-campaign-20261004T103837Z.service`, active at launch.
- Host source: `f76b4c8b67e9858a467cc3e0d77190bd6271e558`, clean. That commit
  includes the resume exit 130 change (`bd56e92`) and the `0.1.0.105` evidence.
- Package: `GianlucaMazza.XgpuE0_0.1.0.105_x64__g0p5dcfz4t9z4`.
- Backend source: `128434e81837ec1558f7e3d68a7f8849a91aa054`.
- [Preflight](preflight.json) was positive immediately before launch: full train
  and validation hashes, idle worker, no pending inbox jobs.
- Acceptance and benchmark are the published
  [0.1.0.105 proofs](../xbox-e0-20261004-105/notes.md).

Trial `e0-20261004T103838Z-c58a86-000` is reserved as ternary, row16, `d` 96,
3 layers, `d_ff` 391, seed 0. It starts at trunk step 0. The step-2112 checkpoint
from `31972d` is not an input.

## First checkpoints

The host progress log is `runs/e0-campaign-20261004-105/e0-20261004T103838Z-c58a86-000.log`.
Published status reached trunk 64 at 2026-10-04T10:39:47Z and trunk 128 at
2026-10-04T10:40:36Z. A later read of the same status was trunk 192, checkpoint
sha256 `1dc8957a4ad4f99597fd8f9a929003373ef81a3cd625ad75c7fea3cffb14c059`,
23833058 bytes. No `checkpoint.json.phase` file was present after those
publishes. This does not show that the 600 s stall is gone. That remains open
until the trial passes trunk 896 and 2112 and reaches 4T.

## Supervision

Linger was already enabled. The existing tunnel unit
`floppylm-e0-tunnel-20261003T104300Z.service` stayed up. The campaign unit uses
`background.slice`, `bg`, `Restart=no`, `KillMode=mixed`, and an unlimited stop
timeout. No status observer is bound with `BindsTo` or `PartOf`. The failed
`31972d` and `a8d8b9` units were left failed and were not restarted.

`fdab67`, `40a67c`, `2fe64f`, `ca781f`, `a8d8b9`, and `31972d` stay on their
original packages. No recovery of those campaigns is running.

## Later (2026-10-04, row16 pair)

Trial `c58a86-000` and its S3 repair both completed 4T, as did seed 1 and its
repair. Both repaired seeds are eligible. Seed 0 val bpb is 1.5155/1.3951/1.3160
and seed 1 is 1.5100/1.3916/1.3082, the same published `ca781f` pair. No
`progress_stall` occurred. Trial `002` (`row8log`, `d_ff` 415, seed 0) started
after that pair and is not a result.
