# Surveys — contract

Each `0N-*.md` file answers **one** question. It is not a bibliography.

## Required sections

1. **Question** — one, in one sentence.
2. **What exists** — 2024–2026 citations plus load-bearing earlier work. Each paper is read at least
   in abstract + central claim. No decorative lists.
3. **What is missing** — the gap, with the counter-example searched for declared.
4. **Implication for the thesis** — which principle P\*, which knob, which falsifier F\* it touches
   ([concept](../concept.md)).
5. **Minimum experiment** — the experiment that attacks the gap, usually an E\* of the
   [roadmap](../roadmap.md).

## Rules

- No "literature gap" claim without having searched for a counter-example.
- Never promote a paper to design. Design lives in [`concept.md`](../concept.md) and the
  [ADRs](../adr/README.md).
- Declare the survey date at the top, and change it when the survey is updated.
- The [roadmap](../roadmap.md) governs E0–E4. A survey's "Minimum experiment" is background, not a
  definition; where they disagree, the roadmap wins.

## Index

Thesis = the [concept](../concept.md) version the survey was framed for. Surveys framed for v0.1
(one or more of: procedural seed weights, 0.5/1.0/1.44 MB budgets, CPU-only E0) carry a banner at the top.

| Survey                                                     | Thesis | Question                                                                                                             |
| ---------------------------------------------------------- | ------ | -------------------------------------------------------------------------------------------------------------------- |
| [01-tiny-lms.md](01-tiny-lms.md)                           | v0.1   | What can the best dense LM ≤10M params do, and how many bytes does it cost?                                          |
| [02-procedural-weights.md](02-procedural-weights.md)       | v0.1   | Is there already a from-scratch LM with a ≤1.44 MB description exploiting rest vs RAM? (decides F0)                  |
| [03-mdl-compression.md](03-mdl-compression.md)             | v0.1   | How many bits does an LM cost, and does rate-aware training move the frontier?                                       |
| [04-runtime-and-demoscene.md](04-runtime-and-demoscene.md) | v0.1   | How many bytes does the runtime eat, and what does the demoscene teach?                                              |
| [05-eval-tiny.md](05-eval-tiny.md)                         | v0.1   | How do we compare tiny models at equal bytes without tricks?                                                         |
| [06-hardware-budget.md](06-hardware-budget.md)             | v0.1   | What can be trained and expanded in useful time on this laptop?                                                      |
| [07-learned-vq-subbit.md](07-learned-vq-subbit.md)         | v0.2   | Is there a from-scratch LM with learned-codebook VQ below 1 bit/weight? Learned vs seed vs ternary (decides F0 v0.2) |
