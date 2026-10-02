# Survey 12 — Evaluation under tiny budgets

Survey date: 2026-10-01. Thesis: v0.2. Bounded initial research pass: abstracts/central
claims and official repository rules; no full-text replication or exhaustive novelty certification.
The [roadmap](../roadmap.md) remains authoritative. Proposed experiments do not authorize runs.

## Question

What can a held-out bpb improvement establish at a tiny artifact budget?

## What exists

[TinyStories](https://arxiv.org/abs/2305.07759) proposes separate grammar, creativity and
consistency judgments. [Parameter Golf](https://github.com/openai/parameter-golf) provides an
explicit byte-normalized evaluation protocol. Likelihood and generated-story quality answer
related but distinct questions.

## What is missing

The counter-example search covered TinyStories and fixed-artifact evaluation protocols.
Neither establishes statistical power for FloppyLM's seeds, nor validates a local judge.
This audit has not inspected the prepared corpus: near-duplicate leakage is a risk to measure,
not a confirmed leak. Shared numeric seed labels also do not guarantee correlated initialization
across different parameter shapes.

## Implication for the thesis

Touches P2/P5 and F1/F4: report paired differences, sample size and effect threshold separately from confidence intervals. Preserve test reservation.

## Minimum experiment

Before E1 freeze primary metric, denominator, selection procedure and seed escalation. For E4 qualify the judge against blind human ratings. Report document-level spread and contamination diagnostics without changing old splits.
