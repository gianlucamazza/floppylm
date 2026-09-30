import json
import struct

import pytest
import torch

from floppylm.codec import SCALE_POLICIES
from floppylm.model import GPTConfig, TinyGPT
from floppylm.pack import FormatError, pack, pack_sections, unpack

CASES = [
    {"core_fmt": f, "scale_policy": p} for f in ("ternary", "2bit", "4bit") for p in SCALE_POLICIES
] + [
    {"core_fmt": "ternary", "delta": 0.7, "mlp": "swiglu"},
    {"core_fmt": "2bit", "mlp": "relu2", "qk_norm": True},
]


def _model(**kw) -> TinyGPT:
    torch.manual_seed(0)
    base = dict(vocab=256, d=32, n_layers=2, n_heads=2, d_ff=80)
    return TinyGPT(GPTConfig(**(base | kw)))


@pytest.mark.parametrize("kw", CASES)
def test_roundtrip_is_byte_identical_with_equal_logits(kw: dict) -> None:
    m = _model(**kw).eval()
    blob, parts = pack_sections(m)
    assert sum(parts.values()) == len(blob)
    m2 = unpack(blob).eval()
    assert pack(m2) == blob
    assert pack_sections(m2)[1] == parts
    assert m2.cfg == m.cfg
    x = torch.randint(0, 256, (2, 16))
    assert torch.equal(m(x), m2(x))


def test_resave_does_not_requantize() -> None:
    m2 = unpack(pack(_model()))
    rec = m2.blocks[0].qkv.canonical
    assert rec is not None and pack(m2).count(rec) == 1


def test_counted_bytes_track_nominal_bits() -> None:
    m = _model()
    blob, parts = pack_sections(m)
    payload = 8 * (len(blob) - parts["header"])
    assert 0.95 < payload / m.nominal_bits() < 1.03


def _blob() -> bytes:
    return pack(_model())


def test_truncation_at_every_boundary_is_rejected() -> None:
    blob = _blob()
    for n in (0, 3, 5, 20, len(blob) // 2, len(blob) - 1):
        with pytest.raises(FormatError):
            unpack(blob[:n])


def test_trailing_bytes_rejected() -> None:
    with pytest.raises(FormatError, match="trailing"):
        unpack(_blob() + b"\0")


def test_bad_magic_and_headers_rejected() -> None:
    blob = _blob()
    (hlen,) = struct.unpack_from("<H", blob, 4)
    header = json.loads(blob[6 : 6 + hlen])

    def with_header(h: dict | bytes) -> bytes:
        raw = (
            h
            if isinstance(h, bytes)
            else json.dumps(h, separators=(",", ":"), sort_keys=True).encode()
        )
        return blob[:4] + struct.pack("<H", len(raw)) + raw + blob[6 + hlen :]

    with pytest.raises(FormatError, match="magic"):
        unpack(b"XXXX" + blob[4:])
    with pytest.raises(FormatError):
        unpack(with_header(b"{not json"))
    with pytest.raises(FormatError):
        unpack(with_header({**header, "extra": 1}))
    with pytest.raises(FormatError):
        unpack(with_header({**header, "d": -32}))
    with pytest.raises(FormatError):
        unpack(with_header({**header, "core_fmt": "7bit"}))
    with pytest.raises(FormatError):
        unpack(with_header(json.dumps(header, sort_keys=True).encode()))  # non-canonical spacing


def test_corrupt_stream_rejected() -> None:
    blob = bytearray(_blob())
    blob[-100] ^= 0xFF  # inside the last quantized record or norms
    blob2 = bytearray(_blob())
    blob2[200] ^= 0x55
    rejected = 0
    for b in (bytes(blob), bytes(blob2)):
        try:
            unpack(b)
        except FormatError:
            rejected += 1
    assert rejected >= 1
