# ADR 0025: Stop the E1 1/16 vector cells and bound the recipe search

## Status

`accepted` — 2026-11-01. Amends [ADR 0023](0023-e1-1-16-pilot.md): decisions 3 and 7 for canaries
only, and the plan to run the twelve vector cells. Records
[the stop proposal](proposals/e1-vq-recipe-stop.md). Does not amend
[ADR 0024](0024-e1-vector-shape.md). Does not open a campaign or dispatch a console job.

## Context

Vector cell `vq-0.5-fixed-s0` is paused with validation bpb 7.05 at 2T. Scalar cells are near 1.23.
The [canaries](../evidence/e1-vq-canary-20261101/notes.md) show why: ADR 0023 decision 7 trains with
10% of groups quantized, and the artifact quantizes all of them. A ramp to full quantization closes
that gap but not the gap to the scalar arms. The best learned book reaches 2.526 at T against 1.295,
above the 1.60 [threshold written before that run](../evidence/e1-vq-canary-20261101/thresholds.txt).

Eight canaries have run, all on seed 0. The recipe question was asked after seeing validation on the
paused cell. ADR 0023 calls choosing G after validation a second comparison, so every further recipe
is counted and reported as one.

## Decision

1. **Stop.** `vq-0.5-fixed-s0` is not resumed. The other eleven vector cells do not start under ADR
   0023 decision 7.
2. **No verdict.** No 1/16 signal is published. It needs eighteen closed cells. F1 and F1-abl stay
   undecided, and this record is not a verdict on the thesis.
3. **Scalars.** The six closed scalar cells stay valid and frozen as measured.
4. **Ladder.** B0 through E2i do not start.
5. **Two more recipes, no others.** Both run to the end, whatever the first one shows. They bring the
   canary count to ten. Common to both: `vq-0.5-learned`, seed 0, ramp to full quantization by step
   2400, lr 0.001, 3247 steps, cooldown 324, 256 KiB train holdout, `train.bin` only, `d` 256, one
   layer.
   - **Recipe A:** shared G=16 at rate 0.5, alphabet 256, an ADR 0023 decision 3 row. `d_ff` is the
     value in the ADR 0024 interval whose init pack is closest to 85937.5 bytes, chosen before
     training. Without an admissible value, recipe A does not run and is not replaced.
   - **Recipe B:** shared G=8 at rate 0.5, assignment every 8 steps, published `d_ff` 801.
6. **Validity.** A recipe counts only if its packed file at T is within ±1% of 85937.5 bytes.
7. **Threshold.** A recipe passes at no more than 1.40 bpb at T on the holdout. There is no middle
   band and no extension to 2T.
8. **Outcome.** If a recipe passes, a new proposal names one recipe, and no vector cell starts until
   it is accepted. If none passes, the vector line at 1/16 closes as not reached with these recipes,
   through a roadmap paragraph and a STATUS update. F1 stays undecided in both cases.

## Consequences

The threshold is an owner judgment and is not derived from the protocol. Holdout bytes come from
`train.bin` and scalar figures from validation, so the comparison is indicative. One seed cannot
reject the thesis. Recipes A and B are opt-in and leave the pilot driver unchanged.

## Alternatives

Resuming as specified was rejected: days of CPU for a result already explained by the recipe.
Adopting the ramp and running the pilot was rejected: its best arm misses the threshold. Publishing
F1 now was rejected: the protocol needs closed cells at 1/16 and the same sign at 1/4. An open recipe
search was rejected because each attempt is a further look at the same question.

## Later (2026-11-01, outcome)

[Neither recipe passed](../evidence/e1-vq-last-canaries-20261101/notes.md), so decision 8 closes the
vector line at 1/16. This note does not change the decision. No console job is authorized.
