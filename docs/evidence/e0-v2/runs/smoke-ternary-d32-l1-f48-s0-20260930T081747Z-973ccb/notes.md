# smoke-ternary-d32-l1-f48-s0-20260930T081747Z-973ccb

**Smoke: functional test, not a scientific result.**

Status: **completed**. Full configuration and environment in `summary.json`; manifest in
`runs/smoke-ternary-d32-l1-f48-s0-20260930T081747Z-973ccb/manifest.json`.

| Cooldown end (step) | Tokens seen | Bytes | Fill | val bpb | sha256 |
| --- | --- | --- | --- | --- | --- |
| 16 | 8,192 | 6,519 | 0.0759 | 5.1353 | `47a8226becb1` |
| 32 | 16,384 | 6,515 | 0.0758 | 4.3818 | `587aa5d21f81` |

- Saturation: not determined (fewer than 3 cooldowns) (bpb(4T) − bpb(2T) = None).
- Individual parity ±1% on target: False.
- Estimated compute: 1.765e+09 FLOP (3 * (2 * stored_params + 4 * n_layers * (ctx / 2) * d) * tokens), wall
  3 s at 4 threads.

Not measured here: test (only `--final-test` on a frozen selection), paired σ, comparison between
arms.

Later note (2026-10-01): this generated page was translated by hand; `summary.json` and the
`notes_md` template in `experiments/e0_v2.py` remain in Italian until the frozen E0 sources are released.
