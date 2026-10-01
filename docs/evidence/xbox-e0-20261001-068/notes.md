# Dashboard package acceptance — 0.1.0.68 — 2026-10-01

Purpose: **functional**. This record does not certify language-model quality or restart a scientific campaign.

## Artifact and deployment

CI [36925453940](https://github.com/gianlucamazza/xbox-gpu-training/actions/runs/36925453940)
built source `3cc47d2edb7c949a3b0e6b1fe9fb1d3ba9fdc0e5` ([PR 31](https://github.com/gianlucamazza/xbox-gpu-training/pull/31) dashboard).
The installed package is `GianlucaMazza.XgpuE0_0.1.0.68_x64__g0p5dcfz4t9z4`.
[package-lineage.json](package-lineage.json) records unsigned and signed SHA-256, preserved CI payloads, the existing development signing certificate and the pinned Device Portal TLS certificate.
Shader `Assets/e0_tensor.cso` matches 0.1.0.56. The GPU fence is still `WaitForSingleObjectEx(..., INFINITE)`.

[openappx.json](openappx.json) and [tls-pin.json](tls-pin.json) are the same environment proofs as the 0.1.0.56 record.

## Hardware gates

- [kernel-parity.json](kernel-parity.json): 52 GPU operation cases passed.
- [acceptance.json](acceptance.json): 36 fixtures, AdamW and exact resume passed.
- [worker.json](worker.json): wrong identity and oversized dispatch rejected; worker reused.
- [runner-recovery.json](runner-recovery.json): exact interrupted recovery and completed-job idempotence passed.
- [lifecycle.json](lifecycle.json): real Dev Home suspension at trunk step 1337 (`suspend` marker); producer reported `lifecycle_exact` and completed trunk 1844.
- [throughput.json](throughput.json): 10139.187 token/s, peak app memory 117567488 bytes, synthetic corpus (same recipe as 0.1.0.56).
- [bit-identity.json](bit-identity.json): identical numerical payloads for 38/38 acceptance cases versus 0.1.0.56; six raw branch files, two numerical checkpoint states, three benchmark artifact hashes and the shader hash agree. Canonical JSON excludes only declared execution telemetry.

[dashboard.png](dashboard.png) shows the accepted package/source on the console after the gates. Its rolling UI throughput is not the whole-run benchmark average.

No extra `--steps 700` bench is part of this record. The same INFINITE-fence hang (CPU 0, empty `checkpoint.json.tmp`) was observed on 0.1.0.56 and 0.1.0.66 during long runs; it is not a dashboard-layout regression.

Idle GPU attribution remains open on the 0.1.0.56 record. Fence-timeout recovery remains [PR 30](https://github.com/gianlucamazza/xbox-gpu-training/pull/30), uninstalled.

## Reproduction

Raw inputs remain under `runs/xbox-{acceptance,benchmark,worker,recovery,lifecycle}-20261001-ci36925453940`.
The reference 0.1.0.56 dirs use suffix `ci36885338811`.
`scripts/verify_e0_bit_identity.py` in xbox-gpu-training produced [bit-identity.json](bit-identity.json).

Campaign `e0-20261001T163456Z-fdab67` stays bound to 0.1.0.56 and was not resumed.
