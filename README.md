# FloppyLM

Lab per il miglior language model che stia **intero** su un floppy 3.5" reale: descrizione dei
pesi, tokenizer e runtime in 1 474 560 byte. Il nome `floppy_4mb` è simbolico.
Status: S1-S10 accepted; Xbox GPU backend implemented and validated on Series S
with 52 independent operation cases, 36 model fixtures and exact checkpoint resume. The representative
throughput trial completed; ADR 0011 accepts row16/row8log for scientific E0.
Scientific campaign `e0-20261001T074326Z-503df0` is running; quality results remain pending.
Commands and provenance: [Xbox E0](docs/xbox-e0.md).

```bash
python scripts/e0_status.py --campaign runs/e0-campaign-20261001-e01 --xbox
```

Reads live GPU progress and verifies frozen source/package/job hashes without
changing the campaign. Omit `--xbox` for local state only.

## L'idea in trenta secondi

Il floppy limita i bit a riposo, non la RAM a runtime. Un denso ternario in 11 Mbit si ferma a
~7M parametri; oltre si entra nel **regime sotto il bit**, e lì conta solo dove stanno i bit: nel
core del transformer. La tesi (v0.2): un core ricorsivo i cui pesi sono indici in un codice
vettoriale a 0.5–0.75 bit/peso, addestrato da zero, batte a parità di byte codificati il miglior
core ternario/2-bit. Tre codici in gara — generato da seed, trellis calcolato, codebook appreso —
con un prior dichiarato: i codici calcolati, a zero byte, sono favoriti.

La v0.1 (perturbazioni da seed sui blocchi ricorsivi) è stata chiusa prima di scrivere codice:
agiva su ~0.1% dei bit e i seed non trasportano informazione ([stress test](docs/concept.md#stress-test-v01)).

## Mappa

Il [docs/README.md](docs/README.md) dice quale file possiede quale fatto.

| Documento                                                  | Possiede                                                   |
| ---------------------------------------------------------- | ---------------------------------------------------------- |
| [docs/concept.md](docs/concept.md)                         | Tesi v0.2, principi, F0–F4, stress test v0.1               |
| [docs/experiments-roadmap.md](docs/experiments-roadmap.md) | E0–E4 e gate                                               |
| [docs/positioning.md](docs/positioning.md)                 | Vs Quant-Noise, Sign Lock-In, QTIP, SeedLM, Parameter Golf |
| [docs/adr/](docs/adr/README.md)                            | Budget, avversari, pratiche di laboratorio                 |
| [docs/research/](docs/research/README.md)                  | Survey R1–R7                                               |
| [docs/evidence/](docs/evidence/README.md)                  | Numeri misurati e stato dei run                            |
