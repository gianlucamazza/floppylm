# ADRs — structural decisions

An ADR exists only for a decision that is **already taken** and expensive to reverse.
It is not a brainstorm, a survey or a TODO.

## Rules

1. **Status token**, first line of `## Status`: `accepted` | `amended` | `superseded-in-part` |
   `superseded`, followed by the dates. When several apply, the most significant wins
   (`superseded` > `superseded-in-part` > `amended` > `accepted`).
2. **No silent rewrites.** An ADR is amended with a dated `## Amendment — <date>` section, or
   superseded by a new ADR. Translation and link fixes are not amendments.
3. **Reciprocal links.** Every relation (supersedes, amends, completes, clarifies) is stated in the
   Status of both ADRs.
4. **Structure**: `# ADR NNNN: Title`, then `## Status`, `## Context`, `## Decision`,
   `## Consequences`, optionally `## Alternatives` and amendments.
5. **Proposals** live in [`proposals/`](#proposals) while under review. Accepting one creates an
   ADR; the proposal then states `accepted — <date>; recorded in ADR NNNN` and stays as context.
6. Normative design ([concept](../concept.md), [roadmap](../roadmap.md)) applies ADRs and does not
   duplicate them. No ADR "for completeness": a negative result that closes a line needs a
   roadmap paragraph and a [STATUS](../STATUS.md) update, not a cancellation ADR.

## Index

| ADR                                         | Decision                                                                                                       | Status             |
| ------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | ------------------ |
| [0001](0001-floppy-budget.md)               | The budget is the floppy, not the parameters: ≤ 1 457 664 B of FAT12 data area; what counts and what does not  | amended            |
| [0002](0002-adversary-dense-frontier.md) | Adversaries fixed before the thesis: dense low-bit frontier and pure recursion (+ ternary recursion from 1/4); double token/FLOP parity; paired gate | amended            |
| [0003](0003-lab-practices.md)               | Lab invariants: bit accounting, seeds, evidence, stop on F\*                                                   | superseded-in-part |
| [0004](0004-miniature-budgets.md) | Budgets 1/16, 1/4, 1×: model bytes only in miniature (whole image at 1×), embedding ~15%; GPU only with an ADR | superseded-in-part |
| [0005](0005-e0v2-protocol.md)               | E0 v2 protocol: serialized-byte parity, WSD, saturation, compute, protected selection, traceability            | superseded-in-part |
| [0006](0006-flp2-only.md)                   | FLP2 is the only format; FLP1 is rejected, readable only at revision `f9e0732`                                 | accepted           |
| [0007](0007-e0v2-review-gates.md)           | Review gates: scientific/functional freeze, exact grid arguments, inference-only artifacts, tracked evidence   | accepted           |
| [0008](0008-e0-numeric-protocol.md)         | S1–S10 numerical recipe, bounded byte repair and paired seeds                                                  | superseded-in-part |
| [0009](0009-xbox-e0-backend.md)             | Independent Python oracle and a separate Xbox GPU training backend for E0 at 1/16                              | superseded-in-part |
| [0010](0010-independent-numerical-gates.md) | Identical-input optimizer and accepted mixed floating-point gate                                               | accepted           |
| [0011](0011-e0-row-scale-selection.md)      | Scientific E0 uses row16/row8log only, preserving S9 and FLP2                                                  | accepted           |
| [0012](0012-repo-boundaries.md)             | floppylm owns FloppyLM semantics; xbox-gpu-training is the only native backend; no FloppyLM in xllama          | accepted           |
| [0013](0013-e1-functional-qualification.md) | Isolated E1 functional qualification (vector/BPE oracles); scientific E1 remains gated | accepted |

## Proposals

| Proposal                                                                  | Outcome             |
| ------------------------------------------------------------------------- | ------------------- |
| [E0 numerical validation refinement](proposals/e0-validation-proposal.md) | accepted → ADR 0010 |
| [E0 zero-row gate correction](proposals/e0-zero-row-proposal.md)          | accepted → ADR 0011 |
| [Isolated E1 functional qualification](proposals/e1-qualification-proposal.md) | accepted → ADR 0013 |
