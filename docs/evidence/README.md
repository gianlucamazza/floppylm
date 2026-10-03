# Evidence

This directory owns the **numbers**. A claim that something "works" without a file here is theatre.
Records are frozen: they may only be translated or receive a dated "Later note" pointer at the end.
Host-absolute paths inside records are normalized to repository-relative paths.

## Layout

```
evidence/e0-v2/runs/<run_id>/
  summary.json     # state, config, bytes and hashes per cooldown, val bpb, saturation, compute
  notes.md         # one generated page: setup, results, what was not measured
evidence/e0-v2/campaigns/<campaign_id>/      # generated campaign report (summary.json, notes.md)
evidence/e0-v2/selections/<name>.json        # frozen selection with artifact hashes
evidence/e0-v2/selections/<name>.test.json   # final test, once per selection
evidence/xbox-e0-YYYYMMDD[-tag]/             # hand-written package acceptance: notes.md + JSON proofs
evidence/e0-lite/pre-v2/                     # stopped pre-v2 grid, diagnostic only
evidence/e1-qualification-YYYYMMDD/          # E1 functional qualification (ADR 0013), not scientific E1
```

The full manifest, state and artifacts of each run live in `runs/<run_id>/` (outside Git; only
`/runs/` at the root is ignored). Historical `smoke-functional*.json` selections predate ADR 0007
and remain unchanged. New selections declare `purpose: scientific | functional`; smoke runs require
`--freeze ... --functional` and cannot certify a scientific baseline. Run summaries stay partial
until host retrieval and evaluation complete.

[Historical report corrections](e0-report-corrections-20261003/notes.md) distinguish
attempt recipes/eligibility from trial outcomes without overwriting frozen records.

## Inventory

### E0 v2 runs and campaigns

| Evidence                                                                                                                                    | Kind                                                                 | State       |
| ------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- | ----------- |
| [`e0-v2/runs/smoke-ternary-d32-l1-f48-s0-20260930T081747Z-973ccb`](e0-v2/runs/smoke-ternary-d32-l1-f48-s0-20260930T081747Z-973ccb/notes.md) | smoke, **functional proof, not scientific**                          | completed   |
| `e0-v2/runs/smoke-ternary-d32-l1-f48-s0-20260930T081826Z-e393da`                                                                            | SIGTERM path test, smoke interrupted on purpose                      | interrupted |
| `e0-v2/selections/smoke-functional*.json`                                                                                                   | functional proof of `--freeze` / `--final-test` on smoke             | —           |
| [`e0-v2/campaigns/e0-20261001T074326Z-503df0`](e0-v2/campaigns/e0-20261001T074326Z-503df0/notes.md)                                         | first scientific campaign, package 0.1.0.24                          | stopped     |
| [`e0-v2/campaigns/e0-20261001T090514Z-4236fd`](e0-v2/campaigns/e0-20261001T090514Z-4236fd/notes.md) | E0.1 campaign, package 0.1.0.28; stopped at `neutral-scale` (saturation) | stopped |
| `e0-v2/runs/e0-20261001T074326Z-503df0-000`                                                                                                 | its only trial, checkpointed at trunk step 455                       | stopped     |
| [`e0-v2/runs/e0-20261001T090514Z-4236fd-000`](e0-v2/runs/e0-20261001T090514Z-4236fd-000/notes.md) | campaign `4236fd` trial 0 (row16, seed 0): bytes −1.3%, not saturated | excluded |
| [`e0-v2/runs/e0-20261001T090514Z-4236fd-000-repair`](e0-v2/runs/e0-20261001T090514Z-4236fd-000-repair/notes.md) | its S3 byte repair: byte parity met, Δ(2T→4T) = −0.079, not saturated | excluded |
| [`e0-v2/runs/e0-20261001T090514Z-4236fd-001`](e0-v2/runs/e0-20261001T090514Z-4236fd-001/notes.md) | trial 001 (row16, seed 1): bytes −1.3%, Δ(2T→4T) = −0.085, not saturated | completed |
| `e0-v2/runs/e0-20261001T090514Z-4236fd-001-repair` | its byte repair, stopped with the campaign at trunk step 162 | interrupted |
| [`e0-v2/runs/e0-20261001T163456Z-fdab67-000`](e0-v2/runs/e0-20261001T163456Z-fdab67-000/notes.md) | `fdab67` on 0.1.0.56, row16 seed 0: bytes short, not saturated. No campaign report was written | excluded |
| [`e0-v2/runs/e0-20261001T163456Z-fdab67-000-repair`](e0-v2/runs/e0-20261001T163456Z-fdab67-000-repair/notes.md) | its S3 repair: parity met, val bpb 1.5155/1.3951/1.3160, Δ(2T→4T) = −0.079 | eligible |
| `e0-v2/runs/e0-20261001T163456Z-fdab67-001` | seed 1 interrupted before a cooldown | interrupted |
| [`e0-v2/campaigns/e0-20261002T072408Z-40a67c`](e0-v2/campaigns/e0-20261002T072408Z-40a67c/notes.md) | campaign on 0.1.0.80; trial 000 interrupted before a cooldown | stopped |
| `e0-v2/runs/e0-20261002T072408Z-40a67c-000` | that trial: Xbox job interrupted, not a result | failed |
| [`e0-v2/campaigns/e0-20261002T090742Z-2fe64f`](e0-v2/campaigns/e0-20261002T090742Z-2fe64f/notes.md) | campaign on 0.1.0.86; seed 0 repair eligible, seed 1 interrupted | stopped |
| [`e0-v2/runs/e0-20261002T090742Z-2fe64f-000`](e0-v2/runs/e0-20261002T090742Z-2fe64f-000/notes.md) | row16 seed 0: bytes short, not saturated | excluded |
| [`e0-v2/runs/e0-20261002T090742Z-2fe64f-000-repair`](e0-v2/runs/e0-20261002T090742Z-2fe64f-000-repair/notes.md) | S3 repair, same artifacts as `fdab67-000-repair`, Δ(2T→4T) = −0.079 | eligible |
| `e0-v2/runs/e0-20261002T090742Z-2fe64f-001` | seed 1 interrupted before a cooldown; do not recover | interrupted |
| [`e0-v2/campaigns/e0-20261002T191632Z-ca781f`](e0-v2/campaigns/e0-20261002T191632Z-ca781f/notes.md) | campaign on 0.1.0.93; both row16 seeds eligible; trial 002 interrupted | stopped |
| [`e0-v2/runs/e0-20261002T191632Z-ca781f-000`](e0-v2/runs/e0-20261002T191632Z-ca781f-000/notes.md) | row16 seed 0: bytes short, val bpb 1.5148/1.3938/1.3120 | excluded |
| [`e0-v2/runs/e0-20261002T191632Z-ca781f-000-repair`](e0-v2/runs/e0-20261002T191632Z-ca781f-000-repair/notes.md) | S3 repair, same artifacts as `fdab67-000-repair`, eligible | eligible |
| [`e0-v2/runs/e0-20261002T191632Z-ca781f-001`](e0-v2/runs/e0-20261002T191632Z-ca781f-001/notes.md) | row16 seed 1: bytes short, val bpb 1.5273/1.4052/1.3204 | excluded |
| [`e0-v2/runs/e0-20261002T191632Z-ca781f-001-repair`](e0-v2/runs/e0-20261002T191632Z-ca781f-001-repair/notes.md) | S3 repair eligible, val bpb 1.5100/1.3916/1.3082, Δ(2T→4T) = −0.083 | eligible |
| `e0-v2/runs/e0-20261002T191632Z-ca781f-002` | `row8log` `d_ff` 415, interrupted at the start, not a result | interrupted |
| [`e0-lite/pre-v2`](e0-lite/pre-v2/notes.md)                                                                                                 | stopped E0-lite grid; diagnostic, excluded from verdicts, FLP1 blobs | —           |

