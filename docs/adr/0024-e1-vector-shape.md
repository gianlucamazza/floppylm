# ADR 0024: Vector shape for the 1/16 pilot

## Status

`accepted` — 2026-10-11. Names the vector width, depth, `d_ff`,
learning rate and weight decay left open by
[ADR 0023](0023-e1-1-16-pilot.md). The measured table fills one book at a
time. Does not amend that protocol, does not open a campaign, does not
reserve a final test, and does not dispatch a console job.

## Context

ADR 0023 names the four shared G=8 books, the seeds, the 85937.5 byte target,
and F1. A `vq` core copied from either stored scalar shape packs far below
that target. Moving only `d_ff` inside the copied depth and width cannot
enter the ±1% window. Training those copies would spend the seeds on arms
that fail parity before the first step.

## Decision

1. **Family.** Each vector arm is SwiGLU, `row8log`, a 4-bit embedding,
   `n_heads = d / 16`, vocab 256, context 256, `delta` 0.5 in the header, and
   `qk_norm` false. G, rate, and book length stay the four ADR 0023 books.
2. **Box.** `d` runs from 64 to 256 in steps of 16. Depth runs from 1 to 16.
   `d_ff` is an integer in the E0 SwiGLU interval, from `ceil(4d/3)` through
   `4d`.
3. **One shape per book.** At seed 0, pack the init FLP2 file. Keep `d_ff`
   values whose file is within ±1% of 85937.5 bytes. Among the whole box, take
   the closest file. Ties break to fewer stored parameters, then smaller `d`,
   then fewer layers, then smaller `d_ff`. No validation loss enters.
4. **Search.** For each `(d, depth)`, compare the pack at the ends of the
   `d_ff` interval. When the high end is at least as large as the low end,
   binary-search the crossing of the target and score only the admissible
   integers next to that crossing. A local decrease scores every `d_ff` in
   the interval. The same order as decision 3 selects across the box.
5. **Optimizer.** Copy the stored 2-bit arm: learning rate 0.003, weight
   decay 0.1. There is no S4 sweep. The vector scales are that `row8log` codec.
6. **Seeds.** The `(d, depth)` pair is shared by seeds 0, 1 and 2. Each seed
   may then move only `d_ff`, by the same closest-file rule inside the same
   interval. That move is the ADR 0019 init-pack. One S3 repair after training
   may move `d_ff` again. Neither move changes G, rate, or book length.
7. **Tokens.** T is 20 times the largest seed-0 stored-parameter count among
   the two submitted scalar arms and the four vector shapes. Seeds 1 and 2
   use that same T.
8. **Stop.** If any book has no admissible init pack in the box, the pilot
   does not start.

## Consequences

The host solver is `solve_vector_shapes` in `src/floppylm/e1_plan.py`. It does
not train. A hand-specified vector width, depth, `d_ff`, learning rate, or
weight decay is not a shape. G=16 stays out of this rule.

The seed-0 table below records each book as the solver closes it. A closed
row is locked by re-packing that file. An open row is not a shape, and T stays
unnamed until every row is closed. The pilot has not started. No console job
is authorized.

## Measured seed-0 shapes

Measured on 2026-10-11 by `solve_vector_shapes`. Seeds 1 and 2 are not packed.
The pilot has not started. No console job is authorized.

| Book | State | d | layers | d_ff | init bytes | stored params |
| --- | --- | --- | --- | --- | --- | --- |
| rate 0.5, fixed | closed | 80 | 12 | 247 | 85934 | 1039040 |
| rate 0.5, learned | closed | 256 | 1 | 801 | 85935 | 942976 |
| rate 0.75, fixed | closed | 80 | 8 | 258 | 85938 | 720640 |
| rate 0.75, learned | open |  |  |  |  |  |

The fixed rate-0.5 file is 3.5 bytes from 85937.5. Re-packing `d_ff` 246 and
248 at the same width and depth yields 85785 and 86031 bytes. Both are farther
from the target. The learned rate-0.5 file is 2.5 bytes from 85937.5.
Re-packing `d_ff` 800 and 802 at the same width and depth yields 85809 and
85972 bytes. Both are farther from the target. The fixed rate-0.75 file is
0.5 bytes from 85937.5. Re-packing `d_ff` 257 and 259 at the same width and
depth yields 85803 and 86070 bytes. Both are farther from the target. Each
closed arm copies learning rate 0.003 and weight decay 0.1.

## Alternatives

Copying a scalar shape and accepting an ineligible vector arm was rejected:
ADR 0019 exists so a known init-pack miss is not trained. Choosing the shape
by validation loss was rejected: that would be a second comparison. A learning-rate
sweep was rejected: S4 already closed the scalar adversaries, and this pilot
copies one of those optimizers rather than opening a new search.
