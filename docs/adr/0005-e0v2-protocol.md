# ADR 0005: E0 v2 protocol

## Status

`superseded-in-part` — accepted 2026-09-30.
Supersedes in part [ADR 0003](0003-lab-practices.md) §2 and §7 (parity, selection) and the "20 tokens per
parameter" rule of [ADR 0004](0004-miniature-budgets.md) §1. ADRs 0003 and 0004 remain valid for everything else.
Superseded in part by [ADR 0006](0006-flp2-only.md): the "including the legacy `FLP1`" part of §10 (no FLP1).
Clarified by [ADR 0007](0007-e0v2-review-gates.md): selection and artifact invariants.
Completed by [ADR 0008](0008-e0-numeric-protocol.md): the numerical choices this ADR left not yet approved (S1–S10) are resolved there.
Superseded in part by [ADR 0015](0015-e0-fixed-data-frontier.md): §4 saturation as an eligibility gate; the signed delta is still recorded.
Superseded in part by [ADR 0020](0020-target-window-parity.md): the reciprocal clause of decision 1.

## Context

The E0-lite grid (pre-v2) could not decide F1: shapes filling the budget between 0.88 and 0.99,
no saturation curve, an uncalibrated adversary, test evaluated inside the training run. Two
independent reviews converged on the corrections ([roadmap](../roadmap.md)).
This ADR records **only the decisions approved** by the user on 2026-09-30. The new numerical
choices, not yet approved at the time, were recorded separately and are resolved by
[ADR 0008](0008-e0-numeric-protocol.md).

## Decision

1. **Byte parity.** Nominal bits serve only the solver to propose shapes. Eligibility is
   decided on the actually serialized bytes (`len(pack(model))`): every candidate within ±1% of the target
   **and** `max(bytes)/min(bytes) − 1 ≤ 0.01` across the compared candidates. No padding. An out-of-tolerance
   run is kept as diagnostics and excluded from verdicts.
2. **Adjustment after entropy coding.** If an arm falls out of tolerance, its shape is readjusted with
   a rule declared before the campaign and with the same number of attempts per arm.
3. **WSD.** One trunk at constant LR with warmup; linear cooldowns to zero ending at T, 2T, 4T,
   each branched from a copy of the trunk. The trunk is never modified by the cooldowns. The
   trunk checkpoint contains model, optimizer, scheduler state, RNG and position in the
   data stream; resuming from a checkpoint is deterministic.
4. **Saturation.** Criterion `|bpb(4T) − bpb(2T)| < 0.01` on val, also recording the signed
   delta. If it fails at 4T, the run is declared **not saturated**; no automatic extension.
5. **Compute.** Tokens and estimated FLOPs are recorded separately for the trunk, for each cooldown and in total
   (search cost), together with the formula, the roundings and the resources consumed (wall
   clock, threads). Comparisons declare whether they are at equal tokens or at equal estimated compute.
6. **Tuning budget.** Fixed number of runs per arm, equal for all compared arms.
7. **Paired σ.** The gate σ is the standard deviation of the differences between two named conditions
   on the same seeds. The spread of a single model is not a paired σ.
8. **Protected selection.** Training and tuning read only train and val. Test is evaluated with a
   separate command, after saving a frozen selection bound to the artifact hashes.
9. **Traceability.** Every run has a unique id, an exclusively created directory, atomic writes, a state
   `running | completed | failed | interrupted`, and a manifest with hashes of data, sources, configuration,
   environment and artifact. An incomplete run never appears completed.
10. **Format.** `pack(unpack(blob)) == blob` for every supported format, including the legacy `FLP1`;
    loaded symbols and scales are canonical and are not requantized on re-save.

## Consequences

- Pre-v2 results remain as diagnostics in [`evidence/e0-lite/pre-v2`](../evidence/e0-lite/pre-v2/notes.md).
- No E0 v2 campaign starts before the choices to be approved are approved
  (done in [ADR 0008](0008-e0-numeric-protocol.md)).

## Amendment — 2026-10-01

[ADR 0015](0015-e0-fixed-data-frontier.md) keeps the §4 criterion and the signed
delta on every completed run, and removes saturation from eligibility and from
scientific freeze. Token base, cooldown ends and "no automatic extension" stand.

## Amendment — 2026-10-07

[ADR 0020](0020-target-window-parity.md) withdraws the reciprocal clause of
decision 1 (`max(bytes)/min(bytes) − 1 ≤ 0.01`). Each compared candidate must
still lie within ±1% of the shared target. Campaign `e0-20261004T103838Z-c58a86`
keeps the decision 1 result already recorded.
