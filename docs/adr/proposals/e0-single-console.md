# E0 stays on one accepted Series S

## Status

Not adopted — 2026-10-05. Does not amend [ADR 0009](../0009-xbox-e0-backend.md). Does not
authorize a second device, a cloud backend, or a move of campaign `c58a86`.

## Context

Campaign `c58a86` is running on the accepted Series S package. The cells still to run are
a serial queue on that console. Three ways to shorten the queue were considered.

## Alternatives

### Cloud GPU

Rejected. [ADR 0009](../0009-xbox-e0-backend.md) binds scientific E0 at 1/16 to the Series S
package, one GPU job at a time. CPU or WARP execution cannot certify those results. A
cloud GPU is a different backend and would be a different campaign.

### A faster host

Not adopted for this campaign. The console does the training. The host hashes the corpus
and scores validation, which is a fraction of a cell. A cloud host would put a tunnel
between the runner and the console. The campaign stays on the LAN host beside the console.

### A second console

Rejected. The campaign has one acceptance and one GPU job. The same recipe on this
console already produced different artifacts:
[trial 012](../../evidence/e0-v2/runs/e0-20261004T103838Z-c58a86-012/notes.md) and
[trial 006](../../evidence/e0-v2/runs/e0-20261004T103838Z-c58a86-006/notes.md). Splitting
later cells across devices would split the instrument.

## Decision

No change. `c58a86` continues on its accepted package. A later campaign that uses another
backend needs its own acceptance and its own ADR.

## Later (2026-10-07)

Campaign `c58a86` stopped at 2026-10-07T12:26:34Z during ternary selection. That
stop does not adopt another console or a cloud backend. The decision above stays
not adopted.
