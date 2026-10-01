# Survey 10 — Recursive and generated weights

Survey date: 2026-10-01. Thesis: v0.2. Bounded initial research pass: abstracts/central
claims and official repository rules; no full-text replication or exhaustive novelty certification.
The [roadmap](../roadmap.md) remains authoritative. Proposed experiments do not authorize runs.

## Question

Can sharing or generating weights improve quality at fixed bytes without hiding compute?

## What exists

[Relaxed Recursive Transformers](https://deepmind.google/research/publications/122290/)
shares layers in converted pretrained models. [Squeezing More from Limited Data](https://arxiv.org/abs/2608.26973)
studies recursive training and factorized embeddings at constrained data budgets.
[SeedLM](https://arxiv.org/abs/2410.10714) reconstructs pretrained weight blocks using pseudo-random
matrices and stored coefficients.

## What is missing

The counter-example search used “recursive transformer weight sharing language models 2025 2026”.
These sources establish precedents, not superiority at FloppyLM's bytes or tokenizer. An abstract-level
result is insufficient to copy a training recipe or infer its FLOP accounting.

## Implication for the thesis

Touches P2 and E1a: use scalar recursion controls; preserve the distinction between unique weights and executed depth.

## Minimum experiment

Preregister E1a with separate equal-token/equal-compute analyses and count adapters, embeddings, coefficients and assignment work. Do not combine all mechanisms in the first pilot.
