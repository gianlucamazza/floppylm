# E0 console lifecycle config

Owner of the settings the campaign runner and the lifecycle unit pass to
xbox-gpu-training `scripts/e0_console_lifecycle.py`
([PR #46](https://github.com/gianlucamazza/xbox-gpu-training/pull/46)).
Procedure stays in the [Xbox runbook](xbox-e0.md). Live package and campaign
identity stay in [STATUS](../STATUS.md).

Nothing here assumes a particular console, host path, process image, GPU
adapter, or engine index. The companion tool performs generic engine/adapter
detection and can terminate by package or pid. This repository only forwards
the values below.

## Resolution order

Highest wins:

1. Campaign / teardown CLI flags (`--lifecycle-tool`, `--lifecycle-config`,
   `--allow-orphan-gpu`, `--host-heartbeat-seconds`, `--package`,
   `--wait-seconds`)
2. `campaign.json` → `console_lifecycle.config` (policy snapshot written at
   campaign start)
3. JSON file `$FLOPPYLM_E0_LIFECYCLE_CONFIG` or `--lifecycle-config`
4. Environment (and `EnvironmentFile=` drop-ins)
5. Documented defaults in the table

Connection settings (Device Portal URL, user, password, TLS pin) are read from
the environment at each invoke so a recover on another tunnel still works.
Credentials are never written to `campaign.json` and never printed.

The unit template `units/floppylm-e0-campaign@.service` loads
`%E/floppylm/xbox.env` then `%E/floppylm/e0-lifecycle.env`. Copy
[e0-lifecycle.env.example](e0-lifecycle.env.example).

## Settings

| Setting | Env | JSON / campaign key | CLI | Default | Forwarded to the tool |
| --- | --- | --- | --- | --- | --- |
| Tool path | `XGPU_E0_CONSOLE_LIFECYCLE` | `tool` | `--lifecycle-tool` | unset (lifecycle skipped, logged) | process executable |
| Host heartbeat interval | `XGPU_E0_HOST_HEARTBEAT_SECONDS` | `heartbeat_seconds` | `--host-heartbeat-seconds` | `300` | `heartbeat` subcommand, repeated |
| Teardown wait | `XGPU_E0_TEARDOWN_WAIT_SECONDS` | `teardown_wait_seconds` | `--wait-seconds` | omit (tool default) | `teardown --wait-seconds` |
| Refuse orphan before start | `XGPU_E0_REFUSE_ORPHAN` | `refuse_orphan` | `--allow-orphan-gpu` sets false | `true` | not a tool flag; runner policy |
| Package full name | `XGPU_E0_PACKAGE` | `package` | `--package` | campaign `package` if present | `--package` |
| Process image | `XGPU_E0_APP_IMAGE` | `image` | — | omit | `--image` |
| Process id | `XGPU_E0_PID` | `pid` | — | omit | `--pid` |
| GPU adapter | `XGPU_E0_GPU_ADAPTER` | `adapter` | — | omit | `--adapter` |
| GPU engine index | `XGPU_E0_GPU_ENGINE` | `engine` | — | omit | `--engine` |
| Engine busy threshold | `XGPU_E0_GPU_ENGINE_PERCENT` | `engine_percent` | — | omit | `--engine-percent` |
| CPU idle threshold | `XGPU_E0_IDLE_CPU_PERCENT` | `cpu_idle_percent` | — | omit | `--cpu-idle-percent` |
| Device Portal URL | `UWP_DEVICE_URL` or `XBOX_IP`+`XBOX_PORT` | `device_url` | — | URL required; port defaults to Device Portal `11443` only when building from `XBOX_IP` | `UWP_DEVICE_URL` |
| Device Portal user | `UWP_DEVICE_USER` or `XBOX_USER` | — | — | unset | `UWP_DEVICE_USER` |
| Device Portal password | `OPENAPPX_DEVICE_PASSWORD` or `XBOX_PASS` | — | — | unset | `OPENAPPX_DEVICE_PASSWORD` |
| TLS pin | `OPENAPPX_DEVICE_PIN` or `XBOX_CERT_SHA256` | — | — | unset | `OPENAPPX_DEVICE_PIN` |

Boolean env values: `0`, `false`, `no`, `off` are false; anything else is true.

Omitted detection flags mean “let the companion tool decide”. Do not copy a
historical engine index into a drop-in unless that console still needs it.

## JSON file

```json
{
  "heartbeat_seconds": 120,
  "teardown_wait_seconds": 90,
  "refuse_orphan": true,
  "package": "Publisher.App_1.2.3.4_x64__publisher",
  "image": "App.exe",
  "adapter": "0",
  "engine": "3",
  "engine_percent": "90",
  "cpu_idle_percent": "1"
}
```

Env key names are also accepted. Do not put passwords in this file.

## Runner and unit calls

The call sites stay thin. They always use these subcommands:

```text
idle-gpu --when before
heartbeat
teardown [--wait-seconds N]
idle-gpu --when after
```

Identity and threshold flags are appended only when configured. `ExecStop` is
`scripts/e0_console_teardown.py --campaign "$FLOPPYLM_E0_OUT"`; it rereads the
same environment and the campaign snapshot.
