# Positioning

Owner del confronto con lo stato dell'arte. Le survey complete stanno in [`research/`](research/README.md).

| Lavoro                       | Cosa fa                                                                | Differenza con FloppyLM                                              |
| ---------------------------- | ---------------------------------------------------------------------- | -------------------------------------------------------------------- |
| Quant-Noise                  | LM da zero con PQ, ~1.3 bit/peso, condivisione di layer                | Sopra il bit per peso unico; nessun confronto con codici casuali     |
| Sign Lock-In (ICML 2026)     | Template di segni low-rank, LM a caratteri da zero a ~0.5–0.7 bit/peso | Non VQ; candidato ibrido per E1b                                     |
| QTIP                         | Codici trellis calcolati, pari a codebook appresi su LLM               | Post-training a ≥ 2 bit; qui è un braccio favorito del core          |
| SeedLM                       | Seed LFSR per blocco, post-training, 3–4 bit/peso                      | Qui il codebook da seed è un braccio, da zero e sotto il bit         |
| AQLM / VPTQ / GPTVQ          | VQ appreso post-training a ~2 bit                                      | Codebook troppo grandi per 11 Mbit; qui codebook condiviso e contato |
| BTC-LLM / GLVQ               | Codebook appresi a 0.7–1.0 bit, post-training                          | Non da zero, non tiny                                                |
| Parameter Golf #1110 / #1113 | Ricorsione (1.22 bpb) batte seed + LoRA (1.37) a ~5 MB                 | Motivo della chiusura di v0.1                                        |
| VBQ (2026)                   | Più grande a meno bit batte più piccolo su TinyStories                 | Regime ≥ 1.8 bit/peso                                                |
| llama2.c stories260K         | LM denso che sta su un floppy                                          | Nessuna metrica per byte; punto della frontiera E0                   |
| Hutter Prize / cmix / NNCP   | Decompressore contato nel budget                                       | Stesso principio di accounting                                       |

Riferimenti e numeri: [R2](research/02-procedural-weights.md), [R7](research/07-learned-vq-subbit.md),
[R1](research/01-tiny-lms.md).
