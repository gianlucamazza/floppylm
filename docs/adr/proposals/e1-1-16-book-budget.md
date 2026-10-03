# E1 1/16 learned-book budget — proposal notes

Status: **proposal notes** for a future scientific E1 ADR. Not an F1 verdict. Does not integrate VQ into TinyGPT.

## Context

[ADR 0013](../0013-e1-functional-qualification.md) measured a learned 4096×16 fp16 book at 131,072 bytes (1.53× the entire 1/16 model) as **book alone**. Roadmap F1 compares learned VQ (codebook counted) against ternary/2-bit at equal coded bytes. The scientific E1 ADR still has to say which books can exist at 1/16.

## Measurement (CPU, 2026-10-02)

Base: scalar 4T artifact `e0-20261002T090742Z-2fe64f-000-repair` (86,038 B, d=96 L=3 d_ff=400). Core matrices re-encoded with `VectorCodec`; hybrid estimate keeps FLP2 header, 4-bit embedding and fp16 norms from the scalar pack. Fixture container is VQF1 (not a scientific format). No training.

Target 85,937.5 bytes.

| learned | G | rate | shared book | book entry B | hybrid B | fill | within budget ceiling |
| --- | ---: | ---: | --- | ---: | ---: | ---: | --- |
| no (seed) | 8 | 0.50 | yes | 0 | 37,776 | 0.440 | yes |
| no | 8 | 0.75 | yes | 0 | 49,520 | 0.576 | yes |
| no | 16 | 0.50 | yes | 0 | 39,207 | 0.456 | yes |
| no | 16 | 0.75 | yes | 0 | 49,863 | 0.580 | yes |
| yes | 8 | 0.50 | yes | 256 | 38,032 | 0.443 | yes |
| yes | 8 | 0.50 | no (12 books) | 3,072 | 40,965 | 0.477 | yes |
| yes | 8 | 0.75 | yes | 1,024 | 50,544 | 0.588 | yes |
| yes | 8 | 0.75 | no | 12,288 | 61,732 | 0.718 | yes |
| yes | 16 | 0.50 | yes | 8,192 | 47,399 | 0.552 | yes |
| yes | 16 | 0.50 | no | 98,304 | 137,687 | 1.602 | **no** |
| yes | 16 | 0.75 | yes | 131,072 | 180,935 | 2.105 | **no** |
| yes | 16 | 0.75 | no | 1,572,864 | 1,622,903 | 18.89 | **no** |

This column checks the upper budget bound only, not scientific ±1% byte parity.

Seed/fixed books all fit with headroom (the core is smaller than ternary at 0.5–0.75 bits/weight; an equal-byte arm would grow width/depth). Learned books fit at G=8, and at G=16 r=0.5 **only if the book is shared**. The 4096-entry G=16 r=0.75 book from the ADR 0013 stress case cannot exist at 1/16 even shared.

Equal-byte F1 therefore cannot use a large learned alphabet unless the book is quantized or the budget is the 1/4. F1-abl (learned vs seed) at 1/16 is still possible on G=8 or shared G=16 r=0.5.

Raw JSON: [e1-book-fit.json](../../evidence/architecture-20261002/e1-book-fit.json).

## Recommendation

Cite this table in the scientific E1 ADR. Default learned arm at 1/16: shared book, G=8 rate 0.5 or 0.75, or G=16 rate 0.5. Exclude per-matrix G=16 r=0.75. Do not implement vector cores until E0 releases the console and that ADR is accepted.
