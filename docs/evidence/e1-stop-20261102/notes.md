# Where the research stopped, 2026-11-02

The measured frontier at the stop recorded in the
[completion plan](../../completion-plan.md#stop-without-a-verdict-2026-11-02). This page collects
numbers that other evidence owns. It runs nothing new, and it is not the 1/16 signal or the F1 verdict.

## Measured

| Item | Result | Evidence |
| --- | --- | --- |
| E0 scalar baseline, Xbox, 1/16 | Complete. Ten paired cells, one final test: ternary minus 2-bit −0.0238 bpb, inside the 0.0263 gate | [review](../e0-review-20261010-94847b/notes.md) |
| Pilot ternary, CPU, 1/16, eligible seeds 0 and 2 | 1.2949 / 1.2343 / 1.1826 validation bpb at T / 2T / 4T | [cells](../e1-1-16/) |
| Pilot 2-bit, CPU, 1/16, seeds 0, 1, 2 | 1.2967 / 1.2310 / 1.1825 validation bpb at T / 2T / 4T | [cells](../e1-1-16/) |
| Pilot `vq-0.5-fixed-s0`, not closed | 7.2335 / 7.0506 validation bpb at T / 2T, on the ADR 0023 recipe | [canaries](../e1-vq-canary-20261101/notes.md) |

## Vector canaries at T

Seed 0, train holdout, 3247 steps. Not comparable to the pilot cells without the caveats below.

| Recipe | Shape | Cadence | bpb at T | File | Evidence |
| --- | --- | ---: | ---: | --- | --- |
| Ramp, learned rate 0.5 | `d` 256, 1 layer | 64 | 2.526 | not recorded | [canaries](../e1-vq-canary-20261101/notes.md) |
| Recipe A, G=16 | `d` 256, 1 layer | 64 | 2.416 | inside ±1% | [last canaries](../e1-vq-last-canaries-20261101/notes.md) |
| Recipe B, G=8 | `d` 256, 1 layer | 8 | 1.665 | +1.83% | [last canaries](../e1-vq-last-canaries-20261101/notes.md) |
| Recipe C, G=8 | `d` 80, 12 layers | 8 | 1.741 | +2.76% | [depth canary](../e1-vq-depth-diagnostic-20261102/notes.md) |

The best file inside the window scores 2.416. A vector arm needs about 1.275 at T to separate from
the scalar arms. All eleven canaries stayed above the 1.40 filter.

## Not measured

- A closed vector cell, a 1/16 signal, F1, or F1-abl. No vector run reached 2T or 4T with a working
  recipe.
- The 1/4 and 1× budgets, recursion, coding (E2), the runtime (E3), and the image and human reviews
  (E4). No floppy image exists.
- Assignment every step, a term that pulls master weights toward their codes, and code usage.
- The 1/16 test split. It stays unopened, because no cell set was frozen.

## How to read this

The result is not a falsification. Eleven canaries on one seed show that these recipes did not close
the gap at T. They do not show that a sub-bit vector core cannot beat a scalar core at equal bytes.
Holdout bytes come from `train.bin` and scalar figures from validation, so the gap is indicative.
