# ADR 0002: Adversaries fixed before the thesis

## Status

`amended` — accepted 2026-09-30, amended 2026-09-30 (twice).

## Context

SmallerGPT, a sibling lab project, lost two lines to a trivial CharGRU (per its verdict).
Here the survey has already found an adversary stronger than the original thesis: at ~5 MB
pure recursion beats seed weights + LoRA by 0.15 bpb
([R2](../research/02-procedural-weights.md)). Parameter Golf also shows that int6 QAT + GPTQ +
Brotli is the reliable baseline and that model shape shifts the verdict
([R1](../research/01-tiny-lms.md), [R3](../research/03-mdl-compression.md)).

## Decision

1. Two adversaries, not one: the **dense low-bit frontier** (best E0 point at 1.44 MB, after
   shape search) and **pure recursion** (shared blocks, no seeds).
2. Same treatment for all arms: training tokens, hyperparameter and shape search budget,
   pruning, entropy coding, rate loss.
3. The dense frontier is frozen before E1 opens. It is not rerun after seeing E1.

## Consequences

- The thesis wins only if it beats pure recursion: the seeds must pay for their own bits.
- A win against the dense frontier alone is not a thesis result.

## Amendment — 2026-09-30 (stress test v0.1)

The stress test of thesis v0.1 ([concept § Stress test](../concept.md)) showed that on CPU a
comparison at equal tokens only is compute-limited and rewards the arm that is cheapest per token.

1. **Distillation for all**: every arm trains with the same distillation loss from
   a fixed teacher (TinyStories-33M, logits precomputed on disk), in addition to the NLL.
2. **Double parity**: every comparison reports both token parity and training FLOP parity.
3. **Adversary retrained** at the token/FLOP budget of the experiment that uses it; point 3
   of the Decision applies to shape and hyperparameters, not to the number of tokens.
4. **Paired gate**: mean difference between arms on the same seeds > max(0.02 bpb, 2σ), with σ
   measured in E0 over 3 seeds.
5. The third adversary is **ternary recursion** (pure recursion with a 1.58-bit core).

## Amendment 2 — 2026-09-30 (evaluation of the next steps)

Point 1 of the previous amendment is **suspended**. Distilling from TinyStories-33M is not feasible
as stated: different tokenizers (GPT-Neo 50k versus 256–1024) make the logits incomparable without
alignment, and full logits over ~10⁸ tokens require terabytes. TinyStories is already text generated
by a stronger teacher.

- Distillation leaves the critical path. It returns only as a uniform treatment for all
  arms, with **our own** teacher on the same tokenizer and top-16 logits on disk.
- Point 5 (ternary recursion) applies from the 1/4 budget; the E1 pilot at 1/16 has no recursion.
