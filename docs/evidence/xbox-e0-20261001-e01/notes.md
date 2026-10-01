# Series S E0.1 acceptance (2026-10-01)

Installed package `GianlucaMazza.XgpuE0_0.1.0.28_x64__g0p5dcfz4t9z4` (E0.1, GPU-resident
tensors), exact source `25f8bc3966ffae940658be94161d31edd83492c9`, push CI run
[36839565773](https://github.com/gianlucamazza/xbox-gpu-training/actions/runs/36839565773)
(xbox-gpu-training PR #18). Adapter `SraKmd_arden`, hardware GPU. All files here are
copies of the local proofs under `runs/*-20261001-ci36839565773/`
(`throughput.json` is the benchmark's `summary.json`).

- `acceptance.json`: 52 independent GPU operation cases, 36 held-out model fixtures,
  identical-input AdamW and exact checkpoint resume passed.
- `worker.json`: wrong job identity and oversized dispatch are rejected; subsequent valid
  GPU work succeeds.
- `recovery.json`: interrupted recovery is exact; completed retrieval leaves results
  unchanged; runner resume of completed work is idempotent.
- `lifecycle.json`: a real `suspend` marker produced a verified checkpoint at trunk step 461.
- `throughput.json`: representative d=96/layers=3/d_ff=391/ctx=256/batch=32 synthetic
  benchmark, 147456 tokens in 14.422 s wall (11.851 GPU s), 10224.282 token/s, peak app
  memory 110366720 bytes.

Bit identity with 0.1.0.24 (every acceptance case, trained weight and benchmark artifact)
is recorded in the backend repository's
[e0-20261001-resident evidence](https://github.com/gianlucamazza/xbox-gpu-training/tree/main/docs/evidence/e0-20261001-resident),
not re-measured here. The previous package evidence is
[xbox-e0-20261001](../xbox-e0-20261001/notes.md).

This certifies functional execution and throughput on synthetic data, not language-model
quality. Campaign `e0-20261001T090514Z-4236fd` binds these acceptance and benchmark files.
