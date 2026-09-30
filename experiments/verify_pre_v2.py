"""Verify pre-v2 FLP1 artifacts: byte-identical re-save and the recorded val bpb.

Usage: python experiments/verify_pre_v2.py <model.flp> [--val-bpb EXPECTED]
Re-evaluates with the pre-v2 protocol: non-overlapping windows of 257 bytes over the first
MiB of val.bin.
"""

import argparse
import hashlib
import math
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from floppylm.pack import pack, unpack

ap = argparse.ArgumentParser()
ap.add_argument("blob")
ap.add_argument("--val-bpb", type=float)
a = ap.parse_args()
b = Path(a.blob).read_bytes()
m = unpack(b).eval()
print("sha256", hashlib.sha256(b).hexdigest(), "resave_identical", pack(m) == b)
if a.val_bpb is not None:
    data = np.memmap(ROOT / "data/tinystories/val.bin", dtype=np.uint8, mode="r")
    ctx = m.cfg.ctx
    n = (1 << 20) // (ctx + 1)
    arr = torch.from_numpy(np.asarray(data[: n * (ctx + 1)]).astype(np.int64)).view(n, ctx + 1)
    tot = 0.0
    with torch.no_grad():
        for i in range(0, n, 64):
            c = arr[i : i + 64]
            loss = F.cross_entropy(m(c[:, :-1]).reshape(-1, 256), c[:, 1:].reshape(-1))
            tot += loss.item() / math.log(2) * c.size(0)
    print("val_bpb", tot / n, "expected", a.val_bpb, "match", abs(tot / n - a.val_bpb) < 1e-9)
