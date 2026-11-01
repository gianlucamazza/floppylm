# Last VQ recipe canaries, 2026-11-01

The two recipes preregistered in [ADR 0025](../../adr/0025-e1-vq-recipe-stop.md). Diagnostic CPU runs.
Not pilot cells, not the 1/16 signal, not the F1 verdict. Validation and test were not opened. Raw
rows are in [results.json](results.json).

## Method

ADR 0025 merged before the runs started. Both ran to the end on seed 0, as `systemd-run` units at
nice 10 with 4 threads each, at the same time. They started from signed commit `447e820`, whose
content is `656c5be` after a rebase that touched no code. Common recipe: `vq-0.5-learned`, ramp to
step 2400, lr 0.001, 3247 steps, cooldown 324, 256 KiB train holdout, `d` 256, one layer.

## Results

| Recipe | G | Cadence | `d_ff` | bpb at T | File at T (bytes) | Inside ±1% | Passes |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| Earlier decisive run | 8 | 64 | 801 | 2.526 | not recorded | unknown | no |
| A | 16 | 64 | 585 | 2.416 | 86089 | yes | no |
| B | 8 | 8 | 801 | 1.665 | 87514 | no, +1.83% | no |

The threshold is at most 1.40 bpb at T, and the window is 85078.1 to 86796.9 bytes. Scoring the
unpacked file gave the same bpb as the model at T for both recipes. These runs bring the canary
count to ten.

## Outcome

Neither recipe passes. Recipe B fails twice, on the threshold and on the window. ADR 0025 decision 8
closes the vector line at 1/16 as not reached with these recipes. F1 and F1-abl stay undecided.

## What the data suggest

This section is an observation, and it decides nothing.

- Cadence is the largest effect measured so far. Changing only the assignment interval from 64 to 8
  moves the score from 2.526 to 1.665.
- G=16 moves it by 0.11 on the same cadence, with a different `d_ff`.
- Recipe B's file grew past the window as training ran. Its `d_ff` would need repair, and a smaller
  `d_ff` could cost some of the gain.
- A shorter cadence has not been tried. Whether it continues the trend is unknown.

## External review

An independent read-only review by Grok (`grok-4.7`), before the results, agreed that the
constant-share recipe explains the 7 bpb failure and that the holdout comparison is sound. It called
recipe B the weaker probe and expected closure. The closure happened, but recipe B outperformed
recipe A by 0.75 bpb, which refutes the first of those judgments. It also noted that no term pulls
master weights toward their codes. The loss is cross-entropy only. No run tested this.

## What this does not show

- It does not reject the thesis. One seed, and F1 needs equal tokens at 1/16 and 1/4.
- Holdout is train bytes and scalar figures are validation bytes, so the gap is indicative.
- No run saved its final model, so code usage was not measured, and collapse and capacity are not
  separated.
- The threshold is an owner judgment, not derived from the protocol.
