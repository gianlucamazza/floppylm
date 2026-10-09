# ADR 0022: One paired campaign on package 0.1.0.109

## Status

`accepted` — 2026-10-09. Amends decision 3 of [ADR 0021](0021-paired-seed-successor.md).
Does not amend decisions 1 or 2, and does not amend the stop rule in decision 4.
Records [the 0.1.0.109 paired-campaign proposal](proposals/e0-paired-campaign-on-109.md).

## Context

ADR 0021 decision 3 froze the paired successor on package 0.1.0.105 and on the
acceptance already bound to that package. Campaign `e0-20261009T150330Z-87686a`
opened under that decision and stopped at 2026-10-09T15:12:23Z. Run
`87686a-000` failed on the console at trunk step 64 with `JSON write failed`
and wrote no branch. It is not a result. Decision 4 stopped that campaign.
There is no second attempt of that run.

Package 0.1.0.109 later passed its own hardware gates and is bit-identical
38/38 to 0.1.0.105
([evidence](../evidence/xbox-e0-20261009-109/notes.md)). That acceptance is
not the acceptance named by decision 3. The stored decisions of `766d4b` are
unchanged. The paired comparison and the final test still have not run.
Functional qualification does not show that the scientific write failure is
gone.

## Decision

1. Campaign `e0-20261009T150330Z-87686a` stays stopped on 0.1.0.105. Run
   `87686a-000` is not recovered. Cell `031` of `766d4b` stays closed.
   `766d4b` is not migrated.
2. One new campaign may open at `paired-seeds` on package 0.1.0.109. It binds
   the acceptance and benchmark published for that package. It copies the
   decisions in ADR 0021 decision 2, including nominal `d_ff` 193 and not
   submitted `d_ff` 205. It does not refill either width and does not replay
   scale, MLP, tuning, or either grid. All ten paired seeds train fresh.
   `protocol_adr` stays `0020`.
3. This amendment authorizes that one campaign. A failed device job stops it.
   There is no automatic second attempt of the same recipe. The scalar recipe
   is named only by its final test.
4. ADR 0021 decision 3 remains the record of the 0.1.0.105 binding. It does
   not authorize another campaign on 0.1.0.105.

## Consequences

The host freeze is the tree at launch. A later open failure is read from the
Win32 code in the device message and stops the campaign. S3 remains the single
post-training repair. [ADR 0019](0019-host-init-pack.md) may still change the
first submitted `d_ff` of a fresh seed. The stored recipe width stays the
nominal decision.

## Alternatives

Resuming `87686a` is refused: the device job failed. Opening another campaign
on 0.1.0.105 would reuse a binding whose campaign already stopped. Replaying
the grids would repeat closed measurements.
