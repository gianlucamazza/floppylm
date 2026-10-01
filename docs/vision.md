# Vision

## Mission

The best language model that fits on a real 3.5" floppy, measured as quality per byte, and the
measured answer to an open question: below one bit, from scratch, does a vector code in the core
beat ternary — and must the code be learned, or is generating it enough?

## Success v0.1

- E0–E2 **measured**, with F1 and F2 decided one way or the other.
- If the thesis holds: E4 produces an image within the [ADR 0001](adr/0001-floppy-budget.md)
  budget that generates coherent TinyStories stories.
- If it does not: the bpb-per-byte frontier under 1.5 MB (scalar vs vector, with and without
  recursion) is publishable anyway.

## Non-goals

- Factual knowledge, chat, instructions.
- A bootable floppy: a data floppy executed by a Linux host ([ADR 0001](adr/0001-floppy-budget.md)).
- Beating models outside the budget; SmolLM2 is only a scale reference.
