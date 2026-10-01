# E0 numerical validation refinement (proposal)

Status: accepted — 2026-09-30; recorded in ADR 0010, which supersedes the numerical
acceptance paragraph of ADR 0009.

## Context

The initial independent fixture exposed a flaw in the validation design: the first
AdamW step is compared after two different floating-point backward reductions.
For embedding element 1844, gradients -4.06435e-8 and -4.1441737e-8, each passing
the gradient gate, produce updated weights differing by 1.41759e-5 at lr 0.003.
AdamW epsilon makes this near-zero update ill-conditioned. This observation is
not evidence of a bug in AdamW; the optimizer must be tested with identical inputs.

The initial relative gate also requires absolute error below 1e-6 around outputs
of magnitude 0.01, despite the separately declared 1e-5 absolute allowance.

## Proposed decision

- Keep quantized symbols and serialized scale bytes exact. In particular row8log
  reconstructed fp32 values are compared through their canonical scale encoding.
- For floating-point outputs and gradients, use the preregistered mixed bound
  `abs(actual-reference) <= 1e-5 + 1e-4 * abs(reference)` on every finite element.
  Report both maximum absolute and relative errors; no averages conceal outliers.
- Test AdamW independently: feed the same initial weights, moments, gradients,
  learning rates, clipping and steps to Python and native optimizer. Apply the
  same mixed bound to parameters and both moments, including near-zero gradients.
- Retain the integrated one-step comparison as a diagnostic with its full error
  report, rather than treating two slightly different gradient inputs as a test of
  the optimizer implementation. Require its forward/gradient gates and finite state.
- Require exact uninterrupted/resumed native state equality and all existing
  scientific byte-parity, saturation and selection gates unchanged.
- Validate a held-out, independently generated fixture set after acceptance;
  the exploratory fixtures do not count as acceptance evidence.

## Consequences

This changes the numerical acceptance protocol after exploratory results and therefore
requires explicit owner acceptance and a superseding ADR. The campaign remains gated
until then. Neither a failing fixture nor a passing CPU fixture certifies Xbox GPU.

## Alternatives

Increasing the integrated weight tolerance until the observed example passes would
hide the ill-conditioned test and is rejected. Matching a particular CPU GEMM's
rounding on a different GPU is not a stable optimizer verification strategy.
