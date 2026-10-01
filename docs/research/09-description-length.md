# Survey 9 — Description length

Survey date: 2026-10-01. Thesis: v0.2. Bounded initial research pass: abstracts/central
claims and official repository rules; no full-text replication or exhaustive novelty certification.
The [roadmap](../roadmap.md) remains authoritative. Proposed experiments do not authorize runs.

## Question

Which bits must a generated-weight model pay for?

## What exists

[Blier and Ollivier](https://arxiv.org/abs/1802.07044) distinguish model-description costs and
incremental data encoding. [Parameter Golf](https://github.com/openai/parameter-golf) makes artifact
size and evaluation rules explicit. An online retraining decoder is a different operational object
from a ready-to-generate model description.

## What is missing

No reviewed source derives a tight language-quality bound for a complete floppy-sized artifact.
The search for a counter-example used fixed-size Parameter Golf artifacts; formal lower bounds
remain an open task. “More weights” is not “more encoded information”.

## Implication for the thesis

Touches P1/P3 and F2/F3: fixed generators have no learned table payload, but generator identifiers, seeds and runtime code still count.

## Minimum experiment

For E2/E3 produce a component ledger from real serialized files; reconcile its sum with artifact length and cluster-rounded image occupancy. Label theoretical entropy separately.
