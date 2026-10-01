# FloppyLM

A lab for the best language model that fits **entirely** on a real 3.5" floppy: weight description,
tokenizer and runtime inside one 1 474 560-byte disk ([what counts](docs/adr/0001-floppy-budget.md)).

**Status:** the E0 scalar baseline runs on an Xbox Series S GPU backend; live state, including
whether any quality result exists, is in [docs/STATUS.md](docs/STATUS.md).

## The idea in thirty seconds

FloppyLM asks **how much language-model quality can fit in 1.44 MB** when the model description,
tokenizer and inference runtime all share the disk. The task is generating short stories;
[vision](docs/vision.md) defines success and scope.

The disk limits the model's stored description. The host can use more RAM to reconstruct and run
it. Instead of storing every weight directly, a vector code stores an index for a group of weights.
A decoder reconstructs that group from a fixed generated code or a learned codebook.

The research question is whether a core encoded below one bit per weight beats ternary or 2-bit
weights **at equal actual serialized bytes**, including codebooks, scales and headers. Having more
reconstructed weights is useful only if held-out quality improves. The [concept](docs/concept.md)
states the precise hypothesis and what would falsify it.

## Architecture and objectives

The [architecture](docs/architecture.md) explains the stored description, reconstruction and
execution paths, and distinguishes implemented components from planned ones. The final artifact
is a **data floppy mounted by a Linux host**; the counting rule is [ADR 0001](docs/adr/0001-floppy-budget.md).

| Stage | Question |
| --- | --- |
| E0 | How strong are scalar baselines at the same model bytes? |
| E1 / E1a | Can vector coding improve quality, and does recursion help? |
| E2 | Does the advantage survive coding and rate-aware training for all arms? |
| E3 | Can the full model meet reconstruction, RAM and throughput limits? |
| E4 | Does the complete disk artifact fit and generate useful stories? |

The [roadmap](docs/roadmap.md) owns all gates. Python is the numerical oracle; the separate
Xbox DX12 trainer is checked against it. Qualification proves implementation properties;
scientific results require the experiment gates and recorded evidence in [STATUS](docs/STATUS.md).
A negative scientific result is valuable: it measures where the proposed representation fails.

For the review backlog and source-backed research priorities, see the
[excellence plan](docs/excellence-plan.md) and [research briefs](docs/research/README.md).

## Quickstart

```bash
pytest                            # full host test suite
python experiments/e0_v2.py --run --smoke   # functional CPU smoke; needs data/, writes a tracked evidence dir
python scripts/e0_status.py --campaign runs/<campaign-dir>   # read-only campaign state
```

Requirements: Python ≥ 3.12 with `numpy` and `torch` ≥ 2.4, plus `pytest` and `ruff` for development
([pyproject.toml](pyproject.toml)); no install step is needed, since scripts and pytest put `src/` on the path.
Training reads the prepared TinyStoriesV2-GPT4 corpus in `data/tinystories/`: download the raw
files listed in `floppylm.data.SOURCES` into `data/raw/` and call the Python function
`floppylm.data.prepare`. `python experiments/e0_v2.py --verify-data` re-prepares the corpus in
`runs/tmp` (~2.2 GB) and rewrites `data/tinystories/reproducibility.json`.
Flags and the Xbox procedure: [code map](docs/operations/code-map.md),
[runbook](docs/operations/xbox-e0.md).

## Map

[docs/README.md](docs/README.md) gives reading paths and says which file owns which fact.

| Document                                                             | Owns                                                       |
| -------------------------------------------------------------------- | ---------------------------------------------------------- |
| [docs/STATUS.md](docs/STATUS.md)                                     | Live state                                                 |
| [docs/vision.md](docs/vision.md)                                     | Mission, success, non-goals                                |
| [docs/concept.md](docs/concept.md)                                   | Thesis v0.2, principles, F0–F4, v0.1 stress test           |
| [docs/roadmap.md](docs/roadmap.md)                                   | E0–E4 and their gates                                      |
| [docs/positioning.md](docs/positioning.md)                           | Vs Quant-Noise, Sign Lock-In, QTIP, SeedLM, Parameter Golf |
| [docs/adr/](docs/adr/README.md)                                      | Accepted decisions                                         |
| [docs/research/](docs/research/README.md)                            | Surveys R1–R12                                              |
| [docs/evidence/](docs/evidence/README.md)                            | Measured numbers                                           |
| [docs/stack.md](docs/stack.md), [docs/glossary.md](docs/glossary.md) | Toolchain and machines; terms                              |

## License

[MIT](LICENSE).
