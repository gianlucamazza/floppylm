# Reciprocal byte parity and the ±1% window

## Status

accepted — 2026-10-07; recorded in [ADR 0020](../0020-target-window-parity.md).

The decision section below is the same-day record that campaign `c58a86` is not
reopened and that its diagnostic minimum is not a shape. ADR 0020 applies the
shared-target window to a successor written before its first cell.

## Context

[ADR 0005](../0005-e0v2-protocol.md) §1 requires two checks on serialized bytes:
every candidate within ±1% of the target, and `max/min − 1 ≤ 0.01`. The target
window runs from 0.99× to 1.01× the target, about 2% wide. `1.01/0.99 − 1` is
2.02%. Two cells can each pass the target check and still fail the reciprocal
check.

Campaign `e0-20261004T103838Z-c58a86` finished the ternary grid and stopped at
2026-10-07T12:26:34Z in phase `grid-ternary`. All thirteen shapes are
individually inside ±1% of 85937.5 bytes. On the 4T branch the sizes run from
85098 bytes (`d` 80, 4 layers, `d_ff` 262, fill 0.9902) to 85982 bytes (`d` 96,
4 layers, `d_ff` 176, fill 1.0005). `max/min − 1` is 1.0388%. The 1% ceiling
above the small cell is `85098 × 1.01` = 85948.98 bytes. The large cell is 33
bytes above that ceiling. `comparisons.grid-ternary` is saved with
`byte_comparable: false` and thirteen scores. Selection refused the set.
`decisions` contains `neutral-mlp` and `neutral-scale` only. 2-bit did not start.

A cell is marked `eligible` from a one-element parity call, so `max/min − 1`
on that one cell is 0. Reciprocal parity is judged on the set. Thirteen
eligible cells can still stop the phase. That is the accepted rule.

The diagnostic minimum at T, 2T and 4T is the small cell, val bpb
1.4599/1.3375/1.2522. That rank is not a shape decision. One of the thirteen
scores repeats the already measured tuning repair (`014-repair`, recorded
again as `102-repair`) and remains a member of the refused set.

S3 is one repair, and it runs only when a cell falls outside ±1% of the target.
These thirteen cells are inside that window.

## Alternatives

### Loosen the reciprocal tolerance

Not adopted. The 1% reciprocal bound is ADR 0005 §1. Changing it after these
scores would rewrite the comparison this campaign already ran.

### Drop an extreme cell

Not adopted. Dropping the small cell or the large cell would be a rule chosen
after the scores. The small cell is also the diagnostic minimum.

### A second S3 repair

Not adopted. S3 is the single preregistered repair, and it applies when a cell
is outside ±1% of the target. A second repair is not registered.

### Name the diagnostic rank

Not adopted. A phase may name a winner only after the set passes byte parity
and the 4T minimum also wins at T and at 2T. The set failed byte parity. The
stable order stays a diagnostic.

## Decision

No change. ADR 0005 and ADR 0015 stay as written. Campaign `c58a86` has no
ternary winner and is not resumed. A later campaign may use a different band
only through an accepted ADR written before its first cell.

## Later (2026-10-07)

The owner accepted that later ADR the same day, before any new cell.
[ADR 0020](../0020-target-window-parity.md) withdraws the reciprocal spread check
for a successor. Acceptance does not reopen `c58a86` and does not name the
diagnostic minimum of its thirteen cells. The four alternatives above stay
unapplied to that set.
