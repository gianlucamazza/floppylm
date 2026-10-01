# E0 zero-row gate correction (proposal)

Status: accepted — 2026-10-01; recorded in ADR 0011.
This is separate from the accepted numerical refinement in ADR 0010.

## Context

ADR 0008 decision 9 accepts scale 0 and exact zero reconstruction for all-zero rows
in every format. The existing Python oracle explicitly exempts tensor16 from its
mixed zero/nonzero-row test (`tests/test_codec.py`). The native backend matches
that oracle; agreement does not establish this independent protocol invariant.

Diagnostic input: `[[0,0,0,0],[1,-1,2,-2]]`.
For 2bit/tensor16 the zero row reconstructs to four values of `0.425537109375`;
for 4bit/tensor16 to four values of `0.157470703125`. The ternary zero row
reconstructs to zero, but still shares a nonzero tensor scale. Row16 and row8log
meet both parts of S9 for all three formats. All-zero tensors meet the current
codec contract for tensor16; individual zero rows in a mixed tensor do not.

A single shared tensor scale cannot independently encode a zero row. Even-level
2/4-bit grids contain no zero symbol. Preserving every existing nonzero level and
exact zero rows needs additional metadata, which the current tensor16 payload
and bit-accounting do not represent.

## Proposed decision

Exclude tensor16 from scientific E0 scale selection; compare row16 and row8log
with the same two neutral seeds and byte-parity gates. Keep tensor16 available for
functional/reference diagnostics with its existing encoding. Do not modify FLP2,
serialized bytes or numerical thresholds. Before scientific job submission,
validate the independent mixed zero/nonzero-row invariant for every participating
core and embedding format.

Record acceptance in a new ADR superseding only the tensor16 option in ADR 0008
choice 8 and clarifying how choice 9 gates scientific selection. Existing accepted
ADRs remain unchanged. No scientific run has started.

## Consequences

The scale A/B has two eligible policies. Other recipe, retry, seed, saturation,
parity and final-test gates remain as accepted. Existing tensor16 artifacts retain
their encoding and can still be inspected or used as diagnostics.

## Alternatives

- Change S9 to require exact zero only for an entirely zero tensor under tensor16.
  This preserves three policies but weakens the explicitly accepted row invariant.
- Design and version a tensor16 policy with a serialized zero-row mask. This preserves
  the invariant with extra counted bytes, but expands the codec/format scope and
  requires a separately reviewed format decision.
- Silently change the oracle, ignore the failing invariant, or claim the existing
  GPU fixtures prove S9: rejected.
