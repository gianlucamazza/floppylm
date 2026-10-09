# ADR 0021: Start the next E0 campaign at the paired seeds

## Status

`amended` — 2026-10-09. Follows [ADR 0020](0020-target-window-parity.md).
Does not amend ADR 0020 decision 3: that decision still forbids copying 2-bit
from `c58a86`. Records [the paired-seed successor proposal](proposals/e0-paired-seed-successor.md).
[ADR 0022](0022-paired-campaign-on-109.md) amends decision 3 after campaign
`87686a` stopped on the 0.1.0.105 binding.

## Context

Campaign `e0-20261007T164712Z-766d4b` stored both phase selections and then
stopped at 2026-10-09T12:07:22Z in `paired-seeds`. Cell `031`, ternary seed 1,
failed on the console at trunk step 128 with `JSON write failed`. That job is
not a result. A failed device job is not resumed.

The stored ternary selection is `d` 80, 4 layers, `d_ff` 262, lr 0.01, wd 0.1
(1.4599/1.3375/1.2522). The stored 2-bit selection is `d` 96, 3 layers,
nominal `d_ff` 193, lr 0.003, wd 0.1. Trained cell `027` submitted `d_ff` 205
and scored 1.4914/1.3663/1.2766. The decision keeps the nominal width.
Replaying the grids would repeat closed measurements. Neither selection is the
scalar recipe: the paired comparison and the final test did not run.

## Decision

1. Campaign `e0-20261007T164712Z-766d4b` is not migrated. Cell `031` is not
   opened and is not recovered. The campaign is not resumed on package 0.1.0.105
   or any later package.
2. A new campaign may open at `paired-seeds` by copying the two stored
   decisions: ternary `d` 80, 4 layers, `d_ff` 262, lr 0.01, wd 0.1; 2-bit
   `d` 96, 3 layers, nominal `d_ff` 193, lr 0.003, wd 0.1. It does not copy
   submitted `d_ff` 205 and does not refill either width. It does not replay
   scale, MLP, tuning, or either grid. It does not copy 2-bit from `c58a86`.
3. The new campaign freezes `protocol_adr` `0020`, package 0.1.0.105, and the
   acceptance already bound to that package. All ten paired seeds train fresh
   under that one freeze. The existing ten-hash freeze and one final test
   follow. The scalar recipe is named only by that final test.
4. A failed device job stops the new campaign. There is no automatic second
   attempt of the same recipe.

## Consequences

The successor does not repeat the closed ternary or 2-bit measurements.
[ADR 0019](0019-host-init-pack.md) may still change the first submitted `d_ff`
of a fresh seed. S3 remains the single post-training repair. The stored recipe
width stays the nominal decision. A missing worker contract that persists is
still an acceptance error; a short reread of that file is not a second
training attempt.

## Amendment — 2026-10-09

Campaign `e0-20261009T150330Z-87686a` consumed the 0.1.0.105 binding and stopped
with no result. Run `87686a-000` and cell `031` stay closed. [ADR 0022](0022-paired-campaign-on-109.md)
authorizes one new paired campaign on package 0.1.0.109. Decisions 1 and 2, and
the stop rule in decision 4, are unchanged. Decision 3 remains the record of
the 0.1.0.105 binding and does not authorize another campaign on that package.

## Alternatives

Resuming cell `031` is refused: the device job failed. Replaying the grids
repeats closed cells and makes the later paired seeds a second campaign under
the same measurements. Naming either phase selection before the paired gate
would skip the comparison this campaign exists to finish.
