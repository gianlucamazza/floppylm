# VQ depth canary, 2026-11-02

The one run preregistered in [ADR 0026](../../adr/0026-e1-vq-depth-diagnostic.md), reported as the
eleventh canary. Diagnostic CPU run. Not a pilot cell, not the 1/16 signal, not the F1 verdict.
Validation and test were not opened. Raw rows are in [results.json](results.json).

## Method

ADR 0026 merged as `1d5ca35` before the run started. The run used signed commit `8fc9713`, with no
content difference from that merge. It ran to the end on seed 0, as a `systemd-run` unit at nice 10
with 4 threads, in 7288 seconds, while an unrelated `llama-server` was using the same machine. The
JSON confirms the preregistered recipe: `vq-0.5-learned`, G=8, `d` 80, 12 layers, `d_ff` 245,
assignment every 8 steps, ramp to step 2400, lr 0.001, 3247 steps, cooldown 324, 256 KiB train
holdout.

## Results

| Recipe | Shape | Cadence | bpb at T | File at T (bytes) | Inside ±1% | Passes |
| --- | --- | ---: | ---: | ---: | --- | --- |
| B, [previous canary](../e1-vq-last-canaries-20261101/notes.md) | `d` 256, 1 layer, `d_ff` 801 | 8 | 1.665 | 87514 | no, +1.83% | no |
| C, this run | `d` 80, 12 layers, `d_ff` 245 | 8 | 1.741 | 88312 | no, +2.76% | no |

The threshold is at most 1.40 bpb at T, and the window is 85078.1 to 86796.9 bytes. Scoring the
unpacked file gave the same bpb as the model at T.

| Step | Quantized share | Holdout bpb |
| ---: | ---: | ---: |
| 400 | 0.25 | 4.695 |
| 800 | 0.40 | 4.371 |
| 1200 | 0.55 | 3.027 |
| 1600 | 0.70 | 2.537 |
| 2000 | 0.85 | 2.220 |
| 2400 | 1.00 | 2.232 |
| 2800 | 1.00 | 2.048 |
| 3200 | 1.00 | 1.789 |
| 3247 | 1.00 | 1.741 |

## Outcome

The run fails on the threshold and on the window. Under ADR 0026 decision 3 a score above 1.40 gets no
repeat, so no second run took place. Under decision 4 the ADR 0025 closure is final, and no further
1/16 recipe is proposed under this line. F1 and F1-abl stay undecided, because the eighteen cells have
not closed.

## What the data suggest

This section is an observation, and it decides nothing.

- Twelve layers at `d` 80 did not beat one layer at `d` 256 on the same recipe. This one-seed comparison
  gives no support to shape as the dominant limit, but width and depth changed together.
- The score was still falling at T: 0.31 bpb over the last 447 steps, part of them in cooldown. A longer
  run might score lower. The bar is fixed at T, and the run says nothing about 2T or 4T.
- The file grew 2403 bytes from its init pack of 85909. Reaching the window would have needed a smaller
  `d_ff`, about 232 by the ADR formula. That repair was not run, so its effect on the score is unknown.

## What this does not show

- It does not reject the thesis. One seed, and F1 needs equal tokens at 1/16 and 1/4.
- Holdout is train bytes and scalar figures are validation bytes, so the gap is indicative.
- The final model was not saved, so code usage was not measured.
- This canary was chosen after seeing ten canaries. The threshold is an owner judgment, not derived
  from the protocol.
