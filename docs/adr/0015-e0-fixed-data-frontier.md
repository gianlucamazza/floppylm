# ADR 0015: E0 compares at equal tokens; saturation is recorded

## Status

`accepted` — 2026-10-01; owner decision on
[proposal option B](proposals/e0-saturation-proposal.md).
Supersedes in part [ADR 0005](0005-e0v2-protocol.md) §4 (saturation as an eligibility
gate), [ADR 0007](0007-e0v2-review-gates.md) (scientific freeze requiring saturation),
[ADR 0008](0008-e0-numeric-protocol.md) consequences (unsaturated runs cannot be selected),
[ADR 0004](0004-miniature-budgets.md) Decision §1 (flat loss as a miniature eligibility
premise) and concept P4. Does not change ADR 0008 decision 1 (T = 20 × stored parameters),
byte parity, S2–S10, the paired gate or the final-test reservation.

## Context

Campaign `e0-20261001T090514Z-4236fd` stopped at `neutral-scale` because both row16
seeds failed `|bpb(4T) − bpb(2T)| < 0.01` by a factor of eight (Δ ≈ −0.08, three
trials including the S3 repair). Raising T until the gate would pass is not affordable
on one console under the measured 90 µs/token cost. Fitting an asymptote would make
the verdict a model. Stopping at the gate leaves E0 without a scalar frontier.

The measured numbers and the four options live in the
[proposal](proposals/e0-saturation-proposal.md). This ADR records option B.

## Decision

1. **Eligibility** of an E0 v2 trial is completed status plus individual and
   reciprocal serialized-byte parity, with at most one preregistered S3 repair.
   Saturation is **not** an eligibility gate.
2. **Saturation remains a recorded fact.** Every completed run still writes
   `|bpb(4T) − bpb(2T)|`, the signed delta and the verdict
   (`saturo` / `non saturo` / undetermined). No automatic extension past 4T.
3. **Comparisons are at equal tokens.** Cooldown ends stay T, 2T and 4T with
   T = 20 × stored parameters. Selection among eligible candidates is minimum
   mean 4T val bpb; declared enumeration order breaks ties.
4. **Rank stability.** A campaign phase may name a winner only if that 4T winner
   is also a minimizer of mean val bpb at T and at 2T. A flip stops the phase
   with a recorded instability. For the paired ternary/2-bit comparison, the sign
   of mean(ternary) − mean(2-bit) at 4T must match the sign at T and at 2T.
   Paired-gate magnitude (`max(0.02, 2σ)`) is evaluated at 4T.
5. **Scientific freeze** requires completed, non-smoke, byte-admissible runs with
   equal targets and artifact-verified parity. It does not require a saturated
   verdict.
6. **Claims.** E0 (and any miniature F1 signal that uses this protocol) is a
   **fixed-data frontier**, not a convergence result. Summaries and campaign
   reports must keep the signed saturation delta. Historical campaign `4236fd`
   is not migrated.

New campaigns freeze `protocol_adr` `0015`. Opening a campaign whose frozen
protocol differs is an error; there is no implicit migration.

## Consequences

The 55-trial cost model is unchanged. Unsaturated but byte-admissible trials
can be selected. Rank instability is a scientific stop, not a harness failure.
Byte parity, the paired gate, freeze/final-test reservation and S3 remain the
eligibility and protection boundary.

## Alternatives

A (raise T until `|Δ| < 0.01`), C (fit `L∞ + A·t^(−α)`), and no change were
rejected: A is not affordable on one console under the projection; C makes the
verdict a fitted model; no change produces no E0 frontier.
