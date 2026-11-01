"""Does a vq core survive full quantization under a given partial-quantization recipe?

Diagnostic only. Not a pilot cell and not the F1 signal. It reads train.bin alone: the last
--holdout bytes are never sampled for training and score the fully quantized model. It does
not open validation or test and writes nothing under runs/e1-1-16.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import torch  # noqa: E402

from floppylm.data import load  # noqa: E402
from floppylm.e1_pilot import PILOT_BATCH, cell_plan, materialize_cell  # noqa: E402
from floppylm.train import (  # noqa: E402
    DataStream,
    QuantRamp,
    _optimizer,
    _step,
    lr_at,
    sliding_bpb,
)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", required=True, help="pilot vq arm, e.g. vq-0.5-fixed")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--steps", type=int, default=800)
    ap.add_argument("--ramp-end", type=int, help="ramp to p=1 by this step; omit for constant 0.1")
    ap.add_argument("--lr", type=float, help="override the recipe learning rate")
    ap.add_argument("--cooldown", type=int, default=0, help="linear lr decay over the last steps")
    ap.add_argument("--every", type=int, default=200)
    ap.add_argument("--warmup", type=int, default=64)
    ap.add_argument("--holdout", type=int, default=64 * 1024)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    torch.set_num_threads(args.threads)

    index = next(
        i
        for i, cell in enumerate(cell_plan())
        if cell["arm"] == args.arm and cell["seed"] == args.seed and cell["core"] == "vq"
    )
    built = materialize_cell(index)
    model, spec = built["model"], built["spec"]
    if args.ramp_end is not None:
        model.quant_ramp = QuantRamp(0, args.ramp_end)

    train = load(args.data, "train")
    fit, holdout = train[: -args.holdout], train[-args.holdout :]
    stream = DataStream(fit, PILOT_BATCH, model.cfg.ctx, spec.seed)
    opt = _optimizer(model, spec)

    peak = spec.lr if args.lr is None else args.lr
    cd_start = args.steps - args.cooldown if args.cooldown else None
    rows = []
    start = time.monotonic()
    for step in range(args.steps):
        model.train()
        loss = _step(
            model,
            opt,
            stream,
            lr_at(step, args.warmup, peak, cd_start, args.cooldown),
            step=step,
            seed=spec.seed,
        )
        done = step + 1
        if done % args.every == 0 or done == args.steps:
            model.eval()
            with torch.no_grad():
                bpb, _ = sliding_bpb(model, holdout, args.holdout)
            ramp = model.quant_ramp
            rows.append(
                {
                    "step": done,
                    "partial_prob": 0.1 if ramp is None else ramp.at(step),
                    "train_loss_bits": loss / 0.6931471805599453,
                    "holdout_quantized_bpb": bpb,
                    "seconds": time.monotonic() - start,
                }
            )
            print(json.dumps(rows[-1]), flush=True)
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(
                json.dumps(
                    {
                        "kind": "vq-canary",
                        "arm": args.arm,
                        "seed": args.seed,
                        "ramp_end": args.ramp_end,
                        "lr": peak,
                        "cooldown": args.cooldown,
                        "not_a_result": True,
                        "rows": rows,
                    },
                    indent=1,
                )
            )


if __name__ == "__main__":
    main()
