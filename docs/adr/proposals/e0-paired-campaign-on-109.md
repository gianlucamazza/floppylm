# One paired campaign on package 0.1.0.109

## Status

accepted — 2026-10-09; recorded in [ADR 0022](../0022-paired-campaign-on-109.md).

## Context

[ADR 0021](../0021-paired-seed-successor.md) decision 3 froze the paired
successor on package 0.1.0.105. Campaign `87686a` opened on that package and
stopped when run `87686a-000` failed at trunk step 64 with `JSON write failed`.
No branch was written. Package 0.1.0.109 then passed its own gates and is
bit-identical 38/38 to 0.1.0.105. The stored `766d4b` decisions are unchanged,
and the paired comparison has not run.

## Decision

Leave `87686a` and cell `031` closed. Authorize one new `--from-paired`
campaign on 0.1.0.109, bound to that package's published acceptance and
benchmark. Copy nominal `d_ff` 193, not submitted `d_ff` 205. Train all ten
seeds fresh. A failed device job stops that campaign.
