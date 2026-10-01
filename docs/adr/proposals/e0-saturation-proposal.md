# E0 saturation gate at 1/16 (proposal)

## Status

Proposed — 2026-10-01. Awaiting an owner decision; nothing below is accepted. Campaign
`e0-20261001T090514Z-4236fd` was stopped on 2026-10-01 after both row16 seeds proved unsaturated.

## Context

[ADR 0005](../0005-e0v2-protocol.md) §4 makes a run eligible only if
`|bpb(4T) − bpb(2T)| < 0.01` on val; [ADR 0008](../0008-e0-numeric-protocol.md) decision 1 sets
T = 20 × stored parameters. `experiments/e0_campaign.py` excludes any trial that fails either
byte parity or saturation, and `neutral()` stops the campaign when no neutral candidate
remains comparable.

The first scientific trial at 1/16 (ternary, row16, GELU, d=96, 3 layers, d_ff=391; about
360k stored parameters) measured:

| Cooldown end | Tokens     | val bpb | Δ to previous |
| ------------ | ---------- | ------- | ------------- |
| T            | 7 200 768  | 1.5148  | —             |
| 2T           | 14 401 536 | 1.3938  | −0.1210       |
| 4T           | 28 803 072 | 1.3120  | −0.0818       |

Source: [run summary](../../evidence/e0-v2/runs/e0-20261001T090514Z-4236fd-000/summary.json).

Its preregistered S3 byte repair (d_ff 391 → 400, T = 892 steps) reached byte parity
(fill 0.999–1.001) and confirmed the curve: val bpb 1.5155, 1.3951, 1.3160, Δ(2T→4T) = −0.0791,
still not saturated, so the trial was excluded
([repair summary](../../evidence/e0-v2/runs/e0-20261001T090514Z-4236fd-000-repair/summary.json)).
Because `neutral()` needs both seeds of a candidate, row16 can no longer be selected. The second
row16 seed (`4236fd-001`) gave val bpb 1.5273, 1.4052, 1.3204 (Δ(2T→4T) = −0.0848): the gap is
stable across seeds. The owner stopped the campaign at that point
([record](../../evidence/e0-v2/campaigns/e0-20261001T090514Z-4236fd/notes.md)).
The gate fails by a factor of eight. If the next three neutral trials behave alike, the campaign
stops at `neutral-scale` before tuning, grids or paired seeds.

**Projection (an assumption, not a measurement).** The gain per doubling shrank by a ratio of
0.676 (0.657 in the repair). Holding that ratio, Δ falls below 0.01 only between 128T and 256T, i.e. at about
5 000 tokens per stored parameter, and the asymptote would be near 1.14 bpb. Other shapes and
formats may decay differently; one trial cannot calibrate this.

**Cost model (measured on package 0.1.0.28).** Training took 2 795 s for 30.95M tokens
(90 µs/token, roughly linear in tokens) plus 285 s of host evaluation. A 4T trial costs about
52 min; the campaign has about 55 sequential trials.

## Options

**A. Keep the criterion, raise the token base.** Cooldowns at k·T, 2k·T, 4k·T.

| Last cooldown | Per trial | 55 trials | Projected Δ at the end |
| ------------- | --------- | --------- | ---------------------- |
| 16T           | ~3.2 h    | ~7 days   | 0.037 (still fails)    |
| 64T           | ~12.5 h   | ~29 days  | 0.017 (still fails)    |
| 256T          | ~50 h     | ~114 days | 0.008                  |

Keeps P4 ("convergence before the verdict") literally; under the projection it is not affordable
on one console.

**B. Compare at equal tokens, record saturation.** Saturation stops being an eligibility gate;
arms are compared at the same token count, and a verdict requires the same sign and gate at T,
2T and 4T (rank stability). The signed Δ stays in every summary. Cost unchanged. It amends ADR 0005
§4, ADR 0004's convergence premise and concept P4: the E0 frontier becomes a frontier at fixed
data, and claims must say so.

**C. Extrapolate the asymptote.** Add cooldown ends (for example T…16T, five points) and fit
`L(t) = L∞ + A·t^(−α)` per run; compare L∞ with its fitted uncertainty. Three points leave zero
degrees of freedom, so at least five are needed. About 4× the current cost (~3.2 h per trial,
~7 days), and the verdict depends on the fitted model.

**No change.** The campaign stops at its gate; E0 records that no 1/16 shape saturates at 4T and
nothing beyond `neutral-scale` is measured.

## Decision requested

Choose A, B, C or no change, or a variant. Whatever is chosen becomes a new ADR that names the
amended clauses (ADR 0005 §4, ADR 0008 decision 1, and for B also ADR 0004 and concept P4), and a
new campaign with fresh preregistration. Byte parity, S2–S10, the paired gate and the final-test
reservation are not in question.
