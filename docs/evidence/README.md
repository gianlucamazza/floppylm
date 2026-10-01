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
| [`e0-lite/pre-v2`](e0-lite/pre-v2/notes.md)                                                                                                 | stopped E0-lite grid; diagnostic, excluded from verdicts, FLP1 blobs | —           |

### Xbox package acceptance

| Evidence                                                      | Package  | Scope                                                                                     |
| ------------------------------------------------------------- | -------- | ----------------------------------------------------------------------------------------- |
| [xbox-e0-20260930](xbox-e0-20260930/notes.md)                 | 0.1.0.11 | fixtures, optimizer, resume, first throughput, zero-row diagnostic                        |
| [xbox-e0-20260930-kernels](xbox-e0-20260930-kernels/notes.md) | 0.1.0.19 | 52 per-operation cases after kernel fixes                                                 |
| [xbox-e0-20261001](xbox-e0-20261001/notes.md)                 | 0.1.0.24 | full acceptance, worker, recovery, real suspension, data reproducibility, campaign launch |
| [xbox-e0-20261001-e01](xbox-e0-20261001-e01/notes.md)         | 0.1.0.28 | E0.1 acceptance, worker, recovery, lifecycle, throughput                                  |
| [xbox-e0-20261001-dashboard](xbox-e0-20261001-dashboard/notes.md) | 0.1.0.56 | full hardware gates, pinned deployment, bit identity, screenshot; idle attribution open |

### E1 functional qualification

[e1-qualification-20261001](e1-qualification-20261001/notes.md): CPU scalar profiling, BPE512
round trips, vector storage/reconstruction probes and deterministic partial-quantization canaries
under [ADR 0013](../adr/0013-e1-functional-qualification.md). It is neither scientific E1 nor Xbox
vector acceptance; the producing code is `scripts/e1_qualify.py` on `main`.

A dated narrative of these packages is in the [archive](../archive/xbox-e0-history.md).
Scientific E0 results are pending; the [roadmap](../roadmap.md) defines completion gates.
