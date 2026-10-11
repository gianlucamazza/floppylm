# E0 console lifecycle config

Owner of the settings the campaign runner and the lifecycle unit pass to
xbox-gpu-training `scripts/e0_console_lifecycle.py`
([PR #46](https://github.com/gianlucamazza/xbox-gpu-training/pull/46), tip
`94769836a5af8ceaa226ea2c24aef39cef696c1f`). The tool's table lives in
`docs/e0/lifecycle.md` on that branch. Procedure stays in the
[Xbox runbook](xbox-e0.md). Live package and campaign identity stay in
[STATUS](../STATUS.md).

Nothing here assumes a particular console, host path, process image, GPU
adapter, or engine index. This repository only forwards the names below.
Unset values are omitted so the tool's documented defaults apply.

## Resolution order

Highest wins on the FloppyLM side:

1. Campaign / teardown CLI flags (`--lifecycle-tool`, `--lifecycle-config`,
   `--allow-orphan-gpu`, `--heartbeat-interval-seconds`, `--package`,
   `--teardown-wait-seconds`)
2. `campaign.json` → `console_lifecycle.config` (policy snapshot written at
   campaign start)
3. JSON file `$FLOPPYLM_E0_LIFECYCLE_CONFIG` or `--lifecycle-config`
4. Environment (and `EnvironmentFile=` drop-ins)
5. Omit the flag so xbox-gpu-training#46 defaults apply

On the tool: documented default < credentials file < environment < CLI flag.
The credentials path is `--credentials` or `XGPU_PORTAL_CREDENTIALS`.

Connection settings (Device Portal URL, user, password, TLS pin) are read from
the environment or credentials file at each invoke so a recover on another
tunnel still works. The password is never a CLI flag, never written to
`campaign.json`, and never printed. Pass it through `XGPU_PORTAL_PASSWORD`,
`OPENAPPX_DEVICE_PASSWORD`, or the credentials file only.

The unit template `units/floppylm-e0-campaign@.service` loads
`%E/floppylm/xbox.env` then `%E/floppylm/e0-lifecycle.env`. Copy
[e0-lifecycle.env.example](e0-lifecycle.env.example).

## Settings

Names match xbox-gpu-training `docs/e0/lifecycle.md`. FloppyLM-only rows are
marked.

| Setting | Env | JSON / campaign key | CLI | Default when omitted | Forwarded to the tool |
| --- | --- | --- | --- | --- | --- |
| Tool path (FloppyLM) | `XGPU_E0_CONSOLE_LIFECYCLE` | `tool` | `--lifecycle-tool` | unset (lifecycle skipped, logged) | process executable |
| Idle exit | `XGPU_IDLE_EXIT_SECONDS` | `idle_exit_seconds` | `--idle-exit-seconds` | tool `1800` | `--idle-exit-seconds` |
| Host heartbeat interval | `XGPU_HEARTBEAT_INTERVAL_SECONDS` | `heartbeat_interval_seconds` | `--heartbeat-interval-seconds` | tool `30` (runner thread uses 30 when unset) | `--heartbeat-interval-seconds` |
| Heartbeat stale | `XGPU_HEARTBEAT_STALE_SECONDS` | `heartbeat_stale_seconds` | `--heartbeat-stale-seconds` | tool `1800` | `--heartbeat-stale-seconds` |
| Poll interval | `XGPU_POLL_INTERVAL_SECONDS` | `poll_interval_seconds` | `--poll-interval-seconds` | tool `1` | `--poll-interval-seconds` |
| GPU pin threshold | `XGPU_GPU_THRESHOLD_PERCENT` | `gpu_threshold_percent` | `--gpu-threshold-percent` | tool `90` | `--gpu-threshold-percent` |
| GPU sample count | `XGPU_GPU_SAMPLE_COUNT` | `gpu_sample_count` | `--gpu-sample-count` | tool `3` | `--gpu-sample-count` |
| GPU sample interval | `XGPU_GPU_SAMPLE_INTERVAL_SECONDS` | `gpu_sample_interval_seconds` | `--gpu-sample-interval-seconds` | tool `1` | `--gpu-sample-interval-seconds` |
| GPU engine filter | `XGPU_GPU_ENGINES` (comma indices) | `gpu_engines` | `--gpu-engine` (repeat) | tool: all engines | `--gpu-engine` (repeat) |
| Idle CPU threshold | `XGPU_IDLE_CPU_PERCENT` | `idle_cpu_percent` | `--idle-cpu-percent` | tool `1` | `--idle-cpu-percent` |
| Teardown wait | `XGPU_TEARDOWN_WAIT_SECONDS` | `teardown_wait_seconds` | `--teardown-wait-seconds` | tool `60` | `--teardown-wait-seconds` |
| Process image names | `XGPU_PROCESS_IMAGES` (comma) | `process_images` | `--process-image` (repeat) | tool `xgpue0.exe` | `--process-image` (repeat) |
| Package full name | `XGPU_E0_PACKAGE` | `package` | `--package` | campaign `package` if present | `--package` |
| Package family | `XGPU_PACKAGE_FAMILY` | `package_family` | `--package-family` | tool: none | `--package-family` |
| Terminate by | `XGPU_TERMINATE_BY` | `terminate_by` | `--terminate-by` (repeat) | tool `package`, `pid` | `--terminate-by` (repeat) |
| Portal URL | `XGPU_PORTAL_URL` or `UWP_DEVICE_URL` | `portal_url` | `--portal-url` | URL required; `XBOX_IP`+port builds one | `--portal-url` |
| Portal port | `XGPU_PORTAL_PORT` | `portal_port` | `--portal-port` | tool `11443` | `--portal-port` |
| TLS verify | `XGPU_PORTAL_TLS_VERIFY` | `tls_verify` | `--tls-verify pin\|none\|system` | tool `pin` | `--tls-verify` |
| TLS pin | `XGPU_PORTAL_TLS_PIN` or `OPENAPPX_DEVICE_PIN` | `tls_pin` | `--tls-pin` | none | `--tls-pin` |
| Portal user | `XGPU_PORTAL_USER` or `UWP_DEVICE_USER` | — | — | unset | env only |
| Portal password | `XGPU_PORTAL_PASSWORD` or `OPENAPPX_DEVICE_PASSWORD` | — | — | unset | env / credentials file only |
| Credentials file | `XGPU_PORTAL_CREDENTIALS` | `credentials` | `--credentials` | none | `--credentials` |
| Refuse orphan before start (FloppyLM) | `XGPU_E0_REFUSE_ORPHAN` | `refuse_orphan` | `--allow-orphan-gpu` sets false | `true` | not a tool flag; runner policy |

Boolean env values: `0`, `false`, `no`, `off` are false; anything else is true.

Do not forward the retired flags `--engine`, `--adapter`, `--image`, `--pid`,
`--engine-percent`, `--cpu-idle-percent`, or `--wait-seconds`.

## JSON file

```json
{
  "heartbeat_interval_seconds": 30,
  "idle_exit_seconds": 1800,
  "teardown_wait_seconds": 90,
  "gpu_engines": ["3"],
  "process_images": ["xgpue0.exe"],
  "terminate_by": ["package", "pid"],
  "refuse_orphan": true,
  "package": "Publisher.App_1.2.3.4_x64__publisher"
}
```

Env key names are also accepted. Do not put passwords in this file.

## Runner and unit calls

The call sites stay thin. Global flags come before the subcommand:

```text
python e0_console_lifecycle.py [global flags] idle-gpu --when before
python e0_console_lifecycle.py [global flags] heartbeat
python e0_console_lifecycle.py [global flags] teardown
python e0_console_lifecycle.py [global flags] idle-gpu --when after
```

Identity and threshold flags are appended only when configured. `ExecStop` is
`scripts/e0_console_teardown.py --campaign "$FLOPPYLM_E0_OUT"`; it rereads the
same environment and the campaign snapshot.
