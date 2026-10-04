# Checkpoint-publish qualification — 0.1.0.105

Purpose: **functional**. No scientific campaign was resumed onto this package.
Historical campaigns keep their original package and source bindings.
Campaign `e0-20261004T082243Z-31972d` stays stopped on `0.1.0.102`.

## Package and scope

The installed Release package is `GianlucaMazza.XgpuE0_0.1.0.105_x64__g0p5dcfz4t9z4`, built by
CI [37194378620](https://github.com/gianlucamazza/xbox-gpu-training/actions/runs/37194378620)
from squash `128434e81837ec1558f7e3d68a7f8849a91aa054`
([PR #41](https://github.com/gianlucamazza/xbox-gpu-training/pull/41), PR head `b9d8145`).
[Lineage](package-lineage.json) binds the unsigned and signed package hashes and the
preserved CI payloads. Signing used the existing development certificate. Deployment
used the existing Odroid SSH tunnel and the TLS pin already published for 0.1.0.98.
That pin matched; it was not replaced. No uninstall was required: the install replaced
0.1.0.102 in place and kept LocalState. The start command succeeded.

This package changes checkpoint publication. The body is serialized before any file
is opened. A large publish records a one-line phase (`dumping`, then `writing`,
then `replacing`) and writes a unique partial, not a stable `checkpoint.json.tmp`.
The UWP build uses `CreateFileFromAppW`. The parked-probe classification is
unchanged: a frozen published fence with no in-flight GPU request is still
`progress_stall`.

The host step-2112 checkpoint of `31972d` was copied and hashed before the stop.
It is a preserved artifact, not an input to these gates and not a resume source.

## Measured hardware gates

- [Acceptance](acceptance.json): 36 fixtures, 52 independent GPU operation cases
  ([kernel proof](kernel-parity.json)), AdamW and exact resume passed.
- [Watchdog](watchdog.json): the parked probe published checkpoint step 2, the
  ordinary heartbeat advanced, and the process exited after 601.855 seconds.
  The [fault](watchdog-fault.json) is `progress_stall`, requested fence 0, elapsed
  600988 ms, error “published progress frozen without an in-flight GPU request”.
  [Process exit](process-exit.json) and [runtime events](runtime-events.jsonl)
  record that observation. Exact recovery of the control matched.
- One explicit restart produced a [new idle worker](worker-after-restart.json).
- [Worker guards](worker.json) passed (`fixed` true, `baseline_broken` false).
- [Recovery](recovery.json): the interrupted runner returned 130 with summary
  `interrupted`, resume completed, and a second resume left the summary unchanged.
  Branch and checkpoint recovery of the interrupted job matched the full job.
  This directory is the proof; there was no earlier failed pass on this package.
- [Lifecycle](lifecycle.json): suspension interrupted at trunk step 109 on
  adapter `SraKmd_arden` and recovered exactly. The completed run finished at
  trunk step 1844.
- [Bit identity](bit-identity.json) versus accepted 0.1.0.102: 38/38 canonical
  acceptance payloads, six raw branch files, two numerical checkpoint states,
  three benchmark branch hashes and the shader CSO agree. Shader SHA-256 is
  `a6e6c2f641b6a1362e69c06d92f4faf2ae86b41baea9a681a86655ac994ca50f`.
  Only declared execution telemetry is excluded. Reference
  [lineage](reference-102/package-lineage.json) and
  [benchmark](reference-102/throughput.json) are byte-preserved copies of the
  0.1.0.102 record. Benchmark last loss is 0.5518537215078254 on both packages.
- [Synthetic benchmark](throughput.json): 9679.418 token/s; peak app memory
  126918656 bytes. This is functional throughput, not a quality result and not
  a controlled performance claim.
- [Preservation](preservation.json): the pre-existing inbox inventory hash was
  unchanged. Archived payload bytes were not rehashed. After these gates the
  worker was idle: state ready, no active job, fault null, source prefix
  `128434e81837`.

No dashboard image was captured for this package.

The initiating cause of the scientific stall remains unproven. Lifecycle crossed
64-step boundaries, including trunk 64 and trunk 960, and completed. That is not
a scientific trial. This package removes the stable empty temporary and separates
serialization from the write. It does not establish that a 600 s stall inside
`dump()` or the first write is gone. It does not authorize migrating `31972d`,
`a8d8b9`, or any earlier campaign.

## Reproduction and raw evidence

Raw run directories, relative to the repository:

- `runs/xbox-acceptance-20261004-ci37194378620/`
- `runs/xbox-watchdog-20261004-ci37194378620/`
- `runs/xbox-worker-20261004-ci37194378620/`
- `runs/xbox-recovery-20261004-ci37194378620/`
- `runs/xbox-lifecycle-20261004-ci37194378620/`
- `runs/xbox-benchmark-20261004-ci37194378620/`
- `runs/xbox-bit-identity-20261004-ci37194378620.json`

Run acceptance, then the watchdog harness with that acceptance, then worker,
recovery, lifecycle and benchmark. The bit-identity report compares this
acceptance and benchmark with `runs/xbox-acceptance-20261004-ci37186655285/`
and `runs/xbox-benchmark-20261004-ci37186655285/`.
