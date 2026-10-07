# Fill-aware first shape (S3 tax) — proposal

Status: accepted — 2026-10-04; recorded in ADR 0019. The running campaign does not use this rule.

## Context

The shape solver (`floppylm.shapes.grid`) fills **nominal** bits to ≥ 99.5% of the 1/16 budget (`fill_min=0.995`, default `ratio=1.0`). Eligibility is **serialized** bytes within ±1% of 85,937.5 (`parity.TOLERANCE`). S3 already measures `ratio = model_bytes * 8 / nominal_bits` on the ineligible 4T artifact and refills `d_ff` (`e0_v2.repair_shape`). That second GPU trial costs ~40–50 min per recipe.

## Measurement (CPU, 2026-10-02)

Artifacts: `runs/e0-20261002T090742Z-2fe64f-000` vs `000-repair`. Target 85,937.5 bytes.

| Artifact | d_ff | bytes | fill | coded/nominal | core B | emb B |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| original T | 391 | 84,793 | 0.9867 | 0.9871 | 66,734 | 10,799 |
| original 2T | 391 | 84,916 | 0.9881 | 0.9885 | 66,726 | 10,930 |
| original 4T | 391 | 84,800 | 0.9868 | 0.9872 | 66,732 | 10,742 |
| init (same cfg, CPU pack) | 391 | 85,052 | 0.9897 | 0.9901 | — | — |
| repair T | 400 | 85,850 | 0.9990 | 0.9870 | 67,762 | 10,774 |
| repair 2T | 400 | 85,922 | 0.9998 | 0.9878 | 67,758 | 10,850 |
| repair 4T | 400 | 86,038 | 1.0012 | 0.9892 | 67,874 | 10,850 |

The ineligible fill is stable across T/2T/4T (~1.3% short). A CPU `pack` of the **initialized** model (fill 0.9897) predicts the 4T shortfall within 0.5%. After S3, coded/nominal stays ~0.987–0.989; extra `d_ff` 9 is what crosses ±1%. The same repair hashes appear on `4236fd`, `fdab67` and `2fe64f` seed 0.

Raw JSON: [s3-fill.json](../../evidence/architecture-20261002/s3-fill.json).

## Options (not selected)

1. **CPU pack before the Xbox trial.** Initialize the solver shape, `pack_sections`, if fill is outside ±1% run `fill_d_ff(..., ratio=coded/nominal)` and submit only the repaired shape. Keeps S3 as the recorded fallback. No change to T, recipe or TinyGPT.
2. **Fixed prior `ratio≈0.987`** for ternary/row16 in `shapes.grid`. Cheaper, but format-specific; 2-bit / SwiGLU / row8log are unmeasured.
3. Leave S3 as the only adjustment (current). Honest, slow.

## Recommendation

Option 1 as a later harness change, accepted by a short ADR amendment to S3 (“at most one repair” may fire on the host before the GPU job). Do not apply it to a campaign already frozen. Do not silently change `fill_min`.

## Later (2026-10-04)

Accepted as [ADR 0019](../0019-host-init-pack.md). The 2026-10-02 measurement above is unchanged. The init pack of the neutral shapes submits `d_ff` 398 (row16) and 422 (row8log). The trained S3 repairs were 400 and 424. Campaign `c58a86` does not use the new rule.
