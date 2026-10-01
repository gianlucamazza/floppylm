# Positioning

Owner of the comparison with prior work. Full surveys live in [`research/`](research/README.md).

| Work                         | What it does                                                          | Difference from FloppyLM                                         |
| ---------------------------- | --------------------------------------------------------------------- | ---------------------------------------------------------------- |
| Quant-Noise                  | From-scratch LM with PQ, ~1.3 bits/weight, ~0.65 per effective weight with layer sharing              | Above one bit per unique weight; no comparison with random codes |
| Sign Lock-In (ICML 2026)     | Low-rank sign templates, from-scratch char LM at ~0.5–0.7 bits/weight | Not VQ; hybrid candidate for E1b                                 |
| QTIP                         | Computed trellis codes, on par with learned codebooks on LLMs         | Post-training at ≥ 2 bits; here a favoured core arm              |
| SeedLM                       | Per-block LFSR seeds, post-training, 3–4 bits/weight                  | Here the seed codebook is an arm, from scratch and below one bit |
| AQLM / VPTQ / GPTVQ          | Post-training learned VQ at ~2 bits                                   | Codebooks too large for 11 Mbit; here a shared, counted codebook |
| BTC-LLM / GLVQ               | Learned codebooks at 0.7–1.0 bits, post-training                      | Not from scratch, not tiny                                       |
| Parameter Golf #1110 / #1113 | Recursion (1.22 bpb) beats seed + LoRA (1.37) at ~5 MB                | Reason v0.1 was closed                                           |
| VBQ (2026)                   | Larger at fewer bits beats smaller on TinyStories                     | Regime ≥ 1.8 bits/weight                                         |
| llama2.c stories260K         | Dense LM that fits on a floppy                                        | No per-byte metric; a point on the E0 frontier                   |
| Hutter Prize / cmix / NNCP   | Decompressor counted in the budget                                    | Same accounting principle                                        |

References and numbers: [R2](research/02-procedural-weights.md), [R7](research/07-learned-vq-subbit.md),
[R1](research/01-tiny-lms.md).
