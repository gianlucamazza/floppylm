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
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import torch  # noqa: E402

from floppylm.data import load  # noqa: E402
from floppylm.e1_pilot import PILOT_BATCH, cell_plan, materialize_cell  # noqa: E402
from floppylm.e1_plan import TARGET_BYTES, _best_d_ff, vector_config  # noqa: E402
from floppylm.model import TinyGPT  # noqa: E402
from floppylm.pack import pack_sections, unpack  # noqa: E402
from floppylm.seed import seed_all  # noqa: E402
from floppylm.train import (  # noqa: E402
    DataStream,
    QuantRamp,
    _optimizer,
    _step,
    lr_at,
    sliding_bpb,
)
from floppylm.vq import VectorBook  # noqa: E402


def custom_model(
    group: int, d: int, n_layers: int, seed: int, d_ff: int | None = None
) -> TinyGPT | None:
    """Learned rate-0.5 book at a named shape, or None without an admissible d_ff.

    ADR 0024 decision 3 at this width and depth, unless d_ff names the ADR 0026 repair value.
    Reads no split and trains nothing.
    """
    if d_ff is None:
        book_spec = SimpleNamespace(rate=0.5, learned=True)
        shape = _best_d_ff(d, n_layers, book_spec, VectorBook(group, 0.5, 0, learned=True))
        if shape is None:
            return None
        d_ff = shape.d_ff
    seed_all(seed)
    return TinyGPT(vector_config(d, n_layers, d_ff), VectorBook(group, 0.5, seed, learned=True))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", required=True, help="pilot vq arm, e.g. vq-0.5-fixed")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--steps", type=int, default=800)
    ap.add_argument("--ramp-end", type=int, help="ramp to p=1 by this step; omit for constant 0.1")
    ap.add_argument("--lr", type=float, help="override the recipe learning rate")
    ap.add_argument("--cooldown", type=int, default=0, help="linear lr decay over the last steps")
    ap.add_argument("--assign-every", type=int, help="assignment cadence; omit for 64")
    ap.add_argument("--group", type=int, choices=(8, 16), help="learned rate-0.5 book; default 8")
    ap.add_argument("--shape-d", type=int, help="custom width for a learned book; default 256")
    ap.add_argument("--shape-layers", type=int, help="custom depth for a learned book; default 1")
    ap.add_argument("--shape-d-ff", type=int, help="ADR 0026 repair value; default closest file")
    ap.add_argument("--every", type=int, default=200)
    ap.add_argument("--warmup", type=int, default=64)
    ap.add_argument("--holdout", type=int, default=64 * 1024)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if (ROOT / "runs" / "e1-1-16").resolve() in args.out.resolve().parents:
        raise SystemExit("--out must stay outside runs/e1-1-16")
    for name in ("shape_d", "shape_layers", "shape_d_ff"):
        value = getattr(args, name)
        if value is not None and value <= 0:
            raise SystemExit(f"--{name.replace('_', '-')} must be positive")
    torch.set_num_threads(args.threads)

    index = next(
        i
        for i, cell in enumerate(cell_plan())
        if cell["arm"] == args.arm and cell["seed"] == args.seed and cell["core"] == "vq"
    )
    built = materialize_cell(index)
    model, spec = built["model"], built["spec"]
    custom = (args.group, args.shape_d, args.shape_layers, args.shape_d_ff)
    if any(value is not None for value in custom):
        if args.arm != "vq-0.5-learned":
            raise SystemExit("a custom shape needs arm vq-0.5-learned (ADR 0025, ADR 0026)")
        model = custom_model(
            args.group or 8,
            args.shape_d or 256,
            args.shape_layers or 1,
            args.seed,
            args.shape_d_ff,
        )
        if model is None:
            raise SystemExit("no admissible d_ff: this recipe does not run (ADR 0025, ADR 0026)")
    model.assign_every = args.assign_every
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
                        "group": args.group or 8,
                        "assign_every": args.assign_every or 64,
                        "d": model.cfg.d,
                        "n_layers": model.cfg.n_layers,
                        "d_ff": model.cfg.d_ff,
                        "not_a_result": True,
                        "rows": rows,
                    },
                    indent=1,
                )
            )

    # ADR 0025 decision 6: the file at T decides validity and scores as the artifact.
    blob, sections = pack_sections(model)
    artifact_bpb, _ = sliding_bpb(unpack(blob), holdout, args.holdout)
    final = {
        "packed_bytes": len(blob),
        "sections": sections,
        "within_window": abs(len(blob) - TARGET_BYTES) <= 0.01 * TARGET_BYTES,
        "artifact_holdout_bpb": artifact_bpb,
    }
    print(json.dumps(final), flush=True)
    record = json.loads(args.out.read_text())
    args.out.write_text(json.dumps({**record, "final": final}, indent=1))


if __name__ == "__main__":
    main()
