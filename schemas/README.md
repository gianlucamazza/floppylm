# floppylm contracts

JSON Schemas (draft 2020-12) for every file exchanged between floppylm and its only native
training backend, xbox-gpu-training ([ADR 0012](../docs/adr/0012-repo-boundaries.md)), plus the
[inbox protocol](../docs/contracts/inbox-protocol.md) that moves them. floppylm owns all of them;
the backend vendors them at a pinned floppylm commit and tests against that copy.

| Schema                                                                    | File                                                                                                                             | Direction      |
| ------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | -------------- |
| [`floppylm.e0.job.v1`](floppylm.e0.job.v1.json)                           | `<job_id>.job.json` (training)                                                                                                   | host → backend |
| [`floppylm.e0.initialization.v1`](floppylm.e0.initialization.v1.json)     | job `initialization` asset                                                                                                       | host → backend |
| [`floppylm.checkpoint.v1`](floppylm.checkpoint.v1.json)                   | `results/<job_id>/checkpoint.json`, job `resume` asset                                                                           | both           |
| [`floppylm.e0.weights.v1`](floppylm.e0.weights.v1.json)                   | `results/<job_id>/branch-<end_step>.json`                                                                                        | backend → host |
| [`floppylm.e0.result.v1`](floppylm.e0.result.v1.json)                     | `results/<job_id>/status.json`, host `result.json`                                                                               | backend → host |
| [`floppylm.e0.fixture.v1`](floppylm.e0.fixture.v1.json)                   | model fixture job                                                                                                                | host → backend |
| [`floppylm.e0.fixture.report.v1`](floppylm.e0.fixture.report.v1.json)     | its `<job_id>.actual.json`                                                                                                       | backend → host |
| [`floppylm.e0.kernels.v1`](floppylm.e0.kernels.v1.json)                   | per-operation fixture job, with the op-id table                                                                                  | host → backend |
| [`floppylm.e0.kernels.result.v1`](floppylm.e0.kernels.result.v1.json)     | its `<job_id>.actual.json`                                                                                                       | backend → host |
| [`floppylm.e0.optimizer.v1`](floppylm.e0.optimizer.v1.json)               | optimizer fixture job                                                                                                            | host → backend |
| [`floppylm.e0.optimizer.report.v1`](floppylm.e0.optimizer.report.v1.json) | its `<job_id>.actual.json`                                                                                                       | backend → host |
| [`floppylm.device.v1`](floppylm.device.v1.json)                           | `device.json`, with optional `capabilities`                                                                                      | backend → host |
| [`floppylm.xbox.acceptance.v1`](floppylm.xbox.acceptance.v1.json)         | acceptance proof bound by scientific runs                                                                                        | host evidence  |
| [`floppylm.e0.constants.v1`](floppylm.e0.constants.v1.json)               | [published instance](values/floppylm.e0.constants.v1.json): codec, model, optimizer and schedule constants and the tensor layout | shared         |

[`floppylm.e0.common.v1`](floppylm.e0.common.v1.json) holds shared definitions (config, spec,
descriptor, tensors, moments, execution statistics, gates). Schemas reference each other by
`$id`; load all of them into one registry.

## Rules

- A schema describes what the producers write, including their failure variants and the
  historical forms still present in evidence. Changing a producer without updating the schema
  fails `tests/test_contracts.py`, which validates every matching object in `docs/evidence/`.
- A published `vN` may only gain optional fields, added here before any producer emits them, and
  corrections that make it match its producers. Removing or redefining a field needs `vN+1`.
- `values/floppylm.e0.constants.v1.json` is generated from the Python sources; a test fails if it
  drifts from them.
- Golden instances live in `tests/fixtures/contracts/{valid,invalid}/<schema>--<case>.json`.
  Valid ones come from the real producers: floppylm's Python code, the native backend in
  `--reference` mode (a tiny job on the host CPU) and measured evidence. Each invalid one is a
  reduced valid instance that breaks exactly one rule. Regenerate both with:

  ```bash
  python scripts/contract_fixtures.py --binary <xbox-gpu-training build>/xgpu_e0_train
  ```
