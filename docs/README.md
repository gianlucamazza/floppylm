# FloppyLM documentation

The [root README](../README.md) is the public story. This page tells you **which document owns
which fact** and where to start.

## Reading paths

**Newcomer (15 minutes)**

1. [vision](vision.md): what success means.
2. [concept](concept.md): the thesis and what kills it (F0–F4).
3. [positioning](positioning.md): what already exists.
4. [ADR 0001](adr/0001-floppy-budget.md): what counts toward the floppy.
5. [roadmap](roadmap.md) and [completion plan](completion-plan.md): what is measured, in which order.
6. [STATUS](STATUS.md): where things stand today.

**Operator** (running E0): [STATUS](STATUS.md) → [Xbox runbook](operations/xbox-e0.md) →
[code map](operations/code-map.md) → [stack](stack.md).

**Reviewer** (checking a claim): [evidence](evidence/README.md) → the owning [ADR](adr/README.md)
→ [glossary](glossary.md).

## Fact owners

Update the owner; every other document links to it instead of copying.

| Fact                                           | Owner                                                                                                                              |
| ---------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| Live state: package, campaign, what is running | [STATUS](STATUS.md)                                                                                                                |
| Mission, success, non-goals                    | [vision](vision.md)                                                                                                                |
| Thesis, principles P1–P5, F0–F4, v0.1 record   | [concept](concept.md)                                                                                                              |
| Prior art comparison                           | [positioning](positioning.md)                                                                                                      |
| Floppy budget and what counts                  | [ADR 0001](adr/0001-floppy-budget.md)                                                                                              |
| Adversaries and the paired gate                | [ADR 0002](adr/0002-adversary-dense-frontier.md) (amendment), [ADR 0005](adr/0005-e0v2-protocol.md) §7                             |
| E0 protocol; S1–S10 values | [ADR 0005](adr/0005-e0v2-protocol.md); the accepted table in the [roadmap](roadmap.md#e0-v2--accepted-numerical-choices), recorded by [ADR 0008](adr/0008-e0-numeric-protocol.md) and [ADR 0011](adr/0011-e0-row-scale-selection.md); eligibility and rank stability in [ADR 0015](adr/0015-e0-fixed-data-frontier.md); byte comparison in [ADR 0020](adr/0020-target-window-parity.md) |
| Approved completion scope and execution order  | [completion plan](completion-plan.md) |
| E0–E4 definitions and completion gates         | [roadmap](roadmap.md)                                                                                                              |
| Xbox procedure                                 | [runbook](operations/xbox-e0.md)                                                                                                   |
| Native backend contracts (`floppylm.*.v1`) and the inbox protocol | [schemas](../schemas/README.md), [inbox protocol](contracts/inbox-protocol.md) |
| Modules and CLI flags                          | [code map](operations/code-map.md)                                                                                                 |
| Toolchain and machines                         | [stack](stack.md)                                                                                                                  |
| Measured numbers                               | [evidence](evidence/README.md)                                                                                                     |
| Literature and gaps                            | [research](research/README.md)                                                                                                     |
| Terms                                          | [glossary](glossary.md)                                                                                                            |
| Superseded narratives                          | [archive](archive/xbox-e0-history.md)                                                                                              |

## Conventions

1. **One owner per fact.** Never copy a number, status line or table from its owner; link to it.
2. **Live state only in [STATUS](STATUS.md).** A package bump or campaign start/stop edits that page alone.
3. **Current vs archive.** Superseded documents move to `archive/` with a banner naming their successor.
4. **ADRs are not rewritten** ([rules](adr/README.md)); proposals live in `adr/proposals/`.
5. **Evidence is frozen.** Only translation and dated "Later note" pointers are allowed.
6. **English** for all docs and code comments; kebab-case file names; no links outside the repository
   except to public URLs.
