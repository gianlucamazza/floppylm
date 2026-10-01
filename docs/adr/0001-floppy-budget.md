# ADR 0001: The budget is the floppy, not the parameters

## Status

`amended` — accepted 2026-09-30, amended 2026-10-01 (project name only).

## Context

The name `floppy_4mb` is symbolic: the target is a real 3.5" HD floppy,
2880 sectors of 512 B = 1 474 560 B. Without a counting rule written before E0, every
comparison can be gamed (tokenizer outside the budget, "system" runtime, dynamic libraries).

Measurements in [R4](../research/04-runtime-and-demoscene.md): FAT12 costs 33 sectors (boot, 2×9 FAT,
14 root dir) → **data area 1 457 664 B**. llama2.c's `run.c` at `-Os` stripped weighs ~19 KB
dynamic; static glibc ~0.9 MB (unusable); musl estimated at 30–60 KB. A bootable Linux floppy
leaves ~264 KB free.

## Decision

1. **Budget** = sum of the files on the FAT12 image, rounded up to the 512 B cluster,
   ≤ 1 457 664 B. No file outside the image is required to generate text, except the kernel
   and the host libc if the binary is dynamic (see 3).
2. **What counts**: model description (weights, seeds, coefficients, entropy coding
   tables), tokenizer, runtime binary, any configuration file.
3. **What does not count**: the host (Linux x86-64). The final runtime (E4) is a **static
   musl** binary; until E4 a pessimistic constant of 64 KB is used for runtime + decoder.
4. **Data floppy, not bootable.** Boot means running the binary from the mounted floppy.
5. **Boot budget** (F3): expansion ≤ 60 s, RAM ≤ 1 GB, generation ≥ 5 tok/s on an
   i7-1165G7 with 4 threads, measured on the C binary, not on PyTorch.
6. Operating budget for the model until E4: **1 457 664 − 64 KB − actual tokenizer** bytes.

## Consequences

- Runtime RAM is free up to 1 GB: this is the asymmetry the thesis exploits
  ([concept](../concept.md)).
- The tokenizer is inside the budget: large vocabularies cost twice (file + embedding).

## Amendment — 2026-10-01 (project name)

The project and repository are named **floppylm**; the former working name `floppy_4mb` in the
Context above is historical. The budget decision is unchanged.
