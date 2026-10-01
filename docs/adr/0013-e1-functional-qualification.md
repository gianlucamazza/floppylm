# ADR 0013: Isolated E1 functional qualification

## Status

Accepted — 2026-10-01. The owner explicitly approved the qualification proposal.
The accepted decision is the eight-point Decision section and its Consequences
in [the preserved proposal](../e1-qualification-proposal.md).

Administrative numbering: the owner approved the proposal as ADR 0012. Concurrent
main commit `8b76068` assigned 0012 to repository boundaries, so this isolated
record uses 0013. The approved decision is unchanged.

## Context

E0.1 runs in a separate frozen checkout. The owner selected controlled qualification
before choosing E1 tokenizer/backend, local CPU/Xbox compute, and local evaluation.
The proposal records candidate dimensions, rates, generator, scale semantics,
assignment, partial-quantization recipes and train-only byte BPE.

## Decision

Implement the functional oracles, storage accounting and canaries described in the
proposal, isolated from the active E0 checkout. Do not launch scientific E1 or
merge changes into the frozen E0 source set. Freeze functional inputs/sources and
identify incomplete or infeasible candidates explicitly.

## Consequences

Qualification can proceed now. Scientific model integration, persistent training
state, tokenizer/context fairness, model format and backend selection require a
later evidence-backed accepted protocol. E0 numerical/byte gates are unchanged.

## Alternatives

Immediate scientific E1, selecting tokenizer by nominal shape count, or selecting
vector backend by scalar throughput alone were rejected. See the full proposal.
