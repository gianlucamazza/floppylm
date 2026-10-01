# Isolated E1 functional qualification (proposal)

## Status

Accepted — 2026-10-01; recorded in [ADR 0013](../0013-e1-functional-qualification.md)
(approved as ADR 0012, renumbered because 0012 was taken concurrently). Original status:

Proposed — 2026-10-01. Requires owner acceptance before implementing the new
vector/tokenizer choices. This proposal authorizes functional qualification only;
it does not authorize scientific E1, change E0, or supersede accepted byte gates.
Per the ADR index convention, this proposal lives outside `docs/adr/`. Once
accepted, publish its decision as ADR 0012 and preserve this proposal's history.

## Context

The owner approved completion of E0–E4 with scientific gates, local Xbox/CPU
compute and no paid services. Tokenizer and scientific backend must be qualified
before selection. E0.1 is running in the original checkout with frozen sources.
The E1 worktree is separate; no source changes are merged into the E0 checkout.

At one-quarter budget the current solver admits 5 ternary/4 2-bit shapes with
V=256, versus 29/25 with V=512. This is a feasibility observation, not a quality
result. The current GPU backend supports scalar training; vector kernels have
not been implemented or qualified.

## Decision

1. Implement standalone PyTorch vector-weight oracles and a lossless byte BPE
   tokenizer in the isolated worktree. Keep them outside scientific E1 entrypoints
   until a later accepted protocol fixes model integration, format and run recipes.
2. Qualify group dimensions 8 and 16 at 0.5 and 0.75 index bits per weight. Alphabet
   size is exactly `2 ** (dimension * rate)`: 16/64/256/4096. Groups are contiguous
   within rows, padded with zeros at the row tail; count padded indices explicitly.
3. Generated and learned books start from the same PCG32 seed and pseudo-Gaussian
   values: sum twelve unsigned 16-bit draws, subtract 393210, divide by 65536,
   then round to fp16. This avoids platform-specific transcendental generators.
   A fixed book stores its seed and generator identity; a learned book stores its
   fp16 entries once per shared book, never once per matrix or layer.
4. Each row uses RMS scale, serialized through existing row16 or row8log scale
   semantics. Zero rows reconstruct to exact zero. Assignment uses squared
   Euclidean distance with bounded chunks and lowest index on a tie. Reject
   non-finite weights, invalid shapes/indices and malformed book/scale payloads.
5. Test partial quantization and periodic snapping as functional candidates:
   probability {0.05, 0.1} times cadence {16, 64, 256}, six recipes for each arm.
   Fully quantized artifact evaluation is mandatory; a master-weight result cannot
   stand in for the deployed model. No scientific ranking comes from tiny canaries.
6. Lossless BPE begins with all 256 bytes and adds up to 256 merges. Pretokenize
   into ASCII letter runs, digit runs, whitespace runs and other-byte runs, with
   0x03 as its own protected boundary. No normalization or unknown-token replacement.
   Learn from the first 2 MiB of the frozen train split only. Count all merge-table
   and configuration bytes. Highest pair frequency wins; ties use ascending token
   IDs. Python encode/decode and serialization must round-trip arbitrary bytes.
7. Functional data, synthetic probes and feasibility reports are labelled
   `purpose: functional`. Bind every report to source and input hashes. Do not
   open test, perform validation-driven scientific selection or submit Xbox jobs
   while E0 owns the console. Neither an infeasible book nor an operational error
   is an F1/F2 scientific verdict.
8. Qualification evidence includes exact storage components, reconstruction,
   gradient checks against independent explicit calculations, deterministic
   seeded generation, malformed-input rejection and bounded-memory assignment.
   A learned 4096x16 fp16 book is 131072 bytes: reject it at 1/16 rather than hiding
   its cost. Candidate feasibility includes scales and metadata, not index rate alone.

## Consequences

These oracles make codec/tokenizer design concrete and falsifiable without
altering the active campaign or inventing GPU vector performance. The later E1
scientific ADR must fix shape/tuning budgets, context fairness, serialized model
format, backend acceptance and final-test reservation before scientific runs.
Shared-book identity, dead-code reseeding and assignment state must be explicit
in that later training/checkpoint contract; this ADR does not guess it.

## Alternatives

Immediate scientific E1 would leave critical choices unregistered. Selecting BPE
from shape count alone does not establish quality. Selecting Xbox from scalar
throughput alone does not establish vector throughput. Rewriting the active
checkout would invalidate E0's source freeze. These alternatives are rejected.
