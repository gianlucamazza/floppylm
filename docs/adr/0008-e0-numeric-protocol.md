# ADR 0008: Freeze the E0 numerical protocol

## Status

`superseded-in-part` — accepted 2026-09-30. The owner accepted roadmap S1–S10 and requested implementation.
Completes [ADR 0005](0005-e0v2-protocol.md) without changing its scientific thresholds.
Superseded in part by [ADR 0011](0011-e0-row-scale-selection.md): the tensor16 option in decision 8.
Superseded in part by [ADR 0015](0015-e0-fixed-data-frontier.md): unsaturated runs may be selected; decision 1 (token base) is unchanged.

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
6. Forward FLOP/token = `2 × stored_parameters + 4 × layers × (ctx / 2) × d`.
   Estimated training FLOP = `3 × forward × tokens`; evaluation time is separate.
7. Sliding evaluation uses stride ctx/2, scores every target once and aligns the tail.
   The separator is a normal target. Val reads the first MiB; final test the first 2 MiB.
8. Select one scale policy from row16, row8log and tensor16 using the neutral A/B.
9. All-zero rows reconstruct exactly zero, including row8log code 0.
10. E0 uses exact text deduplication; near-duplicate filtering and OOD evaluation remain
    later requirements, not claims about this campaign.

## Consequences

No automatic training beyond 4T. Byte failures remain diagnostics, not scientific
selections. Saturation is recorded; [ADR 0015](0015-e0-fixed-data-frontier.md) allows
unsaturated, byte-admissible runs into selection. Retry cost is part of the reported
search cost. The actual token count after step rounding remains recorded alongside
requested T.

## Alternatives

Unlimited retries, padding and retrospective changes to the search budget would make
the comparison dependent on observed results and are rejected.
