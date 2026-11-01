"""Tiny GPT whose every stored number goes through a codec or an fp16 round trip."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass

import torch
import torch.nn as nn
import torch.nn.functional as F

from .codec import SCALE_POLICIES, ScalarCodec, scalar
from .vq import VectorBook, VectorCodec

MLPS = ("gelu", "relu2", "swiglu")
ROPE_THETA = 10000.0
RMSNORM_EPS = float(torch.finfo(torch.float32).eps)  # torch default, stated explicitly
GELU_APPROXIMATE = "none"  # exact erf form
FORMATS = ("ternary", "2bit", "4bit")  # E0 scalar formats; the vq core is not one of them
CORE_FORMATS = (*FORMATS, "vq")


@dataclass(frozen=True)
class GPTConfig:
    vocab: int = 256
    d: int = 96
    n_layers: int = 3
    n_heads: int = 6
    d_ff: int = 384
    mlp: str = "gelu"  # gelu | relu2 | swiglu
    core_fmt: str = "ternary"
    emb_fmt: str = "4bit"
    scale_policy: str = "row16"
    delta: float = 0.5
    qk_norm: bool = False
    ctx: int = 256

    def __post_init__(self) -> None:
        ints = ("vocab", "d", "n_layers", "n_heads", "d_ff", "ctx")
        if not all(isinstance(getattr(self, k), int) and getattr(self, k) > 0 for k in ints):
            raise ValueError(f"config sizes must be positive ints: {self}")
        if self.d % self.n_heads or (self.d // self.n_heads) % 2:
            raise ValueError("d must split into heads of even size")
        if self.mlp not in MLPS or self.core_fmt not in CORE_FORMATS or self.emb_fmt not in FORMATS:
            raise ValueError(f"unknown mlp or format: {self}")
        if self.core_fmt == "vq" and (self.emb_fmt != "4bit" or self.scale_policy != "row8log"):
            raise ValueError("vq core uses a 4-bit embedding and row8log scales")
        if self.scale_policy not in SCALE_POLICIES:
            raise ValueError(f"unknown scale policy: {self}")
        if not (0 <= self.delta < 4) or not isinstance(self.qk_norm, bool):
            raise ValueError(f"invalid delta or qk_norm: {self}")
        if self.vocab > 65535 or self.ctx > 1 << 16 or self.n_layers > 255 or self.d > 65535:
            raise ValueError(f"config out of serializable range: {self}")

    def to_dict(self) -> dict:
        return asdict(self)

    def tensor_shapes(self) -> list[tuple[str, tuple[int, ...]]]:
        """Stored tensors in serialization order: ("q", (rows, cols)) or ("n", (d,))."""
        d, f = self.d, self.d_ff
        up = 2 * f if self.mlp == "swiglu" else f
        block = [
            ("n", (d,)),
            ("q", (3 * d, d)),
            ("q", (d, d)),
            ("n", (d,)),
            ("q", (up, d)),
            ("q", (d, f)),
        ]
        return [("q", (self.vocab, d))] + block * self.n_layers + [("n", (d,))]

    def codecs(self) -> tuple[ScalarCodec, ScalarCodec]:
        """(embedding codec, core codec). A vq core needs the shared book on the model."""
        if self.core_fmt == "vq":
            raise ValueError("vq core codec needs the shared book; construct TinyGPT")
        emb = scalar(self.emb_fmt, self.scale_policy)
        return emb, scalar(self.core_fmt, self.scale_policy, self.delta)

    def nominal_bits(self) -> float:
        if self.core_fmt == "vq":
            raise ValueError("vq nominal bits include the shared book; ask the model")
        emb, core = self.codecs()
        bits = 0.0
        for i, (kind, shape) in enumerate(self.tensor_shapes()):
            if kind == "n":
                bits += 16 * shape[0]
            else:
                bits += (emb if i == 0 else core).nominal_bits(shape)
        return bits


def _fp16(w: torch.Tensor) -> torch.Tensor:
    return w.detach().half().float() + (w - w.detach())


class QLinear(nn.Module):
    """Linear layer whose weight is always the codec's reconstruction (frozen after unpack)."""

    def __init__(self, d_in: int, d_out: int, codec: ScalarCodec | VectorCodec, std: float) -> None:
        super().__init__()
        self.codec = codec
        self.frozen = False
        self.canonical: bytes | None = None  # exact stored record after unpack; re-saved verbatim
        self.assignment: tuple | None = None  # (symbols, scale bytes) held between vq cadence steps
        self.weight = nn.Parameter(torch.randn(d_out, d_in) * std)

    def qweight(self) -> torch.Tensor:
        if self.frozen:
            return self.weight
        # No held assignment: full fake-quant, including every scalar matrix.
        if self.assignment is None:
            return self.codec.weight(self.weight)
        # Held indices are the ADR 0023 assignment. Eval uses every group.
        # Training uses the partial mask stored by the prepared step.
        symbols, scale_bytes = self.assignment
        probability = 1.0 if not self.training else getattr(self, "_partial_prob", None)
        seed = 0 if not self.training else getattr(self, "_mask_seed", None)
        if probability is None or seed is None:
            raise RuntimeError("vq training forward has no prepared step")
        return self.codec.partial_weight(
            self.weight, probability, seed, symbols=symbols, scale_bytes=scale_bytes
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return F.linear(x, self.qweight())


class RMSNorm(nn.Module):
    def __init__(self, d: int) -> None:
        super().__init__()
        self.weight = nn.Parameter(torch.ones(d))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return F.rms_norm(x, (x.size(-1),), eps=RMSNORM_EPS) * _fp16(self.weight)


class Rope(nn.Module):
    def __init__(self, head_dim: int, ctx: int) -> None:
        super().__init__()
        inv = 1.0 / (ROPE_THETA ** (torch.arange(0, head_dim, 2, dtype=torch.float32) / head_dim))
        ang = torch.arange(ctx, dtype=torch.float32)[:, None] * inv[None]
        self.register_buffer("cos", ang.cos(), persistent=False)
        self.register_buffer("sin", ang.sin(), persistent=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        t = x.size(-2)
        cos, sin = self.cos[:t], self.sin[:t]
        x1, x2 = x[..., ::2], x[..., 1::2]
        return torch.stack((x1 * cos - x2 * sin, x1 * sin + x2 * cos), -1).flatten(-2)


class Block(nn.Module):
    def __init__(self, cfg: GPTConfig, codec: ScalarCodec | VectorCodec, rope: Rope) -> None:
        super().__init__()
        d, f = cfg.d, cfg.d_ff
        out_std = 1 / math.sqrt(2 * cfg.n_layers)
        self.cfg, self.rope = cfg, rope
        self.norm1, self.norm2 = RMSNorm(d), RMSNorm(d)
        self.qkv = QLinear(d, 3 * d, codec, 1 / math.sqrt(d))
        self.proj = QLinear(d, d, codec, out_std / math.sqrt(d))
        up = 2 * f if cfg.mlp == "swiglu" else f
        self.fc = QLinear(d, up, codec, 1 / math.sqrt(d))
        self.fc2 = QLinear(f, d, codec, out_std / math.sqrt(f))

    def _mlp(self, x: torch.Tensor) -> torch.Tensor:
        h = self.fc(x)
        if self.cfg.mlp == "swiglu":
            a, b = h.chunk(2, -1)
            h = F.silu(a) * b
        elif self.cfg.mlp == "relu2":
            h = F.relu(h).square()
        else:
            h = F.gelu(h, approximate=GELU_APPROXIMATE)
        return self.fc2(h)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        b, t, d = x.shape
        q, k, v = self.qkv(self.norm1(x)).split(d, -1)
        q, k, v = (z.view(b, t, self.cfg.n_heads, -1).transpose(1, 2) for z in (q, k, v))
        if self.cfg.qk_norm:
            q, k = F.rms_norm(q, (q.size(-1),)), F.rms_norm(k, (k.size(-1),))
        a = F.scaled_dot_product_attention(self.rope(q), self.rope(k), v, is_causal=True)
        x = x + self.proj(a.transpose(1, 2).reshape(b, t, d))
        return x + self._mlp(self.norm2(x))


class TinyGPT(nn.Module):
    def __init__(self, cfg: GPTConfig, book: VectorBook | None = None) -> None:
        super().__init__()
        assert cfg.d % cfg.n_heads == 0
        self.cfg = cfg
        self.quant_ramp = None  # train.QuantRamp on a diagnostic run; None is ADR 0023 decision 7
        # The book is not a GPTConfig field. ADR 0023 puts one VQB1 in the FLP2
        # shared section; delta stays in the header and the vector core ignores it.
        if cfg.core_fmt == "vq":
            if not isinstance(book, VectorBook):
                raise ValueError("vq core requires one VectorBook")
            self.book: VectorBook | None = book
            emb = scalar(cfg.emb_fmt, cfg.scale_policy)
            core: ScalarCodec | VectorCodec = VectorCodec(book, "row8log")
            # Cadence state is not a config field and not a stored result.
            self.reseed_log: list[dict] = []
            self.assigned_at: int | None = None
        else:
            if book is not None:
                raise ValueError("scalar core carries no book")
            self.book = None
            emb, core = cfg.codecs()
        rope = Rope(cfg.d // cfg.n_heads, cfg.ctx)
        self.emb = QLinear(cfg.d, cfg.vocab, emb, 1 / math.sqrt(cfg.d))  # (vocab, d), tied
        self.blocks = nn.ModuleList(Block(cfg, core, rope) for _ in range(cfg.n_layers))
        self.norm = RMSNorm(cfg.d)

    def forward(self, idx: torch.Tensor) -> torch.Tensor:
        w = self.emb.qweight()
        x = F.embedding(idx, w)
        for blk in self.blocks:
            x = blk(x)
        return F.linear(self.norm(x), w)

    def train(self, mode: bool = True):
        if mode and hasattr(self, "_artifact_state"):
            raise RuntimeError("Loaded FLP2 models are inference-only; resume a trunk checkpoint")
        return super().train(mode)

    def stored_tensors(self) -> list[QLinear | RMSNorm]:
        """Fixed serialization order."""
        out: list[QLinear | RMSNorm] = [self.emb]
        for b in self.blocks:
            out += [b.norm1, b.qkv, b.proj, b.norm2, b.fc, b.fc2]
        return out + [self.norm]

    def shared_section(self) -> bytes:
        """One VQB1 book, or empty for a scalar core. Not once per matrix."""
        return b"" if self.book is None else self.book.to_bytes()

    def nominal_bits(self) -> float:
        if self.book is None:
            return self.cfg.nominal_bits()
        bits = 8 * len(self.shared_section())
        emb = scalar(self.cfg.emb_fmt, self.cfg.scale_policy)
        core = VectorCodec(self.book, "row8log")
        for i, (kind, shape) in enumerate(self.cfg.tensor_shapes()):
            if kind == "n":
                bits += 16 * shape[0]
            else:
                bits += (emb if i == 0 else core).nominal_bits(shape)
        return bits

    def stored_params(self) -> int:
        n = sum(t.weight.numel() for t in self.stored_tensors() if isinstance(t, QLinear))
        if self.book is not None and self.book.learned:
            n += self.book.values.numel()
        return n

    def core_params(self) -> int:
        return self.stored_params() - self.emb.weight.numel()

    def flops_per_token(self) -> float:
        """Forward FLOPs per token: linear layers + attention scores/values (causal ~ctx/2)."""
        c = self.cfg
        attn = 2 * 2 * c.n_layers * (c.ctx / 2) * c.d
        return 2 * self.stored_params() + attn
