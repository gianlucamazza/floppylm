# ADR 0026: One depth canary for the closed E1 1/16 vector line

## Status

`accepted` — 2026-11-02. Amends decision 5 of [ADR 0025](0025-e1-vq-recipe-stop.md), and only to allow
this canary. Does not amend [ADR 0023](0023-e1-1-16-pilot.md) or
[ADR 0024](0024-e1-vector-shape.md). Does not open a campaign or dispatch a console job.

## Context

ADR 0025 allowed two more recipes and no others. [Neither passed](../evidence/e1-vq-last-canaries-20261101/notes.md),
and the vector line closed. Assignment every 8 steps moved the score from 2.526 to 1.665, on the same
one-layer shape as every other learned rate-0.5 canary.

That depth was not chosen for the model. ADR 0024 decision 3 keeps the closest file. The learned
rate-0.5 book closed at d256, one layer, while the fixed rate-0.5 book, 240 bytes smaller, closed at
d80, twelve layers. No canary separates shape from recipe. The paused d80 cell records 1.14 bpb with
its cores unquantized, on validation at step 5845 and on a fixed book, so it is a hint and not a bound.

This canary is chosen after seeing ten canaries, which is the search ADR 0025 meant to prevent. It is
reported as the eleventh. The owner accepts that cost because the current stop has no measurement
behind it, while closed cells would give F1 a result even if the vector arms lose.

## Decision

1. **One run, to the end.** `vq-0.5-learned`, shared G=8, rate 0.5, seed 0, **d80, twelve layers,
   `d_ff` 245**, assignment every 8 steps, ramp to full quantization by step 2400, lr 0.001, 3247
   steps, cooldown 324, 256 KiB train holdout, `train.bin` only. `d_ff` 245 is the ADR 0024 decision 3
   value at this width and depth, with an init pack of 85909 bytes.
2. **Bar.** The run passes at no more than 1.40 bpb at T on the holdout, with its file within ±1% of
   85937.5 bytes. This is a filter for spending days of CPU. It is not the winning bar: ADR 0023 needs the
   best vector mean below the best scalar mean by `max(0.02, 2σ)`, at T and at 2T, so at best about
   1.275 at T.
3. **Repair.** If the score passes and the file does not, one repeat runs at
   `d_ff = 245 + round((85937.5 - bytes) / 180)`, 180 bytes being the nominal cost of one `d_ff` unit at
   this shape. It must pass both parts of the bar.
4. **Outcome.** If it passes, a new proposal names the recipe and shape, and no vector cell starts until
   it is accepted. If it does not, the ADR 0025 closure is final, and no further 1/16 recipe is
   proposed under this line. F1 stays undecided until eighteen cells close.
5. **Operational failure.** If the run fails twice for an operational reason, the closure stands and
   the failure is not a scientific result.

## Consequences

The run changes only the shape against recipe B, but width and depth change together, so a difference
is attributed to the shape and not to depth alone. One seed cannot reject the thesis. Holdout bytes
come from `train.bin` and scalar figures from validation, so the comparison is indicative.

## Alternatives

Assignment every step was rejected for now: the roadmap excludes it on cost, and it leaves the shape
question open. An unquantized ceiling at one layer was rejected: it bounds one shape and says nothing
about the recipe at twelve layers. Stopping now remains the owner's alternative, and it would leave
the stop without a measurement.
