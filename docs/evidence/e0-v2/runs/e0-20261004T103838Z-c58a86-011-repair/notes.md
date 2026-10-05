# e0-20261004T103838Z-c58a86-011-repair

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261004T103838Z-c58a86-011-repair/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 937 | 7,675,904 | 85,820 | 0.9986 | 1.5771 | `cd2fd2230b1b` |
| 1874 | 15,351,808 | 85,932 | 0.9999 | 1.4326 | `870cb56208fd` |
| 3748 | 30,703,616 | 85,831 | 0.9988 | 1.3301 | `03ada12ca182` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.10254528841373123).
- Individual parity ±1% of target: True.
- Estimated compute: 9.062e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  5481 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-05)

Eligible at `d_ff` 288, lr 0.001, delta 0.7, seed 0. Val bpb 1.5771/1.4326/1.3301, above
the neutral SwiGLU seed 0 repair at T, 2T and 4T. Not a tuning decision.
