# e0-20261007T164712Z-766d4b-027

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261007T164712Z-766d4b-027/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 762 | 6,242,304 | 85,561 | 0.9956 | 1.4914 | `fd8ab04af30d` |
| 1524 | 12,484,608 | 85,541 | 0.9954 | 1.3663 | `c5548ea22fe3` |
| 3048 | 24,969,216 | 85,597 | 0.9960 | 1.2766 | `940c5ba710a8` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.08975112204687141).
- Individual parity ±1% of target: True.
- Host init pack: 83,274 B, fill 0.9690, ratio 0.970017; submitted d_ff 205.
- Estimated compute: 6.216e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  3444 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-09)

Eligible on the first pack under ADR 0019 and ADR 0020. The 2-bit grid
comparison is byte-comparable and rank-stable at T, 2T and 4T. This cell is
the stored 2-bit phase selection. The decision records nominal `d_ff` 193; this
cell submitted `d_ff` 205. The three cooldown artifacts match tuning cell
`016`. Not the scalar recipe.
