# ADR 0011: Row scale policies for scientific E0

## Status

Accepted — 2026-10-01. The owner selected exclusion of tensor16 and approved
the completion plan. Supersedes only the tensor16 option in ADR 0008 decision 8.

## Context

The independent mixed zero/nonzero-row gate fails for tensor16. A single tensor
scale cannot preserve S9 for every row with the current even-level grids.

## Decision

Scientific E0 compares row16 and row8log with two neutral seeds. S9, FLP2,
numerical thresholds, tuning budget, byte parity and paired seeds are unchanged.
Tensor16 remains a functional codec diagnostic, outside scientific selection.

## Consequences

Freeze the two-policy campaign before observing results. Reject tensor16 scientific
submissions explicitly. Preserve earlier artifacts and accepted ADRs unchanged.

## Alternatives

A zero-row mask expands the format and byte-accounting scope. Weakening S9 changes
the accepted invariant. Neither alternative was selected.
