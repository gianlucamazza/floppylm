"""Run ADR 0013 functional qualification, without validation/test or console jobs."""

import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def canary(learned, probability, cadence):
    from floppylm.vq import VectorBook, VectorCodec, pack_vectors

    torch.manual_seed(17)
    weight = torch.nn.Parameter(torch.randn(4, 16))
    target = torch.randn_like(weight)
    book = VectorBook(8, 0.5, 42, learned=learned)
    codec = VectorCodec(book)
    initial_book = book.values.detach().clone()
    parameters = [weight] + ([book.values] if learned else [])
    optimizer = torch.optim.AdamW(parameters, lr=0.001, weight_decay=0)
    symbols, _ = codec.encode(weight)
    snaps = 0
    # Exercise the longest declared cadence at least once in every recipe.
    for step in range(1, 258):
        optimizer.zero_grad(set_to_none=True)
        quantized = codec.partial_weight(weight, probability, step, symbols=symbols)
        loss = (quantized - target).square().mean()
        loss.backward()
        if not torch.isfinite(loss) or any(
            p.grad is None or not torch.isfinite(p.grad).all() for p in parameters
        ):
            raise RuntimeError("nonfinite or missing canary gradient")
        optimizer.step()
        if step % cadence == 0:
            symbols = codec.snap(weight)
            snaps += 1
    artifact, parts = pack_vectors({"weight": weight}, {"weight": codec})
    symbols, scales = codec.encode(weight)
    deployed = codec.decode(symbols, scales, tuple(weight.shape))
    return {
        "learned": learned,
        "probability": probability,
        "cadence": cadence,
        "steps": 257,
        "snaps": snaps,
        "artifact_sha256": hashlib.sha256(artifact).hexdigest(),
        "artifact_bytes": len(artifact),
        "parts": parts,
        "master_sha256": hashlib.sha256(weight.detach().numpy().tobytes()).hexdigest(),
        "book_changed": not torch.equal(book.values.detach(), initial_book),
        "fully_quantized_mse": float((deployed.detach() - target).square().mean()),
    }


