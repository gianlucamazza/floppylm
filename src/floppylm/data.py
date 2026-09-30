"""TinyStories: stream stories, exact dedup, deterministic hash split, byte files."""

import hashlib
import io
from collections.abc import Iterable, Iterator
from pathlib import Path

import numpy as np

EOT = "<|endoftext|>"
SEP = b"\x03"  # story separator byte; removed from story text


def stories(src: str | Iterable[str]) -> Iterator[str]:
    lines = io.StringIO(src) if isinstance(src, str) else src
    seen: set[bytes] = set()
    buf: list[str] = []

    def flush() -> Iterator[str]:
        text = "".join(buf).strip().replace("\x03", "")
        buf.clear()
        h = hashlib.sha1(text.encode()).digest()
        if text and h not in seen:
            seen.add(h)
            yield text

    for line in lines:
        if line.strip() == EOT:
            yield from flush()
        else:
            buf.append(line)
    yield from flush()


def split_of(text: str) -> str:
    h = int.from_bytes(hashlib.sha1(text.encode()).digest()[:8], "little") % 1000
    return "test" if h < 10 else ("val" if h < 20 else "train")


def prepare(raw_files: list[Path], out_dir: Path) -> dict[str, int]:
    """Merge files, dedup across them, write {train,val,test}.bin; return story counts."""
    out_dir.mkdir(parents=True, exist_ok=True)
    fh = {s: open(out_dir / f"{s}.bin", "wb") for s in ("train", "val", "test")}
    counts = dict.fromkeys(fh, 0)

    def all_lines() -> Iterator[str]:
        for p in raw_files:
            with open(p, encoding="utf-8", errors="replace") as f:
                yield from f
                yield EOT + "\n"

    for text in stories(all_lines()):
        s = split_of(text)
        fh[s].write(text.encode() + SEP)
        counts[s] += 1
    for f in fh.values():
        f.close()
    return counts


def load(out_dir: Path, split: str) -> np.memmap:
    return np.memmap(out_dir / f"{split}.bin", dtype=np.uint8, mode="r")
