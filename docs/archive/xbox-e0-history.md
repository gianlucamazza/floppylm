# Xbox E0 validation history

> **Archive.** Dated index of earlier packages and campaigns. Measured numbers are owned by the
> linked evidence; procedure by the [runbook](../operations/xbox-e0.md); live state by
> [STATUS](../STATUS.md).

| Date       | Package / CI run                     | Outcome                                                                                                   | Evidence                                                                                                                                      |
| ---------- | ------------------------------------ | --------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| 2026-09-30 | CI 36743191762 (`da4b391`)           | First device initialization selected WARP; acceptance correctly stopped                                   | local `runs/xbox-acceptance-20260930-ci36743191762`                                                                                           |
| 2026-09-30 | 0.1.0.7, CI 36744081513 (`a3d70e8`) | Adapter diagnostics, debug layer disabled; retest on hardware GPU: 36/36 fixtures passed, optimizer gate missing, acceptance not ok | local `runs/xbox-acceptance-20260930-ci36744081513`                                                                                           |
| 2026-09-30 | 0.1.0.8, CI 36745050129 (`01ab771`) | 36 fixtures, optimizer oracle, exact resume passed; representative trial failed atomic JSON replacement   | local `runs/xbox-acceptance-20260930-ci36745050129`                                                                                           |
| 2026-09-30 | 0.1.0.11, CI 36746732705 (`9744ff7`) | 36/36 fixtures, AdamW, resume passed; first throughput; tensor16 vs S9 incompatibility found              | [xbox-e0-20260930](../evidence/xbox-e0-20260930/notes.md)                                                                                     |
| 2026-09-30 | 0.1.0.19, CI 36751689355 (`6dbc407`) | Active-kernel cleanup; 52 operation cases after fixing Weighted gradients and shifted-logit cross-entropy | [xbox-e0-20260930-kernels](../evidence/xbox-e0-20260930-kernels/notes.md)                                                                     |
| 2026-10-01 | 0.1.0.22, CI 36791806399 (`baba2e0`) | Acceptance passed (52 cases, 36 fixtures); status publication then failed at step 704 (Win32 error 5) | [xbox-e0-20261001](../evidence/xbox-e0-20261001/notes.md) (`baseline-publish-failure.json`)                                                   |
| 2026-10-01 | 0.1.0.24, CI 36792707081 (`6a12402`) | Full acceptance, real suspension and recovery; campaign `503df0` launched, then stopped at trunk step 455 | [xbox-e0-20261001](../evidence/xbox-e0-20261001/notes.md), [campaign record](../evidence/e0-v2/campaigns/e0-20261001T074326Z-503df0/notes.md) |
| 2026-10-01 | 0.1.0.28, CI 36839565773 (`25f8bc3`) | E0.1, GPU-resident tensors, bit-identical to 0.1.0.24, ~10× throughput; campaign `4236fd` launched        | [xbox-e0-20261001-e01](../evidence/xbox-e0-20261001-e01/notes.md)                                                                             |

The `503df0` campaign was stopped by SIGTERM to its trial: it had spent 329 GPU seconds of 3848
wall seconds because every operation uploaded inputs and waited for its result. Package 0.1.0.28
(xbox-gpu-training PR #18) keeps tensors GPU-resident with the same shader and accumulation order.
The tensor16/S9 issue was resolved by [the zero-row proposal](../adr/proposals/e0-zero-row-proposal.md)
and [ADR 0011](../adr/0011-e0-row-scale-selection.md).
