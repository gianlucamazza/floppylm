# ADR 0007: Enforce E0 v2 review gates

## Status

`accepted` — accepted 2026-09-30, through approval of the four review corrections.
Clarifies [ADR 0005](0005-e0v2-protocol.md): selection and artifact invariants; does not change scientific thresholds.

## Context

Review of 35adcb1 found ignored evidence, lost grid arguments, optional selection gates,
and mutable loaded weights whose serialization reused older canonical records.

## Decision

- Ignore only the root artifact directory `/runs/`; retain evidence summaries and notes in Git.
- Grid children inherit token, branch and validation limits and the exact solver shape.
- Scientific freeze requires completed, non-smoke, saturated runs with equal byte targets,
  individual and pairwise byte parity verified against the actual hashed artifacts.
- `--freeze ... --functional` is an explicit separate path for smoke runs only. Selections
  and final-test outputs record their purpose. Functional evidence cannot certify a baseline.
- Loaded FLP2 models are inference-only. Disable parameter gradients, reject training mode,
  and verify configuration and all parameter values against their loaded state before saving.
  Resume training from a trunk checkpoint instead.

## Consequences

The inference snapshot consumes additional host RAM, not artifact bytes. Direct mutation is
reported at serialization instead of silently saving stale weights. Historical selections
without a purpose remain historical evidence and cannot be evaluated again by the new CLI.

## Alternatives

Automatic requantization would silently change the loaded model. Keeping parity as an optional
command would leave the scientific selection boundary unenforced. Both are rejected.
