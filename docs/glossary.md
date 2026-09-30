# Glossary

| Termine                        | In una riga                                                      | Owner                                                         |
| ------------------------------ | ---------------------------------------------------------------- | ------------------------------------------------------------- |
| `image_bytes`                  | Byte allocati sull'immagine FAT12, tutto incluso                 | [ADR 0001](adr/0001-floppy-budget.md)                         |
| Regime sotto il bit            | Meno di 1 bit stoccato per peso unico (o effettivo)              | [concept](concept.md)                                         |
| Parametri effettivi            | Parametri del modello espanso in RAM al boot, ricorsione inclusa | [concept](concept.md)                                         |
| Core                           | Pesi dei blocchi transformer, esclusi embedding e norme          | [concept](concept.md)                                         |
| Core vettoriale                | Core scritto come indici in un codice su blocchi di `v` pesi     | [concept](concept.md)                                         |
| VQ-seed / trellis / VQ-appreso | I tre decodificatori del core in gara                            | [concept](concept.md), [R7](research/07-learned-vq-subbit.md) |
| Byte codificati                | Byte dopo entropy coding, base di ogni confronto                 | [concept](concept.md) P3                                      |
| Budget in miniatura            | 1/16 e 1/4 di 11 Mbit, dove i bracci saturano su CPU             | [ADR 0004](adr/0004-miniature-budgets.md)                     |
| Frontiera scalare              | Miglior ternario/2-bit/int4 dopo ricerca di forma                | [ADR 0002](adr/0002-adversary-dense-frontier.md)              |
| Rate loss / MDL                | `NLL + λ·bit(descrizione)`                                       | [R3](research/03-mdl-compression.md)                          |
| bpb                            | Bit per byte di testo held-out, dal runtime C                    | [R5](research/05-eval-tiny.md)                                |
| Boot                           | Mount → decodifica/espansione → primo token                      | [ADR 0001](adr/0001-floppy-budget.md)                         |
