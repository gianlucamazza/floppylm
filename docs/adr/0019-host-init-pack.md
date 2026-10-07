# ADR 0019: Adjust d_ff from the init pack before the first training attempt

## Status

`accepted` — accepted 2026-10-04. Amends decision 3 of [ADR 0008](0008-e0-numeric-protocol.md).
Does not change T, TinyGPT, `fill_min`, or a campaign already frozen.

## Context

The shape solver fills nominal bits. Eligibility is serialized bytes within ±1% of the
target. On the neutral shapes used by campaign `c58a86`, every original cell missed that
band and paid a second GPU attempt. The init pack of those shapes predicts the shortfall:
row16 `d_ff` 391 packs to 85,054 B (fill 0.9897) and row8log `d_ff` 415 packs to 85,015 B
(fill 0.9893), against 85,937.5 B.

`fill_d_ff` with that init coded/nominal ratio submits `d_ff` 398 and 422. The trained S3
repairs were 400 and 424, because a trained 4T pack is slightly more compact than the init
pack. The init packs of 398 and 422 are themselves inside ±1% (85,897 B and 85,835 B). A
fixed ratio of 0.987 is not used: it was measured only for ternary row16.

## Decision

1. Before the first GPU or CPU job of a scientific trial, initialize the solver shape and
   pack it. Record `init_model_bytes`, `init_fill`, `host_ratio` and `submitted_d_ff`.
2. If that pack is outside ±1% of the target, call `fill_d_ff` once with
   `ratio = packed_bytes × 8 / nominal_bits`. Submit that shape when it is different and
   inside the declared `d_ff` range. Otherwise submit the solver shape.
3. The submitted shape is the original attempt. `retry_count` stays 0. Decision 3 of ADR
   0008 still allows one S3 repair if the trained artifact misses parity.
4. Smoke runs, retries and resumes do not adjust. `fill_min` stays 0.995.

## Consequences

A future campaign pays the init pack on the host instead of a second full training attempt
when the prediction holds. If training moves the bytes back outside ±1%, S3 still runs, and
both attempts stay in the record. `c58a86` does not use this rule.

## Alternatives

Leaving S3 as the only adjustment stays available for a frozen campaign and is what
`c58a86` did. A format-wide prior ratio would skip the pack and would be wrong for shapes
whose coded/nominal ratio has not been measured.
