# Concept — FloppyLM v0.2

Owner of the thesis, the principles and F0–F4. Status: **specified** (2026-09-30). v0.1 is kept
as a record in [§ Stress test v0.1](#stress-test-v01). Literature numbers live in the surveys;
our own numbers in [`evidence/`](evidence/README.md).

## Constraint

A language model whose whole image — weight description, tokenizer, runtime — fits on a real
3.5" HD floppy. The budget and what counts toward it are owned by
[ADR 0001](adr/0001-floppy-budget.md); after runtime and tokenizer, about **11 Mbit** remain for
the model ([R4](research/04-runtime-and-demoscene.md)).

## Starting observation

The floppy limits **bits at rest**, not RAM at runtime (1 GB,
[R6](research/06-hardware-budget.md)). A dense ternary model with zero-aware coding costs ~1.485
bits/weight: a ceiling of ~7M parameters ([R1](research/01-tiny-lms.md)). Beyond that lies the
**sub-bit regime**, where only one question matters: **where the bits are**. At 11 Mbit the
transformer core carries ~2/3–3/4 of them and the embedding the rest; any mechanism acting
elsewhere is decoration (the lesson of the stress test below, and of the closed SmallerGPT line).

## What is not new (partial F0)

Seed weights with adapters, from-scratch product quantization, low-rank sign templates and learned
sub-bit codebooks all exist; the comparison table is owned by [positioning](positioning.md).

No work found trains an LM from scratch with a **vector-coded core below 1 bit/weight** and compares
**learned, seed-generated and computed codes** at exactly equal coded bytes, under 1.5 MB, with a
bootable artifact. The claimable novelty is that comparison and its result, not the mechanism.

## Thesis

**Below one bit, a recursive core whose weights are indices into a vector code beats, at equal
coded bytes, the best scalar core (ternary, 2-bit) with the same recursion.**

The core is written `W = D(indices)`: blocks of `v` weights → one index of `r·v` bits
(0.5–0.75 bits/weight), with three competing decoders `D`:

| Arm                  | Code                                      | Code bytes                                 | Literature prior (R7)                        |
| -------------------- | ----------------------------------------- | ------------------------------------------ | -------------------------------------------- |
| **VQ-seed**          | PRNG-generated codebook, fixed            | 0                                          | favoured: QTIP, FSQ, "only the ranks matter" |
| **Computed trellis** | QTIP-style computed code, fractional rate | 0                                          | favoured, beats VQ-8 at equal rate on LLMs   |
| **Learned VQ**       | learned codebook, shared across layers    | K·v·b_c (~0.8 Mbit at K=4096, v=24, 8 bit) | disfavoured: pays for its own bytes          |

The trellis requires Viterbi quantization inside the training loop: it enters in E1b, after the
pilot with VQ-seed and learned VQ ([roadmap](roadmap.md)).

The bet is not "learned beats random": it is that **when training from scratch, the weights adapt
to the code**, and the sub-bit regime becomes reachable without the sign wall (Sign Lock-In, R7).
The learned vs computed comparison is preregistered with a prior against the learned code: if the
learned code wins, it must do so including the codebook bytes.

Indicative accounting at 11 Mbit (d=384, V=1024 tied):

| Component                   | Params                     | bits/param | Mbit                      |
| --------------------------- | -------------------------- | ---------- | ------------------------- |
| Embedding                   | 0.39M                      | 4          | 1.6                       |
| Core, VQ at 0.5 bits/weight | ~18.6M unique (~10 blocks) | 0.5        | 9.3                       |
| Codebook (learned VQ only)  | —                          | —          | 0.8 (taken from the core) |
| Norms, scales               | —                          | —          | 0.1                       |

Against ternary (~6M core params, ~3.5 blocks) the sub-bit core has ~3× the unique weights;
recursion multiplies them further. The 4-bit embedding is now ~15%: a vocabulary of 512–2048 is
chosen in E0.

## Principles

- **P1 — Count everything.** The number is `image_bytes` on the real file ([ADR 0003](adr/0003-lab-practices.md)).
- **P2 — Strong adversaries, treated equally.** Dense ternary/2-bit and ternary recursion, same
  entropy coding, same rate loss; double token/FLOP parity
  ([ADR 0002](adr/0002-adversary-dense-frontier.md)).
- **P3 — Coded bytes, not nominal bits.** VQ indices are near maximum entropy, while sparse
  ternary gains from entropy coding: comparisons happen after coding (R7, F2).
- **P4 — Equal tokens before the verdict.** F1 is decided at the miniature budgets at equal
  tokens, with rank stability across T, 2T and 4T. Saturation is recorded; unsaturated
  comparisons are a fixed-data frontier
  ([ADR 0015](adr/0015-e0-fixed-data-frontier.md), [ADR 0004](adr/0004-miniature-budgets.md)).
- **P5 — Quality per byte, not "runs on a floppy".** Held-out bpb from the C runtime; TinyStories
  coherence is secondary ([R5](research/05-eval-tiny.md)).

## Falsification

Every F\* uses the paired gate defined in [ADR 0002](adr/0002-adversary-dense-frontier.md)
(amendment) and [ADR 0005](adr/0005-e0v2-protocol.md) §7, with σ measured in E0.

| F      | Fires if                                                                                                                                                | Attacked by                                                                                                     |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| F0     | A work already makes the learned/seed/computed comparison below 1 bit, from scratch, ≤ 1.5 MB                                                           | continuous; today **partial** ([R2](research/02-procedural-weights.md), [R7](research/07-learned-vq-subbit.md)) |
| F1     | No vector arm beats the best of ternary and 2-bit (same recursion) on coded bytes, at both miniature budgets                                            | E1                                                                                                              |
| F1-abl | Learned VQ does not beat the best of VQ-seed and trellis: learning the code does not matter (expected; decides the mechanism, does not kill the thesis) | E1                                                                                                              |
| F2     | The advantage disappears when all arms get entropy coding + rate loss                                                                                   | E2                                                                                                              |
| F3     | Expansion > 60 s, RSS > 1 GB, or < 5 tok/s on the C binary                                                                                              | E3                                                                                                              |
| F4     | Coherence not non-inferior to TinyStories-8M (margin 0.5), or below grammar 6 / consistency 5                                                           | E4                                                                                                              |

## Declared limits

- TinyStories domain: no factual knowledge is expected.
- No GPU rental in the approved scope ([completion plan](completion-plan.md)); changing that requires a
  dedicated ADR ([ADR 0004](adr/0004-miniature-budgets.md));
  E0 at 1/16 runs on the Series S backend ([ADR 0009](adr/0009-xbox-e0-backend.md)).
- Evaluation fixed before the numbers: no n-gram cache or TTT at evaluation ([R2](research/02-procedural-weights.md)).
- Pure straight-through VQ-QAT is fragile (Quant-Noise: worse than post-training); the recipe is
  partial quantization / periodic snapping with dead-code reseeding (R7).

## Stress test v0.1

Record of thesis v0.1 (2026-09-30), closed before it was implemented.

**Thesis v0.1.** A shared recursive core perturbed per iteration:
`W[b,k] = W_core[b] + Σ_j c[b,k,j]·G(seed[b,k,j])`, coefficients `c` under an MDL loss.

**Why it was closed** (own assessment + independent cold reviewer, convergent):

1. **Where the bits are.** At V=2048, d=384: embedding ~28%, core ~64%, coefficients `c`
   **0.03–0.2%**. The thesis innovated on the component that does not carry the signal.
2. **The seed carries no information.** J random directions in D≈d² capture a J/D fraction of the
   energy of a useful delta; searching a 16-bit seed gives a maximum cosine ≈ √(2 ln 2¹⁶ / D)
   ≈ 0.012. The "extra" parameters have zero bits: the rate loss pushes `c` → 0.
3. **Prior against.** At ~5 MB pure recursion beats seed + LoRA by 0.15 bpb (R2); at equal bits,
   iteration embeddings, IA³ and rank-1 LoRA have aligned directions and dominate isotropic ones.
4. **Methodology.** On CPU, E1 was compute-limited; gates had no σ; distillation was missing.
   Corrected in [ADR 0002](adr/0002-adversary-dense-frontier.md) (amendment) and
   [ADR 0004](adr/0004-miniature-budgets.md).

The test that formally closes it is **E1a** in the [roadmap](roadmap.md), after the E1 pilot: it is
needed anyway to choose the recursion for the 1/4 budget. The procedural spirit survives, moved to
where the bits are: the seed-generated codebook is now a favoured core arm.