def qualify(train, expected_sha256, out, threads):
    from floppylm import runlog
    from floppylm.bpe import ByteBPE
    from floppylm.vq import VectorBook, VectorCodec, pack_vectors, unpack_vectors

    sources = runlog.sources(ROOT)
    bound = [
        Path(__file__),
        ROOT / "docs/adr/0013-e1-functional-qualification.md",
        ROOT / "docs/e1-qualification-proposal.md",
    ]
    hashes = {str(p.relative_to(ROOT)): runlog.sha256_file(p) for p in bound}
    torch.set_num_threads(threads)
    started = time.perf_counter()
    train_hash = runlog.sha256_file(train)
    if train_hash != expected_sha256:
        raise RuntimeError("train differs from frozen input")
    with train.open("rb") as stream:
        prefix = stream.read(2 * 1024 * 1024)
    if len(prefix) != 2 * 1024 * 1024:
        raise RuntimeError("qualification requires the declared 2 MiB train prefix")
    out.mkdir(parents=True, exist_ok=False)
    began = time.perf_counter()
    bpe = ByteBPE.train(prefix)
    table = bpe.to_bytes()
    restored = ByteBPE.from_bytes(table)
    tokens = restored.encode(prefix)
    if restored.decode(tokens) != prefix:
        raise RuntimeError("train BPE round trip differs")
    probes = bytes(range(256)) + np.random.default_rng(19).bytes(65536)
    if restored.decode(restored.encode(probes)) != probes:
        raise RuntimeError("arbitrary-byte BPE round trip differs")
    (out / "bpe.json").write_bytes(table)
    (out / "train-prefix.u16").write_bytes(tokens.astype("<u2").tobytes())
    tokenizer = {
        "vocab": bpe.vocab,
        "qualified_v512": bpe.vocab == 512,
        "table_bytes": len(table),
        "table_sha256": hashlib.sha256(table).hexdigest(),
        "prefix_bytes": len(prefix),
        "prefix_sha256": hashlib.sha256(prefix).hexdigest(),
        "tokens": len(tokens),
        "bytes_per_token": len(prefix) / len(tokens),
        "token_stream_bytes": tokens.nbytes,
        "token_stream_sha256": runlog.sha256_file(out / "train-prefix.u16"),
        "seconds": time.perf_counter() - began,
        "round_trip_exact": True,
    }
    print(json.dumps({"tokenizer": tokenizer}), flush=True)
    weights = {"a": torch.from_numpy(np.random.default_rng(23).normal(size=(7, 33)).astype("f4"))}
    weights["a"][0].zero_()
    weights["b"] = weights["a"].clone()
    candidates = []
    for learned in (False, True):
        for dimension in (8, 16):
            for rate in (0.5, 0.75):
                book = VectorBook(dimension, rate, 42, learned=learned)
                for policy in ("row16", "row8log"):
                    began = time.perf_counter()
                    codec = VectorCodec(book, policy)
                    blob, parts = pack_vectors(weights, dict.fromkeys(weights, codec))
                    decoded = unpack_vectors(blob)
                    for name, weight in weights.items():
                        symbols, scales = codec.encode(weight)
                        expected = codec.decode(symbols, scales, tuple(weight.shape)).detach()
                        if not torch.equal(decoded[name], expected) or torch.count_nonzero(
                            decoded[name][0]
                        ):
                            raise RuntimeError("vector decode or zero row differs")
                    tag = f"{'learned' if learned else 'fixed'}-g{dimension}-r{rate}-{policy}"
                    (out / (tag + ".vqf")).write_bytes(blob)
                    # Book alone is a lower bound: passing it does not qualify a full model.
                    candidates.append(
                        {
                            "candidate": tag,
                            "dimension": dimension,
                            "rate": rate,
                            "learned": learned,
                            "policy": policy,
                            "levels": book.levels,
                            "bytes": len(blob),
                            "parts": parts,
                            "book_entry_bytes": book.levels * dimension * 2 if learned else 0,
                            "book_header_bytes": 16,
                            "book_exceeds_1_16_budget": parts["shared"] > 1375000 / 16,
                            "padded_weights": sum(
                                w.shape[0] * ((-w.shape[1]) % dimension) for w in weights.values()
                            ),
                            "indices": sum(
                                w.shape[0] * math.ceil(w.shape[1] / dimension)
                                for w in weights.values()
                            ),
                            "sha256": hashlib.sha256(blob).hexdigest(),
                            "reconstruction_exact": True,
                            "seconds": time.perf_counter() - began,
                        }
                    )
    recipes = []
    for learned in (False, True):
        for probability in (0.05, 0.1):
            for cadence in (16, 64, 256):
                began = time.perf_counter()
                first = canary(learned, probability, cadence)
                second = canary(learned, probability, cadence)
                if first != second or first["book_changed"] != learned:
                    raise RuntimeError("canary replay or codebook learning differs")
                recipes.append(
                    {**first, "repeat_exact": True, "seconds": time.perf_counter() - began}
                )
    if (
        sources["files"] != runlog.sources(ROOT)["files"]
        or any(hashes[str(p.relative_to(ROOT))] != runlog.sha256_file(p) for p in bound)
        or train_hash != runlog.sha256_file(train)
    ):
        raise RuntimeError("functional source/input changed during qualification")
    result = {
        "purpose": "functional",
        "adr": "0013",
        "backend": "cpu",
        "sources": sources,
        "qualification_hashes": hashes,
        "train": {"sha256": train_hash, "bytes": train.stat().st_size},
        "environment": runlog.environment(threads),
        "tokenizer": tokenizer,
        "vector_candidates": candidates,
        "canaries": recipes,
        "seconds": time.perf_counter() - started,
        "limits": [
            "No validation/test opened, no Xbox job submitted, no scientific E1 selection.",
            "Canaries use a 4x16 matrix, G8/r0.5/row16; "
            "other books have storage/decode probes only.",
            "Fixture sizes are not full-model byte feasibility; "
            "headers/scales/indices are all counted.",
            "Persistent assignment/checkpoint and dead-code policy "
            "await the scientific E1 protocol.",
        ],
    }
    runlog.write_json(out / "summary.json", result)
    print(
        json.dumps(
            {"candidates": len(candidates), "recipes": len(recipes), "seconds": result["seconds"]}
        ),
        flush=True,
    )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--train-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--threads", type=int, default=2)
    args = parser.parse_args()
    if args.threads < 1:
        parser.error("positive thread count required")
    qualify(args.train, args.train_sha256, args.out, args.threads)


if __name__ == "__main__":
    main()
