# floppylm contracts

JSON Schemas (draft 2020-12) for every file exchanged between floppylm and its only native
training backend, xbox-gpu-training ([ADR 0012](../docs/adr/0012-repo-boundaries.md)).
floppylm owns them; the backend consumes them at a pinned floppylm commit.

| Schema | File | Direction |
| --- | --- | --- |
| [`floppylm.e0.job.v1`](floppylm.e0.job.v1.json) | `<job_id>.job.json` | host → backend |
| [`floppylm.e0.initialization.v1`](floppylm.e0.initialization.v1.json) | job `initialization` asset | host → backend |
| [`floppylm.e0.weights.v1`](floppylm.e0.weights.v1.json) | `branch-<end_step>.json` | backend → host |
| [`floppylm.e0.result.v1`](floppylm.e0.result.v1.json) | `results/<job_id>/status.json`, host `result.json` | backend → host |
| [`floppylm.device.v1`](floppylm.device.v1.json) | `LocalState/device.json` | backend → host |

[`floppylm.e0.common.v1`](floppylm.e0.common.v1.json) holds shared definitions (config,
descriptor, tensor). Schemas reference each other by `$id`; load all of them into one registry.

## Rules

- A schema describes what the producers write today, including their failure variants.
  Changing a producer without updating the schema fails `tests/test_contracts.py`.
- A breaking change adds a new `vN` schema and file; a published `v1` only gains corrections
  that make it match its producers.
- Golden instances live in `tests/fixtures/contracts/{valid,invalid}/<schema>--<case>.json`
  and are regenerated with `python scripts/contract_fixtures.py`. Valid ones come from the real
  producers and measured native evidence; each invalid one breaks exactly one rule.
