# Contributing

Read [README.md](README.md) and [docs/README.md](docs/README.md) first. The native
Xbox trainer lives in [xbox-gpu-training](https://github.com/gianlucamazza/xbox-gpu-training)
([ADR 0012](docs/adr/0012-repo-boundaries.md)).

## Rules

- **One owner per fact.** Update the owner page; other documents link to it
  ([docs/README.md](docs/README.md#fact-owners)).
- **Live state only in [docs/STATUS.md](docs/STATUS.md).** Package bumps and campaign
  start/stop/recover edit that page alone.
- **ADRs are not rewritten** ([docs/adr/README.md](docs/adr/README.md)). Amend or supersede.
- **Evidence is frozen.** Translation and dated Later notes only.
- While an E0 campaign is running, do not edit `src/` or `experiments/`.
- Do not wrap training or campaign jobs in `bg` / `background.slice`
  ([ADR 0003](docs/adr/0003-lab-practices.md), [ADR 0017](docs/adr/0017-runtime-liveness.md)).
  Host long jobs with `systemd-run --user` and linger. Recovery is explicit, never automatic.
- Schemas `floppylm.*.v1` are owned here. The Xbox repo vendors them; change them here first.

## Language and style

- Code, comments, docs, commit messages and PR titles: **English**.
- Conventional commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`).
- Terms: [docs/glossary.md](docs/glossary.md).

## Branches and pull requests

- Branch `<type>/<short-slug>` from `main`; one PR per change.
- Squash-merge. Do not merge with red CI (`python`).
- PR body: objective, commands run, results, what was **not** done
  ([template](.github/PULL_REQUEST_TEMPLATE.md)).
- Labels: `research`, `e0`, `contracts`, `adr`, `documentation`.

## Local checks

```bash
python -m pip install -e '.[dev]'
ruff check src tests scripts experiments
python -m pytest -q -m 'not native'
```

`python -m pytest -q` also runs the native marker. Those tests need the host
build of `xgpu_e0_train` (`XGPU_E0_BINARY`). CI builds that binary from the
pinned xbox-gpu-training commit in [`.github/workflows/tests.yml`](.github/workflows/tests.yml)
and runs the full suite.
