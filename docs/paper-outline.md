# Paper scaffold: language-model quality under a floppy-sized description budget

Preparation scaffold, 2026-10-01. No results or publication novelty claim are implied.
Numbers come only from frozen [evidence](evidence/README.md); the [roadmap](roadmap.md) owns gates.

## Abstract

Fill only after the decisive comparison: task, complete accounting boundary, compared methods,
training regime, measured effect and uncertainty, computational cost, and whether the hypothesis held.

## Problem and scope

Define disk capacity, usable FAT12 area, cluster rounding, host exclusions and runtime resources
by reference to ADR 0001. Distinguish miniature model budgets from full image occupancy.
State the restricted story domain and the candidate comparative contribution.

## Related work

Use R1–R12. For each load-bearing citation record version, table/section and regime
(from scratch, PTQ or fine-tuning). Include contrary evidence and unresolved novelty searches.

## Representation and implementation

Define scalar, fixed-vector, learned-vector and computed-trellis representations. Separate nominal
rate, payload rate and complete artifact rate. Specify unique weights, recursion and reconstruction.
Bind source commits and backend packages; distinguish functional fixtures from scientific models.

## Experimental protocol

Record byte repair, search budget, train/val/test hashes, deduplication, tokenizer, seeds, stopping
rule and selection. Name the estimand: fixed tokens, fixed compute or convergence. Report assignment
and tuning cost. Explain effect threshold and uncertainty without calling 2σ a confidence interval.

## Results

| Budget | Arm | Actual bytes | Tokens | Estimated FLOPs | Held-out bpb | Seed differences | Saturation | Evidence hash |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

Populate only admissible frozen measurements. Publish a separate exclusion table with reasons.
A gate failure and an inconclusive undertrained comparison are different outcomes.

## Ablations

Learned versus generated books including all bytes; recursion with scalar controls; coding and
rate loss for every arm; tokenizer sensitivity under a preregistered protocol.

## Runtime and physical artifact

Only after E3/E4: binary size, full disk file ledger, reconstruction time, peak RSS, throughput,
reconstruction checks and C-runtime bpb. Provide the mounted data-disk reproduction procedure.

## Limitations and reproducibility

Document restricted domain, seed count, uncertainty, near-duplicate exposure, hardware scope,
compute estimation and extrapolation limits. Release configs, manifests, hashes, commands and
negative results. Unexecuted stages remain explicitly unexecuted.
