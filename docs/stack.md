# Stack

Owner di linguaggio, toolchain, vincoli macchina. Non possiede la tesi.

## Linguaggio

- Training ed esperimenti: Python ≥ 3.12, PyTorch 2.11 CPU, `numpy`. Dev: `pytest`, `ruff`.
  Stesso schema di [SmallerGPT](../../smallergpt/docs/stack.md): niente venv finché il banco gira.
- Runtime: C99 derivato da `run.c` di llama2.c, statico con musl (da installare in E4), `-Os`,
  stripped ([R4](research/04-runtime-and-demoscene.md)).
- Generatori: xorshift/PCG/Philox implementati identici in C e Python; test di parità bit-a-bit.
- Prosa docs in italiano, commenti codice in inglese.

## Macchina

Lenovo i7-1165G7, 4C/8T, 32 GB, Iris Xe senza CUDA. Misurato: 92–117 GFLOPS fp32 in burst,
~23 GB/s, bf16 lento (no nativo), AVX512-VNNI per int8 ([R6](research/06-hardware-budget.md)).
Job lunghi **fuori** da `background.slice` (quota 1 core), con `nohup` e log in `runs/`
([ADR 0003](adr/0003-lab-practices.md), amendment). GPU a noleggio solo con ADR (E3).

## Cosa si versiona

Docs, ADR, survey, codice, `summary.json` + `notes.md`. Checkpoint e immagini `.img` restano fuori
da git; il numero vive nel JSON.
