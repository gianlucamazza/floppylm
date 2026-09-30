from pathlib import Path

import torch

from floppylm.pack import pack, unpack

FIXTURE = Path(__file__).parent / "fixtures" / "flp1_smoke.flp"


def test_flp1_fixture_resaves_identically() -> None:
    blob = FIXTURE.read_bytes()
    m = unpack(blob)
    assert m.cfg.rule == "flp1"
    assert pack(m) == blob
    assert torch.isfinite(m(torch.randint(0, 256, (1, 16)))).all()
