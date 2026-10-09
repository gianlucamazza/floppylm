# ADR 0020: Compare candidates that share the ±1% target window

## Status

`accepted` — 2026-10-07. Amends the reciprocal clause of [ADR 0005](0005-e0v2-protocol.md) §1
and the reciprocal wording of [ADR 0015](0015-e0-fixed-data-frontier.md) decision 1.
Records [the reciprocal-band proposal](proposals/e0-reciprocal-parity-band.md).
[ADR 0021](0021-paired-seed-successor.md) follows this rule for a new campaign that
starts at the paired seeds. Decision 3 still forbids copying 2-bit from `c58a86`.

## Context

ADR 0005 §1 required two checks on serialized bytes: every candidate within ±1% of
the target, and `max/min − 1 ≤ 0.01`. The target window runs from 0.99× to 1.01×
the target. `1.01/0.99 − 1` is 2.0202%. Two cells can each pass the target check
and still fail the reciprocal check.

Campaign `e0-20261004T103838Z-c58a86` finished its ternary grid under that rule and
stopped. All thirteen shapes are inside ±1% of 85937.5 bytes. On the 4T branch the
sizes run from 85098 to 85982 bytes, and `max/min − 1` is 1.0388%. Selection refused
the set. That spread is the occasion for this rule. It is not a result to rewrite,
and the diagnostic minimum of that set is not a shape decision.

A one-element parity call makes the old reciprocal check vacuously true, so a trial
can be marked eligible while the set still fails. This ADR keeps the per-candidate
target check and withdraws the extra spread check.

## Decision

1. Candidates that share one target are comparable when each serialized size is
   within ±1% of that target. The clause `max/min − 1 ≤ 0.01` is withdrawn.
2. Campaign `e0-20261004T103838Z-c58a86` is not migrated. Its saved comparison stays
   `byte_comparable: false`. The diagnostic minimum (`d` 80, 4 layers, `d_ff` 262)
   is not a decision. The campaign is not resumed.
3. A successor may open at `grid-ternary` by copying three closed facts from that
   campaign: scale `row8log`, MLP SwiGLU at nominal `d_ff` 274, and ternary tuning
   `lr` 0.01, `delta` 0.5, `wd` 0.1. It trains a new ternary grid under
   [ADR 0019](0019-host-init-pack.md) and this rule. 2-bit tuning and the 2-bit
   grid are not copied.
4. New campaigns freeze `protocol_adr` `0020`. Opening a campaign whose frozen
   protocol differs is an error. Campaigns frozen at `0015` are not opened.

## Consequences

One-element eligibility checks are unchanged in effect. `select_winner`, paired
comparison and scientific freeze use the shared-target rule. The successor does
not repeat the closed scale, MLP or ternary-tuning measurements. ADR 0019 may
still change the first submitted `d_ff` of a new cell. S3 remains the single
post-training repair.

## Alternatives

Keeping the reciprocal check leaves a successor able to stop on two cells that
both meet the declared target. Rerunning neutral scale under the old rule repeats
closed measurements. Naming the diagnostic minimum would turn a refused set into
a decision after the scores.
