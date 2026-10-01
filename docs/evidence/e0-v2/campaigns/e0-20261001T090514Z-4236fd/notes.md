# e0-20261001T090514Z-4236fd

Status: **stopped**.

Trials: 2; byte repairs: 2.
Costs, exclusions, recipes and hashes are in summary.json.
This campaign establishes a scalar E0 baseline. Vector cores are outside E0.

Later note (2026-10-01): stopped by the owner at 13:44 CEST with SIGTERM to trial
`e0-20261001T090514Z-4236fd-001-repair` (console checkpoint at trunk step 162). Both row16 seeds
had completed and were not saturated (Δ 2T→4T −0.0818 / −0.0791 after repair, and −0.0848), so
`neutral()` could no longer select row16 and the preregistered gate was not expected to pass with
row8log on the same shape. Analysis and options:
[saturation proposal](../../../../adr/proposals/e0-saturation-proposal.md).
