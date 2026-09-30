# ADR 0010: Independent numerical gates for the Xbox backend

## Status

Accepted — 2026-09-30, explicit owner acceptance of `docs/e0-validation-proposal.md`.
Supersedes only the numerical acceptance paragraph of ADR 0009.

## Context

Exploratory fixtures showed that an integrated first AdamW step is ill-conditioned
near epsilon: gradients around -4e-8, differing by 8e-10, produced a weight difference
of 1.41759e-5. Both gradients met their gate. An optimizer comparison must use the
same inputs, not the outputs of two different floating-point backward reductions.
Separate maxima for absolute and relative error also impose an unintended sub-1e-6
allowance near reference magnitude 0.01.

## Decision

- Symbols and serialized scale bytes must be exact; row8log is compared by canonical
  encoding, not by an implementation-specific exp2 reconstruction.
- For finite floating-point outputs, gradients and isolated optimizer state, require
  every element to satisfy `abs(actual-reference) <= 1e-5 + 1e-4 * abs(reference)`.
  Report maximum absolute/relative errors and the largest violation of the bound.
- Test AdamW with identical initial weights, moments, gradients, learning rates,
  clipping and step numbers in Python and C++. Include near-zero gradients and
  multiple steps. Compare parameters and both moments.
- Retain integrated one-step weight error as a diagnostic, requiring valid forward,
  gradients and finite state. It does not replace the isolated optimizer gate.
- Native uninterrupted/resumed state equality remains exact. Scientific byte-parity,
  saturation, paired-seed and selection gates remain unchanged.
- Generate a held-out fixture set after acceptance. Exploratory fixtures are not
  acceptance evidence. Passing CPU fixtures does not certify Xbox GPU execution.

## Consequences

The acceptance protocol changes explicitly after exploratory results; the old failure
remains part of the record. Backend acceptance requires the revised independent gates
and real console evidence before any scientific E0 campaign.

## Alternatives

Increasing a first-step weight tolerance until a particular example passes hides an
ill-conditioned oracle. Reproducing one CPU GEMM's rounding on a different GPU is
not a stable optimizer specification. Both are rejected.
