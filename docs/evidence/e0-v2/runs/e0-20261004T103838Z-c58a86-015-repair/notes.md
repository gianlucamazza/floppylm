# e0-20261004T103838Z-c58a86-015-repair

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/e0-20261004T103838Z-c58a86-015-repair/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 937 | 7,675,904 | 85,912 | 0.9997 | 1.4619 | `5faeda19a392` |
| 1874 | 15,351,808 | 85,778 | 0.9981 | 1.3533 | `a4744ee4c962` |
| 3748 | 30,703,616 | 85,745 | 0.9978 | 1.2792 | `e08f1f1268fb` |

- Saturation: not saturated (bpb(4T) − bpb(2T) = -0.07402687686572573).
- Individual parity ±1% of target: True.
- Estimated compute: 9.062e+13 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  5495 s at 2 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison
between arms.

## Later (2026-10-06)

Eligible at `d_ff` 288, lr 0.01, delta 0.7, seed 0. Val bpb 1.4619/1.3533/1.2792, above
the lr 0.01 delta 0.5 repair at T, 2T and 4T. Not the tuning choice.
