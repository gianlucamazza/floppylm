# VQ recipe canaries, 2026-11-01

Diagnostic CPU runs. Not pilot cells, not the 1/16 signal, not the F1 verdict. The test split was
not opened. All runs use seed 0. Raw rows are in [results.json](results.json).

## Why

Paused cell `vq-0.5-fixed-s0` records validation bpb 7.2335 at T and 7.0506 at 2T. Scalar cells
record about 1.30 and 1.23. A unigram code on the first 64 KiB of validation is 4.42.

## Quantization gap on the paused checkpoint

This one measurement read validation: the first 64 KiB, on the master weights of the paused trunk
at step 5845, with a varied share of core groups quantized. It is disclosed because the recipe
question below was asked after seeing it. Recon NMSE of the core matrices is about 0.78.

| Quantized share | 0 | 0.1 | 0.25 | 0.5 | 0.75 | 1.0 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| bpb | 1.1398 | 1.1901 | 1.393 | 2.9489 | 5.1424 | 7.1484 |

The artifact counts only share 1.0. ADR 0023 decision 7 trains at share 0.1.

## Method

[`scripts/e1_vq_canary.py`](../../../scripts/e1_vq_canary.py) trains a published seed-0 shape on
`train.bin` minus its last bytes, and scores the fully quantized model on those bytes. It reads no
validation or test. `QuantRamp` raises the share linearly from 0.1 to 1. It is opt-in and the pilot
driver does not set it. Runs were nice 10 background processes, not `systemd-run` units, and shared
the machine with other work, so their seconds are not a cost measurement.

## Results

Holdout bpb of the fully quantized model. These runs use a 64 KiB holdout and no cooldown.

| Arm | Share | lr | Steps | Best before share 1 | First at share 1 | Last |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| vq-0.5-fixed | constant 0.1 | 0.003 | 800 | 5.03 | never | 6.75 |
| vq-0.5-fixed | ramp to 600 | 0.003 | 800 | 3.47 | 3.71 | 4.11 |
| vq-0.5-learned | ramp to 600 | 0.003 | 800 | 2.69 | 3.39 | 3.52 |
| vq-0.75-fixed | ramp to 600 | 0.003 | 800 | 2.91 | 4.22 | 4.45 |
| vq-0.5-learned | ramp to 2400 | 0.001 | 2800 | 2.80 | 2.96 | 2.73 |
| vq-0.5-fixed | ramp to 2400 | 0.001 | 2800 | 3.39 | 3.66 | 3.93 |

## Decisive run

Thresholds were written before the run, against the best scalar eligible mean of 1.295 at T: at most
1.40 writes a recipe ADR; 1.40 to 1.60 extends to 2T; at least 1.60 raises closing the pilot.
Recipe: ramp to 2400, lr 0.001, 3247 steps, cooldown 324, 256 KiB holdout.

| Arm | Layers | d | Last before cooldown (step 2800) | At T (step 3247) |
| --- | ---: | ---: | ---: | ---: |
| vq-0.5-learned | 1 | 256 | 2.877 | **2.526** |
| vq-0.75-learned | 2 | 160 | 3.356 | 3.048 |

The best arm is 2.526, above 1.60 and 1.23 bpb from the best scalar. The rule raises closing the pilot.

## What this does not show

- It does not reject the thesis. One seed and one family of recipes were tried, F1 needs equal tokens
  at 1/16 and 1/4, and these runs stop at T.
- Holdout is train bytes and scalar figures are validation bytes, so the gap is indicative. Its size
  is much larger than that difference.
- Fixed and learned arms differ in depth, so their difference is not attributed to the book alone.
- Loss was still falling at T on both learned arms. No extrapolation to 2T or 4T is claimed.
- Other recipes were not tried: a shorter assignment cadence, other optimizers, G=16.
