# Survey 11 — Extreme-size language models

Survey date: 2026-10-01. Thesis: v0.2. Bounded initial research pass: abstracts/central
claims and official repository rules; no full-text replication or exhaustive novelty certification.
The [roadmap](../roadmap.md) remains authoritative. Proposed experiments do not authorize runs.

## Question

Which public benchmarks are informative about a complete 1.44 MB model?

## What exists

[TinyStories](https://arxiv.org/abs/2305.07759) studies small models in a synthetic short-story
domain. [Parameter Golf](https://github.com/openai/parameter-golf) explores larger fixed artifacts
with its own training and evaluation rules. Both are useful references; their results are not scores
on the FloppyLM protocol.

## What is missing

The counter-example search targeted Parameter Golf and tiny-model compression. A leaderboard
entry cannot establish what wins at one tenth the artifact size. Small model count and complete
disk occupancy are different constraints; general language competence remains unestablished.

## Implication for the thesis

Touches F0/F4 and communication: explain the floppy as an information budget and TinyStories as a restricted task.

## Minimum experiment

For E0/E1 compare only candidates evaluated on the same splits and accounting rules. Add external results as contextual rows, never as directly comparable frontier points.
