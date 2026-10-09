# JSON open diagnosis — 0.1.0.109

Purpose: **functional**. No scientific campaign was resumed onto this package.
Historical campaigns keep their original package and source bindings.
Campaign `e0-20261009T150330Z-87686a` stays stopped on `0.1.0.105`.
Campaign `e0-20261007T164712Z-766d4b` stays stopped. Cell `031` is not a result.

## Package and scope

The installed Release package is `GianlucaMazza.XgpuE0_0.1.0.109_x64__g0p5dcfz4t9z4`, built by
CI [37959310043](https://github.com/gianlucamazza/xbox-gpu-training/actions/runs/37959310043)
from squash `961ccc2ab2e800eb25ea1ea33c1af1a46389ee59`
([PR #44](https://github.com/gianlucamazza/xbox-gpu-training/pull/44), PR head `4275ebf`).
[Lineage](package-lineage.json) binds the unsigned and signed package hashes and the
preserved CI payloads. Signing used the existing development certificate. Deployment
used the TLS pin already published for 0.1.0.105. That pin matched; it was not
replaced. No uninstall was required: the install replaced 0.1.0.105 in place and
kept LocalState. The start command succeeded.

This package names the path and the Win32 code when a JSON body cannot be opened.
It retries only sharing violation (32) and lock violation (33), forty times at
50 ms. A full volume is not retried. Schemas, checkpoints and the training budget
are unchanged. The parked-probe classification is unchanged: a frozen published
fence with no in-flight GPU request is still `progress_stall`.

The first acceptance attempt failed while uploading the kernel fixture. Device
Portal returned HTTP 500. The writable remainder on the console was exhausted.
Published functional result directories already copied into evidence were removed.
Scientific `e0-` trees and the corpus stayed. The recorded acceptance is the
exclusive rerun. The first lifecycle attempt called Device Portal to launch Dev
Home while that process was already listed and received HTTP 400
(`0x8027025A`). The script stopped before the comparison. That directory is not
the proof. The recorded lifecycle is the rerun, started after Dev Home was absent
from the process list.

## Measured hardware gates

- [Acceptance](acceptance.json): 36 fixtures, 52 independent GPU operation cases
  ([kernel proof](kernel-parity.json)), AdamW and exact resume passed.
- [Watchdog](watchdog.json): the parked probe published checkpoint step 2, the
  ordinary heartbeat advanced, and the process exited after 600.262 seconds.
  The [fault](watchdog-fault.json) is `progress_stall`, requested fence 0, elapsed
  600005 ms, error “published progress frozen without an in-flight GPU request”.
  [Process exit](process-exit.json) and [runtime events](runtime-events.jsonl)
  record that observation. Exact recovery of the control matched.
- One explicit restart produced a [new idle worker](worker-after-restart.json).
- [Worker guards](worker.json) passed (`fixed` true, `baseline_broken` false).
- [Recovery](recovery.json): the interrupted runner returned 130 with summary
  `interrupted`, resume completed, and a second resume left the summary unchanged.
  Branch and checkpoint recovery of the interrupted job matched the full job.
- [Lifecycle](lifecycle.json): suspension interrupted at trunk step 80 on
  adapter `SraKmd_arden` and recovered exactly. The completed run finished at
  trunk step 1844.
- [Bit identity](bit-identity.json) versus accepted 0.1.0.105: 38/38 canonical
  acceptance payloads, six raw branch files, two numerical checkpoint states,
  three benchmark branch hashes and the shader CSO agree. Shader SHA-256 is
  `a6e6c2f641b6a1362e69c06d92f4faf2ae86b41baea9a681a86655ac994ca50f`.
  Only declared execution telemetry is excluded. Reference
  [lineage](reference-105/package-lineage.json) and
  [benchmark](reference-105/throughput.json) are byte-preserved copies of the
  0.1.0.105 record. Benchmark last loss is 0.5518537215078254 on both packages.
- [Synthetic benchmark](throughput.json): 9728.311 token/s; peak app memory
  125718528 bytes. This is functional throughput, not a quality result and not
  a controlled performance claim.
- [Preservation](preservation.json): the pre-existing inbox inventory hash was
  unchanged. Archived payload bytes were not rehashed. After these gates the
  worker was idle: state ready, no active job, fault null, source prefix
  `961ccc2ab2e8`.

No dashboard image was captured for this package.

These gates do not establish that the scientific `JSON write failed` stop is gone.
They do not authorize resuming `87686a`, `766d4b` cell `031`, or any earlier
campaign. A failed open on this package must be read from the Win32 code.

## Reproduction and raw evidence

Raw run directories, relative to the repository:

- `runs/xbox-acceptance-20261009-ci37959310043/` (failed upload, not the proof)
- `runs/xbox-acceptance-20261009-ci37959310043-r2/`
- `runs/xbox-watchdog-20261009-ci37959310043/`
- `runs/xbox-worker-20261009-ci37959310043/`
- `runs/xbox-recovery-20261009-ci37959310043/`
- `runs/xbox-lifecycle-20261009-ci37959310043/` (Dev Home launch HTTP 400, not the proof)
- `runs/xbox-lifecycle-20261009-ci37959310043-r2/`
- `runs/xbox-benchmark-20261009-ci37959310043/`
- `runs/xbox-bit-identity-20261009-ci37959310043.json`

Run acceptance, then the watchdog harness with that acceptance, then worker,
recovery, lifecycle and benchmark. The bit-identity report compares this
acceptance and benchmark with `runs/xbox-acceptance-20261004-ci37194378620/`
and `runs/xbox-benchmark-20261004-ci37194378620/`.