### Xbox package acceptance

| Evidence                                                      | Package  | Scope                                                                                     |
| ------------------------------------------------------------- | -------- | ----------------------------------------------------------------------------------------- |
| [xbox-e0-20260930](xbox-e0-20260930/notes.md)                 | 0.1.0.11 | fixtures, optimizer, resume, first throughput, zero-row diagnostic                        |
| [xbox-e0-20260930-kernels](xbox-e0-20260930-kernels/notes.md) | 0.1.0.19 | 52 per-operation cases after kernel fixes                                                 |
| [xbox-e0-20261001](xbox-e0-20261001/notes.md)                 | 0.1.0.24 | full acceptance, worker, recovery, real suspension, data reproducibility, campaign launch |
| [xbox-e0-20261001-e01](xbox-e0-20261001-e01/notes.md)         | 0.1.0.28 | E0.1 acceptance, worker, recovery, lifecycle, throughput                                  |
| [xbox-e0-20261001-dashboard](xbox-e0-20261001-dashboard/notes.md) | 0.1.0.56 | full hardware gates, pinned deployment, bit identity, screenshot; idle attribution open |
| [xbox-e0-20261001-068](xbox-e0-20261001-068/notes.md) | 0.1.0.68 | PR 31 dashboard; full hardware gates, bit-identical to 0.1.0.56; fence still INFINITE |
| [xbox-e0-20261002-080](xbox-e0-20261002-080/notes.md) | 0.1.0.80 | PR 32 liveness + PR 30 fence-timeout; full hardware gates, bit-identical to 0.1.0.56/0.1.0.68 |
| [xbox-e0-20261002-086](xbox-e0-20261002-086/notes.md) | 0.1.0.86 | PR 34 drop EE + PR 33 DisplayRequest; full hardware gates including lifecycle; bit-identical to 0.1.0.56/0.1.0.68/0.1.0.80 |
| [xbox-e0-20261002-093](xbox-e0-20261002-093/notes.md) | 0.1.0.93 | PR 37 fence poll wait + PR 35 `loss_series`; full hardware gates; bit-identical 38/38 vs 0.1.0.56/0.1.0.68/0.1.0.80/0.1.0.86 |
| [xbox-e0-20261003-095](xbox-e0-20261003-095/notes.md) | 0.1.0.95 | PR 38 published-fence watchdog; full hardware gates; bit-identical 38/38 vs 0.1.0.56/0.1.0.68/0.1.0.80/0.1.0.86/0.1.0.93 |
| [architecture-20261002](architecture-20261002/) | CPU | S3 coded/nominal fill on `2fe64f-000` vs repair; E1 1/16 VQ book-fit table. Proposals, not ADRs. |

### E1 functional qualification

[e1-qualification-20261001](e1-qualification-20261001/notes.md): CPU scalar profiling, BPE512
round trips, vector storage/reconstruction probes and deterministic partial-quantization canaries
under [ADR 0013](../adr/0013-e1-functional-qualification.md). It is neither scientific E1 nor Xbox
vector acceptance; the producing code is `scripts/e1_qualify.py` on `main`.

A dated narrative of these packages is in the [archive](../archive/xbox-e0-history.md).
`ca781f` is the first row16 pair with both seeds eligible under ADR 0015. The rest of the E0
grid, paired σ and the held-out test remain open; the [roadmap](../roadmap.md) defines those gates.
