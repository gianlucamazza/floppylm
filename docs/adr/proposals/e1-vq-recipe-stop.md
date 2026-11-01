# Stop the E1 1/16 vector cells (proposal)

## Status

`proposed` — 2026-11-01. Not accepted. It does not amend
[ADR 0023](../0023-e1-1-16-pilot.md) until the owner accepts it.

## Context

Vector cell `vq-0.5-fixed-s0` is paused with validation bpb 7.05 at 2T. Scalar cells are near 1.23.
The [canaries](../../evidence/e1-vq-canary-20261101/notes.md) show why: ADR 0023 decision 7 trains
with 10% of groups quantized, and the artifact quantizes all of them. A ramp to full quantization
closes that gap, so the training loss matches the artifact. It does not close the gap to the scalar
arms. The best learned book reaches 2.526 at T against 1.295, above the 1.60 threshold written
before that run. Fixed books got worse at full quantization, with a lower learning rate as well.

The remaining cells would take days of CPU. Under the current recipe they would produce an F1
signal that measures a known recipe defect. The completion plan says that unsaturated training and
operational failure do not prove the vector hypothesis false.

## Decision

1. `vq-0.5-fixed-s0` is not resumed. The other eleven vector cells do not start under ADR 0023
   decision 7.
2. No 1/16 signal is published. It needs eighteen closed cells. F1 and F1-abl stay undecided, and
   this record is not a verdict on the thesis.
3. The six closed scalar cells stay valid and frozen as measured.
4. B0 through E2i do not start.
5. The vector cells reopen only through a new ADR. It names one recipe, and a train-holdout canary
   for that recipe reaches at most 1.40 bpb at T on seed 0, before any new vector cell starts.

## Alternatives

- **Resume as specified.** Rejected: days of CPU for a result already explained by the recipe.
- **Adopt the ramp and run the pilot.** Rejected: its best arm misses the threshold.
- **Publish F1 now.** Rejected: the protocol needs closed cells at 1/16 and the same sign at 1/4.
- **Keep searching recipes.** Left to the owner. It is the only route that reopens the cells, and
  each attempt is a further look at the same question, so its count must be reported.
