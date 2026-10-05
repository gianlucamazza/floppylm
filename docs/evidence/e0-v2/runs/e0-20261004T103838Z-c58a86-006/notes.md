# e0-20261004T103838Z-c58a86-006

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261004T103838Z-c58a86-006/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 907 | 7,430,144 | 84,879 | 0.9877 | 1.4661 | `049a9a9ccc97` |
| 1814 | 14,860,288 | 85,021 | 0.9893 | 1.3433 | `f083ebe45860` |
| 3628 | 29,720,576 | 84,821 | 0.9870 | 1.2616 | `acc5a4134730` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.08165509029727258).
- Individual parity ±1% of target: False.
- Estimated compute: 8.540e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  4703 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-05)

Outside ±1% at nominal `d_ff` 274. The eligible number is the S3 repair at `d_ff` 280.
This original is not an activation result.
