# E1 1/16 pilot protocol (proposal)

## Status

Proposed — 2026-10-04. Not an ADR. Does not authorize code, a campaign, a console
job, or an F1 verdict. Roadmap gate 4 still requires a review of the completed
E0 report before any acceptance. Accepting this proposal creates the scientific
E1 ADR; this file stays as context.

## Context

The 1/16 pilot compares a vector-coded core with the scalar core at equal coded
bytes ([concept](../../concept.md), [roadmap](../../roadmap.md)). [ADR 0013](../0013-e1-functional-qualification.md)
qualified the functional oracles and did not authorize the scientific run. The
[book-budget notes](e1-1-16-book-budget.md) measured which learned books fit
inside the 1/16 ceiling. This proposal cites that table and does not repeat the
measurement.

Campaign `c58a86` is running. Its scale choice is not a finished adversary:
tuning, the grid and the paired seeds can still change width, MLP, learning
rate and which core format wins. The scalar recipe is copied from the completed
E0 selection file. It is not named here.

## Later (2026-10-05)

Scale (`row8log`) and MLP (SwiGLU, nominal `d_ff` 274) are selected. Tuning, the grid
and the paired seeds can still change learning rate, ternary delta, width, depth and
which core format wins. They do not reopen the scale or MLP choice.

E0 will not measure book size, assignment cadence, or the F1 threshold. Those
rules are fixed below so the later ADR has nothing left to invent except the
scalar recipe and the on-disk layout.

## Decision

1. **Scope.** K=1, no recursion, no trellis. Trellis remains E1b. E1a, the 1/4
   run and E2–E4 stay behind their own gates. The open 1/4 tokenizer choice is
   out of scope and does not block this pilot.
2. **Arms and seeds.** Four arms, seeds 0, 1 and 2, paired across arms: scalar
   ternary, scalar 2-bit, VQ-seed, and learned VQ with one shared book. The
   scalar width, depth, `d_ff`, MLP, scale policy, learning rate and weight
   decay are copied from the completed E0 selection for that format.
3. **Books.** A learned book at 1/16 may only be one of the rows the fit table
   marks inside the ceiling: shared G=8 at rate 0.5, shared G=8 at rate 0.75,
   or shared G=16 at rate 0.5. Per-matrix G=16 books and the 4096×16 fp16 book
   are excluded. The pilot default is shared G=8. Both roadmap rates, 0.5 and
   0.75, are trained at that G. Shared G=16 at rate 0.5 may replace G=8 only by
   an edit of the accepted ADR before the first scientific attempt, not after
   seeing validation. Alphabet size is `2 ** (G * rate)` and is not a separate
   choice. VQ-seed uses the same G and rate as the learned arm beside it and
   stores the generator seed instead of the entries.
4. **Equal coded bytes.** The target is the 1/16 serialized-byte target of the
   E0 selection. Every arm's packed file must pass ADR 0015 individual and
   reciprocal parity. Learned-book bytes are inside that file. A seed book
   contributes no entry bytes. One width repair is allowed, under the repair
   rule of the completed E0 campaign. The repair does not change G, rate, or
   the book length. An init-pack adjustment applies only when that rule is
   already accepted before the pilot starts.
5. **Tokens.** T is 20 times the stored-parameter count of the largest arm.
   Every arm sees that same token count, with cooldowns at T, 2T and 4T.
   Saturation is recorded and is not a gate.
6. **Data.** The frozen E0 TinyStories split, byte tokenizer V=256, context
   256, tied 4-bit embedding, fp16 norms. BPE is not used. Validation selects.
   The test split is opened once, after the freeze.
7. **Assignment.** One recipe, not a search: partial-quantization probability
   0.1 and assignment every 64 steps, the middle of the ADR 0013 candidate
   pairs. Only fully quantized snapshots count. Master weights are training
   state and are not a result.
8. **Dead codes.** Book length stays fixed. An entry with no assignment at a
   cadence step is reseeded from that arm's PCG32 stream, and the reseed is
   logged. Entries are not deleted and the book is not grown.
9. **Checkpoint.** Resume continues master weights, indices, the book or its
   seed, scales and optimizer moments. Re-assigning from scratch is a new run.
   The artifact at each cooldown end is the quantized container.
10. **Generator.** The ADR 0013 PCG32 recipe: sum twelve unsigned 16-bit draws,
    subtract 393210, divide by 65536, and round to fp16. A fixed book and a
    learned book start from the same seed. A fixed book stores the seed and the
    generator identity. A learned book stores its fp16 entries once.
11. **F1 and F1-abl.** F1 requires the best vector mean val bpb to be lower
    than the best scalar mean by at least `max(0.02, 2σ)`, and lower at T and
    at 2T as well. F1-abl compares learned VQ with VQ-seed at the same G and
    rate, book bytes included; the prior is that the seed arm is at least as
    good. Both comparisons use eligible validation repairs only.
12. **Freeze and test.** Freeze the selected artifact hashes, then run
    `--final-test` once. A second test is not a revision of the first.
13. **Compute.** [ADR 0004](../0004-miniature-budgets.md) still places the 1/16
    pilot on CPU. [ADR 0009](../0009-xbox-e0-backend.md) moved only E0 off that
    rule. An Xbox vector executor may replace the CPU only after it matches the
    CPU oracle on identical inputs and identical artifact bytes. A scalar
    throughput number does not qualify it. No rented GPU.
14. **Accounting.** The file that parity reads contains the header, the
    embedding, the indices, the scales, the norms, and the learned book when
    the arm has one. The seed of a fixed book is inside the header. No side
    file counts. The byte layout of that container is chosen at implementation
    time, after acceptance, and must satisfy this list.

## Left until the E0 report

- Scalar width, depth, `d_ff`, MLP, scale policy, learning rate, weight decay,
  and which format won the paired comparison.
- The selection-file hash those configs are copied from.
- Whether the single width repair is only the trained-artifact repair, or also
  an init-pack pass, if that pass has been accepted by then.

## Consequences

The text can be reviewed while E0 runs. Accepting it, merging vector training
into the model, or starting a pilot remains forbidden until gate 4. A
4096-entry G=16 book cannot be added afterwards as the 1/16 learned arm. The
six ADR 0013 snapping pairs are not a validation search.

## Alternatives

Writing nothing until E0 ends was rejected for the rules in the Decision: E0
does not measure books, cadence, or the F1 threshold. Training every allowed
G as a search was rejected because G=16 at rate 0.75 does not fit and because
choosing G after validation is a second comparison. Treating the ADR 0013
canaries as the scientific ranking was already rejected by that ADR.
