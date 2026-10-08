# Survey 4 — Runtime, packers and the demoscene

Consolidated from web research on 2026-09-30.

> **Framed for thesis v0.1.** Its "Minimum experiment" section predates [concept v0.2](../concept.md); E0–E4 are defined only by the [roadmap](../roadmap.md).

## Question

How many bytes of the floppy does the runtime (binary + tokenizer + filesystem) eat, and what does the
demoscene teach about **generating instead of storing**?

## What exists

### Filesystem: how much really remains on a 1.44 MB

Measured locally (`mkfs.fat -C -F 12 fd.img 1440`, `minfo`, `mdir`):

| Region                              | Sectors |         Bytes |
| ----------------------------------- | ------: | ------------: |
| Boot sector                         |       1 |           512 |
| 2 × FAT12 (9 sectors each)          |      18 |         9 216 |
| Root dir (224 entries × 32 B)       |      14 |         7 168 |
| **FAT12 overhead**                  |  **33** |    **16 896** |
| Data area (2 847 clusters of 512 B) |   2 847 | **1 457 664** |

- Total image 1 474 560 B; `mdir` reports 1 457 664 free bytes. Per-file slack ≤511 B
  (cluster = 1 sector): with 3–4 files the cost is <2 KB.
- A "raw" floppy (dd with no FS) would give all 1 474 560 B, but it is not readable as a data floppy
  by an arbitrary host: E4 must use FAT12. The 1.68 MB (DMF) / 1.722 MB formats (used by
  [tomsrtbt](https://en.wikipedia.org/wiki/Tomsrtbt)) are out of contract: the budget is 1 474 560.

### Inference runtime: from 18 KB to 18 MB

Measured locally on [`llama2.c/run.c`](https://github.com/karpathy/llama2.c) (38 545 B of
source, gcc 15, x86-64):

| Build                                                                      |   Bytes |
| -------------------------------------------------------------------------- | ------: |
| `gcc -Os`, dynamic glibc, `strip -s`                                       |  18 848 |
| same + `-ffunction-sections --gc-sections -fno-asynchronous-unwind-tables` |  18 840 |
| same, `xz -9e` (only as an estimate of code entropy)                       |   7 156 |
| `gcc -Os -static` glibc, strip                                             | 927 872 |
| same `xz -9e`                                                              | 328 596 |

- Static glibc is unusable (~0.9 MB = 63% of the floppy). Static musl: hello world ~7 KB
  vs ~600 KB glibc ([sta.li FAQ](https://sta.li/faq/),
  [Chainguard](https://edu.chainguard.dev/chainguard/chainguard-images/about/images-compiled-programs/glibc-vs-musl/));
  for run.c (only libm + stdio + mmap) the estimate is **30–60 KB** static stripped. `musl-gcc` is
  not installed: number to be measured in E4.
- llama.cpp: the local `llama-cli` is 1.06 MB, but it drags in `libllama` 3.6 MB + `libggml-base` 0.8 MB
  \+ `libllama-common` 4.9 MB (+ backend): **≥10 MB**. Excluded: 7× the floppy.
- Existing minimal ports: [dosllam2](https://github.com/yeokm1/dosllam2) (llama2.c on 32-bit DOS),
  dozens of single-file ports (Java, Rust, Zig). tinygrad/Python runtimes assume an
  interpreter on the host: allowed only if ADR 0001 declares "host with Python" — discouraged,
  it moves bytes out of the count.
- The FloppyLM runtime must add to run.c: an entropy decoder (rANS/range coder: 1–3 KB of
  code; the kkrunchy depacker is ~300 B of hand-written x86) + a PRNG generator (<1 KB) + the
  "recipe" (basis × coefficients). Estimate: **+3–6 KB** on the binary.

### Executable packers: typical ratios

- **UPX** (ELF/PE): 40–60% of the original size, `--lzma`/`--ultra-brute` down to ~30%
  ([upx(1)](https://man.archlinux.org/man/extra/upx/upx.1.en)). On a 20 KB binary the
  gain is ~10 KB: marginal, and it does not apply to the weights (already entropy-coded).
- **kkrunchy** (farbrausch, 2006): LZ77 + arithmetic coding + x86-specific model; reported
  example 41.5 KB (UPX) → 32.5 KB, i.e. −22% versus UPX
  ([ryg blog](https://fgiesen.wordpress.com/2011/01/24/x86-code-compression-in-kkrunchy/),
  [pouët](https://www.pouet.net/prod.php?which=26088)).
- **Crinkler** (4k/8k): context-mixing linker-compressor, the de facto standard for 4k
  ([code4k](http://code4k.blogspot.com/2010/12/crinkler-secrets-4k-intro-executable.html)).
- **squishy** (Logicoma): kkrunchy's successor for 64k, compresses better at the cost of a lot of CPU
  ([logicoma](https://logicoma.io/squishy/)).
- Lesson: scene packers win with **context mixing on code**; on the weights the equivalent work
  is our entropy coder (E2). They are all Windows/PE; on Linux ELF what remains is UPX or a
  hand-written xz/rANS depacker.

### Demoscene: generating instead of storing

- **.kkrieger** (theprodukkt/farbrausch, Breakpoint 2004): a complete FPS in 96 KB. Textures stored
  as a **creation history** (operator graph) instead of per pixel; meshes from deformed
  primitives; synthesized audio. Only the history + generator code in the executable
  ([Wikipedia](https://en.wikipedia.org/wiki/.kkrieger),
  [werkkzeug3 source](https://github.com/jaromil/kkrieger-werkkzeug3)). Expansion into RAM of
  hundreds of MB starting from ~96 KB: ratio >1000×, paid in loading time.
- **4k/64k intros**: same principle — the data is a program. The ratio works because the
  content (textures, music) has a **compact generative structure** and tolerates perceptual
  loss. The hidden cost: hours of human authoring to find the recipe.
- **Linux on a floppy**: tomsrtbt (2002, 1.722 MB), [Floppinux 2025](https://krzysztofjankowski.com/floppinux/floppinux-2025.html):
  kernel 6.14 ~830 KB, **264 KB** remain free. A bootable Linux floppy leaves <20% to the model.
  FreeDOS kernel + shell ≈ 100 KB, plus a DOS extender for a 32-bit binary (dosllam2).

### PRNGs to regenerate weights

| PRNG                                                                                                   | State       | Properties                                                                     | Measured throughput (1 thread, i7-1165G7)                                  |
| ------------------------------------------------------------------------------------------------------ | ----------- | ------------------------------------------------------------------------------ | -------------------------------------------------------------------------- |
| xorshift32 (×4 lanes)                                                                                  | 4 B/lane    | serial per lane, low quality but sufficient for bases                          | 100M floats in 0.37 s (1.08 GB/s written)                                  |
| PCG32                                                                                                  | 8 B         | serial, good quality, O(log n) jump-ahead                                      | 100M floats in 0.39 s (1.03 GB/s)                                          |
| 16-bit LFSR (SeedLM)                                                                                   | 2 B         | seed = 16 bits per block, hardware-friendly                                    | 245 M scalar steps/s; independent blocks → parallel                        |
| Philox4x32-10 ([Random123](https://www.thesalmons.org/john/random123/releases/latest/docs/index.html)) | counter+key | **counter-based**: w[i] = f(key, i), random access, parallel/lazy regeneration | same order (it is torch's default on CUDA); `torch.rand` CPU 100M in 1.1 s |

- [SeedLM (Apple, ICLR 2025)](https://arxiv.org/abs/2410.10714): for each weight block an LFSR seed
  generates a pseudo-random matrix linearly combined with a few quantized coefficients;
  3–4 bits/weight, data-free, post-training on Llama. It shows that "seed + coefficients" holds at
  LLM scale, but it **compresses an existing dense model** (≥ bits/weight), it does not expand.
- For FloppyLM the PRNG is not the bottleneck: 100M fp32 weights = 400 MB generated in ~0.1 s
  on 4 cores. A counter-based one (Philox or per-block LFSR) is needed if layers are to be
  regenerated on the fly instead of kept in RAM.

## What is missing

- No documented "demoscene-style" LM: searched for `kkrieger language model`,
  `64k intro neural network`, `procedural weights floppy`; only tiny networks exist in 4k/64k
  (synthesis, shaders), not LMs. Counter-example not found, but the search is keyword-based (F0
  stays with survey 02).
- No measured number for static musl run.c + decoder: estimate 30–60 KB, to be closed in E4.
- The tokenizer has no standard "packer": measured on a proxy vocabulary (BERT, frequency
  order): 512 entries 2.7 KB raw / 1.6 KB xz; 4096 entries 28 KB raw / **13 KB xz**; 8192 entries
  59 KB / 27 KB. llama2.c `tokenizer.bin` format (float score + len) at 4096 entries: 57 KB —
  the scores can be derived from the rank and must be removed.

## Implication for the thesis

Byte count (FAT12 data area = 1 457 664 B):

| Scenario                                         |   Runtime |        Tokenizer | Slack/meta |    **Left for the model** |
| ------------------------------------------------ | --------: | ---------------: | ---------: | ------------------------: |
| Data floppy, Linux host, dynamic run.c + decoder |    ~24 KB | 13 KB (4096, xz) |      ~2 KB | **~1 418 KB ≈ 11.3 Mbit** |
| Data floppy, static musl + decoder (portable)    |    ~60 KB |            13 KB |      ~2 KB | **~1 382 KB ≈ 11.0 Mbit** |
| Conservative: static, raw llama2.c tokenizer     |    ~65 KB |            57 KB |      ~2 KB |     ~1 334 KB ≈ 10.7 Mbit |
| Bootable Linux (Floppinux)                       | ~1 190 KB |                — |          — |      ≤264 KB: thesis dead |

- **Realistic runtime + tokenizer + FS ≈ 40–90 KB (3–6% of the floppy)**. The model has
  **~1.38–1.42 MB ≈ 11 Mbit**. The runtime is not the problem: the bits/parameter ratio is.
- ADR 0001 must fix: a **data** floppy read by an x86-64 Linux host, static musl binary (no
  uncounted dependencies), `image_bytes` = 1 474 560. Bootable = out of scope.
- **F0**: the demoscene and SeedLM are prior art for the principle, not for the product (SeedLM
  compresses, it does not train in a generative regime). It does not close F0.
- **F1/F2**: the .kkrieger lesson is that generation beats storage only if the content has a
  compact structure. LM weights are close to noise: without identical entropy coding on the
  dense baseline (F2), any procedural advantage is suspect.
- **F3**: PRNG regeneration costs <1 s per 100M weights: F3 does not trigger for the PRNG; it
  triggers only if the generator is a heavy network (see survey 06).

## Minimum experiment

- **E0**: bit-accounting harness that prints `runtime_bytes` by measuring the real binary
  (static musl `-Os`, strip, with and without UPX) and `tokenizer_bytes` for compressed vocab
  512/1024/4096; fixes the `model_bytes` available to the dense frontier.
- **E1**: the procedural budget uses the same `model_bytes`; seeds and coefficients counted.
- **E2**: same entropy coder (rANS) for dense and procedural; the decoder code counts only
  once in the runtime.
- **E3**: measures expansion time with Philox/LFSR/xorshift at 30–100M; target ≤60 s,
  expected <5 s.
- **E4**: image `mkfs.fat -C -F 12 fd.img 1440` + `mcopy`, check `mdir` and boot from a clean
  host (container without toolchain) → `image_bytes` = 1 474 560 measured, not estimated.

Later note (2026-10-08): the bit-accounting harness and the FAT12 image are E3
and E4. E0 counts serialized model bytes against one shared target. Runtime and
tokenizer bytes are not the E0 selection metric.
