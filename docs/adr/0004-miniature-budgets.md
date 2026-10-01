# ADR 0004: Miniature floppies as a convergence proxy

## Status

`superseded-in-part` — accepted 2026-09-30, amended 2026-09-30.
Superseded in part by [ADR 0005](0005-e0v2-protocol.md): the 20 tokens per parameter rule (Decision §1).
Superseded in part by [ADR 0009](0009-xbox-e0-backend.md): the CPU-only execution requirement for E0 at 1/16 (Amendment §3, "all of E0 … on CPU"); other budgets are unchanged.

## Context

The product has fixed bytes and unlimited training; the lab has a CPU
([R6](../research/06-hardware-budget.md)): ~87M tokens/night at 5M params, ~8M at 30M. At 1.44 MB
the recursive and sub-bit arms stay under-trained by 10–100×, and a "dense wins" would be
a false negative caused by the lab's compute, not by the floppy's bytes.

## Decision

1. E0–E1 run at **three budgets**: 1/16, 1/4 and 1× of 11 Mbit (≈ 86 KB, 344 KB, 1.38 MB of
   model). At the two small budgets every arm must get close to saturation
   (≥ 20 tokens per stored parameter and a flat loss curve over the last 10% of training).
2. An F1 verdict requires the same sign at the two small budgets and a trend that does not close
   as the budget grows. The 1× point on CPU is indicative, not decisive.
3. Full scale at convergence runs only on rented GPU, with a dedicated ADR that fixes
   cost and runs.

## Consequences

- The thesis is decided on CPU before spending.
- An effect that exists only at 1× and not at the small budgets is not enough to pass F1.

## Amendment — 2026-09-30

1. **Model bytes only.** Runtime (~64 KB) and tokenizer are constants and at 1/16 would weigh
   almost as much as the model: at the miniature budgets only the coded model bytes are compared.
   The whole image counts only at 1×.
2. **Constant proportions.** Vocab and width are chosen per budget so that the embedding stays
   ~15% of the bits: at 1/16 a 1024 vocab would take 76% of them. Byte tokenizer (V=256) at 1/16 and
   1/4; BPE is evaluated only at 1×. bpb remains comparable across tokenizers.
3. **Compute.** Estimates at ~65 GFLOPS sustained: a run at 1/16 costs 0.5–1 h on CPU, one at 1/4
   6–17 h. All of E0 and the E1 pilot at 1/16 run on CPU; rented GPU for 1/4 and 1×
   (~$5–20 for the E1 grid) is decided by an ADR only if the pilot shows a signal.
4. Point 2 of the Decision applies to the final verdict; the pilot at 1/16 gives a signal, not a
   verdict.
