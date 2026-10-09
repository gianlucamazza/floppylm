# Paired-seed successor of campaign 766d4b

## Status

accepted — 2026-10-09; recorded in [ADR 0021](../0021-paired-seed-successor.md).

The decision section below is the same-day record that campaign `766d4b` is not
resumed and that its failed cell `031` is not a result. ADR 0021 applies that
start to a new campaign written before its first paired seed.

## Context

Campaign `e0-20261007T164712Z-766d4b` stopped at 2026-10-09T12:07:22Z in
`paired-seeds`. Both phase selections are stored. Ternary is `d` 80, 4 layers,
`d_ff` 262, lr 0.01, wd 0.1. 2-bit is `d` 96, 3 layers, nominal `d_ff` 193,
lr 0.003, wd 0.1. Cell `027` submitted `d_ff` 205; the stored decision keeps
193. Cell `031` failed on the console and cannot be recovered.

[ADR 0020](../0020-target-window-parity.md) decision 3 forbids copying 2-bit
from `c58a86`. It does not forbid copying `766d4b`'s own stored 2-bit decision
into a new campaign.

## Decision

Open a new campaign at the paired seeds. Copy the two stored decisions, keep
`protocol_adr` `0020`, and bind the same package 0.1.0.105 and its acceptance.
Train all ten seeds fresh. Do not replay the grids, do not open run `031`, and
do not name the scalar recipe before the final test. A later device failure
stops the campaign with no automatic second attempt.

## Consequences

The successor can finish the paired comparison and the reserved final test
without repeating closed cells. The nominal 2-bit width and the submitted
width stay two recorded numbers.
