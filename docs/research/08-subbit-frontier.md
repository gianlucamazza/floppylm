# Survey 8 — Sub-bit frontier

Survey date: 2026-10-01. Thesis: v0.2. Bounded initial research pass: abstracts/central
claims and official repository rules; no full-text replication or exhaustive novelty certification.
The [roadmap](../roadmap.md) remains authoritative. Proposed experiments do not authorize runs.

## Question

Does existing work invalidate the candidate comparison at tiny from-scratch budgets?

## What exists

[BTC-LLM v2](https://arxiv.org/abs/2506.12040) reports binary-pattern codebooks and weight
transformations, with rates below one bit on existing LLM families. [QTIP](https://arxiv.org/abs/2406.11235)
uses stateful trellis codes with computed decoding in post-training quantization.
[Quant-Noise](https://arxiv.org/abs/2004.07320) combines training-time quantization noise and later
compression. These precedents prevent a claim that vector-coded, computed or sub-bit weights are new.

## What is missing

Searches on 2026-10-01 used “sub bit language model quantization training from scratch vector
codebook 2026” and “QTIP quantization trellises fractional bit rate”. No reviewed source established
the full FloppyLM comparison. This is a bounded search result, not proof of absence. R7's many
numerical claims still need a table/section audit before publication.

## Implication for the thesis

Touches F0 and F1: the candidate contribution is a measured comparative result, not a new coding family.

## Minimum experiment

Before E1, build a source table with training regime, denominator, model scale, all overhead and comparator; reject any novelty sentence contradicted by a row.
