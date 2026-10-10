# Roadmap gate 4 review of e0-20261009T174028Z-94847b

Reviewed 2026-10-10 against the published
[campaign report](../e0-v2/campaigns/e0-20261009T174028Z-94847b/notes.md),
the [ten-hash freeze](../e0-v2/selections/e0-20261009T174028Z-94847b.json)
and the [final test](../e0-v2/selections/e0-20261009T174028Z-94847b.test.json).
The recomputed checks are in [review.json](review.json). This page does not
open a campaign, accept the
[1/16 pilot proposal](../../adr/proposals/e1-1-16-pilot.md), or authorize a
console job.

## Checks

The campaign finished at 2026-10-10T10:02:53Z with status `completed`, phase
`completed` and no error. Host freeze `96a3054a2b0a0f8478abd4cd961b524c7b49cfdd`
was clean. Protocol ADR is `0020`. Package is
`GianlucaMazza.XgpuE0_0.1.0.109_x64__g0p5dcfz4t9z4`.

Ten trials and three byte repairs are recorded. The counted cells are the
three ternary repairs and the seven first packs that were already inside ±1%
of 85937.5 bytes. The short first packs `94847b-000`, `94847b-001` and
`94847b-003` stay excluded and are absent from the freeze. Every cooldown
branch of the ten counted cells is inside that window. Every counted cell is
`non saturo`.

The freeze and the final test are both `purpose: scientific`, name the same
selection, and carry the same ten `(run_id, artifact, sha256, model_bytes)`
identities. The report hashes match the files:

- selection `de80fff08e750702784e6efbcb583ca86de566965207212c1c6531822a05bbe4`
- final test `6ce7c1d5a9dc20b84a293c677e6f468ddfa2c2b9ca105ddd7edd99404c3db1f7`

`baseline_complete` is true. `instability` is null.

Mean val bpb, ternary then 2-bit:

| Cooldown | Ternary | 2-bit | Ternary minus 2-bit |
| --- | --- | --- | --- |
| T | 1.460359 | 1.502279 | −0.041920 |
| 2T | 1.342273 | 1.374394 | −0.032121 |
| 4T | 1.262101 | 1.285628 | −0.023526 |

The sign is negative at T, 2T and 4T, so rank is stable. The 4T validation
paired mean is −0.023526 bpb, sample SD 0.013161, frozen gate
`max(0.02, 2σ)` = 0.026322. The test paired mean is −0.023838 bpb, sample SD
0.013733, against that same gate. Both absolute means sit inside the gate.
These paired figures match the report.

The stored decisions are unchanged: ternary `d` 80, 4 layers, nominal `d_ff`
262, lr 0.01, wd 0.1; 2-bit `d` 96, 3 layers, nominal `d_ff` 193, lr 0.003,
wd 0.1. Both use SwiGLU and `row8log`. The counted ternary widths are 266,
266, 262, 268 and 262. Every counted 2-bit cell was submitted at `d_ff` 205.
[ADR 0019](../../adr/0019-host-init-pack.md) already allows that init-pack
adjustment. The nominal widths stay the stored decisions.

## Finding

The paired measurement this campaign existed to finish is complete. Ternary
is the lower arm at T, 2T, 4T and on the test. The paired-gate magnitude does
not clear `max(0.02, 2σ)`. Both stored arms remain the scalar baseline. A
later E1 ADR copies those two decisions and the selection hash above.

## Left unaccepted

The 1/16 pilot proposal stays proposed. Its equal-byte rule still cites the
reciprocal check that [ADR 0020](../../adr/0020-target-window-parity.md)
withdrew; this campaign used the ±1% target window. The vector container's
byte layout stays unfixed. No Xbox vector executor is qualified here. `87686a`,
`766d4b` cell `031` and `c58a86` stay stopped.

The next written experiment is that executor qualification against the CPU
oracle, on identical inputs and identical artifact bytes. It is not started
by this review.
