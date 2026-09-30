# ADR 0008: Freeze the E0 numerical protocol

## Status

Accepted — 2026-09-30. The owner accepted roadmap S1–S10 and requested implementation.
Completes ADR 0005 without changing its scientific thresholds.

## Context

The bench implemented numerical defaults before the campaign was authorized. E0 must
declare its recipe and search budget before observing scientific results.

## Decision

1. T is 20 times stored quantized parameters. Cooldowns end at T, 2T and 4T.
2. Linear warmup occupies 2% of T; each isolated cooldown occupies its last 10%.
3. A candidate outside serialized byte parity gets at most one fresh training attempt.
   Keep width, layer count and recipe; solve d_ff using the measured coded/nominal ratio
   of the 4T artifact. Preserve both attempts and exclude a still-ineligible candidate.
4. Tuning has six configurations per arm: lr {1e-3, 3e-3, 1e-2}; ternary delta {0.5, 0.7}
   with wd 0.1; 2-bit wd {0, 0.1}.
5. Use at least three paired seeds, five near the gate; the final E0 paired comparison
   uses seeds 0–4 for the selected ternary and 2-bit recipes.
6. Forward FLOP/token = 2 _ stored parameters + 4 _ layers _ (ctx / 2) _ d.
   Estimated training FLOP = 3 _ forward _ tokens; evaluation time is separate.
7. Sliding evaluation uses stride ctx/2, scores every target once and aligns the tail.
   The separator is a normal target. Val reads the first MiB; final test the first 2 MiB.
8. Select one scale policy from row16, row8log and tensor16 using the neutral A/B.
9. All-zero rows reconstruct exactly zero, including row8log code 0.
10. E0 uses exact text deduplication; near-duplicate filtering and OOD evaluation remain
    later requirements, not claims about this campaign.

## Consequences

No automatic training beyond 4T. Byte failures and non-saturated candidates are
diagnostics, not scientific selections. Retry cost is part of the reported search cost.
The actual token count after step rounding remains recorded alongside requested T.

## Alternatives

Unlimited retries, padding and retrospective changes to the search budget would make
the comparison dependent on observed results and are rejected.
