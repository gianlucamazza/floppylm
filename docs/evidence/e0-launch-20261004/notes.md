# E0 campaign launch on package 0.1.0.102

The owner asked to install 0.1.0.102 and resume E0 work. This record is the new
campaign. It is not a migration of `a8d8b9` and it is not a completed result.

## Frozen identity

- Campaign: `e0-20261004T082243Z-31972d`, created 2026-10-04T08:22:43Z.
- Directory: `runs/e0-campaign-20261004-102`.
- Unit: `floppylm-e0-campaign-20261004T082242Z.service`, active at launch.
- Host source: `4de17b342137af8830daede3e6d830d436809be8`, clean. Python sources
  match the recovery-harness squash `555a865` plus later docs commits.
- Package: `GianlucaMazza.XgpuE0_0.1.0.102_x64__g0p5dcfz4t9z4`.
- Backend source: `4b8f51c3a5ee985ce8fcb71327f0ffc88e487545`.
- [Preflight](preflight.json) was positive immediately before launch: full train
  and validation hashes, idle worker, no pending inbox jobs.
- Acceptance and benchmark are the published
  [0.1.0.102 proofs](../xbox-e0-20261004-102/notes.md).

Trial `e0-20261004T082243Z-31972d-000` is reserved as ternary, row16, `d` 96,
3 layers, `d_ff` 391, seed 0. It starts at trunk step 0. By 2026-10-04T08:23:55Z
the same job was running at trunk step 64. Checkpoint 2944 from `a8d8b9` is not
an input.

## Supervision

Linger was already enabled. The existing tunnel unit
`floppylm-e0-tunnel-20261003T104300Z.service` stayed up. The campaign unit uses
`background.slice`, `bg`, `Restart=no`, `KillMode=mixed`, and an unlimited stop
timeout. No status observer is bound with `BindsTo` or `PartOf`. The failed
`a8d8b9` unit was left failed and was not restarted.

`fdab67`, `40a67c`, `2fe64f`, `ca781f`, and `a8d8b9` stay on their original
packages.

## Later (2026-10-04)

The original unit `floppylm-e0-campaign-20261004T082242Z.service` stopped at
2026-10-04T08:46:30Z. Trial `31972d-000` was interrupted at trunk 896
(`progress_stall`, requested fence 0, 600837 ms) after the T branch. The
checkpoint was published. The runner returned 130 and the campaign parent
recorded a stop.

Explicit recovery unit `floppylm-e0-campaign-20261004T085921Z.service` resumed
the same run, package, and host freeze. By 2026-10-04T09:04:14Z the resumed job
was running at trunk 1216. The stall cause remains unproven.

That recovery unit stopped at 2026-10-04T09:28:41Z. The published result is
interrupted at trunk 2112 after the T branch (end step 879) and the 2T branch
(end step 1758). The watchdog recorded `progress_stall`, requested fence 0,
completed fence 46560, 600839 ms. The device checkpoint is sha256
`3fb5d57cb03591afcbf90054c97544f6abcb6e075c1a297139335d6ae0c86483`, 23713680
bytes. The host copy under `xbox/recovery-checkpoint.json` is still the
trunk-896 checkpoint. The failed worker stayed listed. This second stop has
no recovery running.

## Later (2026-10-04, package 0.1.0.105)

Package `0.1.0.105` replaced `0.1.0.102` in place after the step-2112 checkpoint
was copied to the host and hashed. Qualification of `0.1.0.105` passed. This
campaign was not resumed onto that package. The preserved checkpoint remains
sha256 `3fb5d57cb03591afcbf90054c97544f6abcb6e075c1a297139335d6ae0c86483`,
23713680 bytes. No recovery of `31972d` is running.
