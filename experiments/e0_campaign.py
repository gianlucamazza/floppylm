"""Sequential, preregistered Xbox E0 a-e campaign with durable trial identities.

Hardware acceptance and a representative throughput measurement are prerequisites.
A failed/interrupted trial stops the campaign; reopening never silently retrains it.
Test is opened once, after all ten selected paired-seed artifacts are frozen.
"""

from __future__ import annotations

import argparse
import fcntl
import itertools
import json
import statistics
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from e0_v2 import EVIDENCE, FULL_BUDGET_BITS, _summary, selection_branch, verified_branch
from floppylm import parity, runlog, shapes
from floppylm.model import GPTConfig


class Campaign:
    def __init__(self, root: Path, acceptance: Path, benchmark: Path, *, recover: bool = False):
        self.root, self.acceptance = root, acceptance.resolve()
        self.recover_trials = recover
        proof, speed = json.loads(acceptance.read_text()), json.loads(benchmark.read_text())
        if not proof["ok"] or any(proof[k] != speed[k] for k in ("package", "commit")):
            raise RuntimeError("benchmark and acceptance must bind the same hardware package")
        root.mkdir(parents=True, exist_ok=True)
        self.lock = (root / "worker.lock").open("a")
        fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        self.path = root / "campaign.json"
        if self.path.exists():
            self.state = json.loads(self.path.read_text())
            if self.state.get("protocol_adr") != "0011":
                raise RuntimeError("campaign protocol differs; no implicit migration")
            if self.state["benchmark_sha256"] != runlog.sha256_file(benchmark):
                raise RuntimeError("campaign benchmark changed")
            if self.state["acceptance_sha256"] != runlog.sha256_file(acceptance):
                raise RuntimeError("campaign acceptance changed")
        else:
            self.state = {
                "schema": "floppylm.e0.campaign.v1",
                "protocol_adr": "0011",
                "sources": runlog.sources(ROOT),
                "id": runlog.new_run_id("e0"),
                "created": runlog.now(),
                "status": "running",
                "phase": "neutral-scale",
                "acceptance_sha256": runlog.sha256_file(acceptance),
                "benchmark_sha256": runlog.sha256_file(benchmark),
                "package": proof["package"],
                "commit": proof["commit"],
                "protocol": {
                    "budget_frac": 1 / 16,
                    "neutral_width": 96,
                    "neutral_layers": 3,
                    "neutral_seeds": [0, 1],
                    "tuning_seed": 0,
                    "grid_seed": 0,
                    "paired_seeds": list(range(5)),
                    "batch": 32,
                    "ctx": 256,
                    "scale_order": ["row16", "row8log"],
                    "mlp_order": ["gelu", "swiglu", "relu2"],
                    "lr": [0.001, 0.003, 0.01],
                    "ternary_delta": [0.5, 0.7],
                    "ternary_wd": 0.1,
                    "2bit_wd": [0, 0.1],
                    "grid_widths": list(range(64, 257, 16)),
                    "grid_layers": list(range(1, 17)),
                    "grid_ff_range": [2.0, 6.0],
                    "grid_embedding_share": [0.08, 0.20],
                    "grid_min_nominal_fill": 0.995,
                    "selection": "minimum mean 4T val bpb; declared enumeration order breaks ties",
                    "eligibility": "actual individual and reciprocal byte parity; saturation at 4T",
                    "byte_repair": "at most one fresh attempt per trial, preserving recipe",
                },
                "trials": {},
                "decisions": {},
            }
            # Exclusive creation freezes choices before any scientific result.
            with self.path.open("x") as file:
                json.dump(self.state, file, indent=1)
        self.save()

    def save(self):
        runlog.write_json(self.path, self.state)

    def command(self, run_id, cfg, seed, lr=0.003, wd=0.1, retry=None):
        cmd = [
            sys.executable,
            "-u",
            str(ROOT / "experiments/e0_v2.py"),
            "--run-id",
            run_id,
            "--backend",
            "xbox",
            "--xbox-acceptance",
            str(self.acceptance),
            "--threads",
            "2",
        ]
        if retry:
            return cmd + ["--retry", retry]
        cmd += [
            "--run",
            "--d",
            str(cfg.d),
            "--layers",
            str(cfg.n_layers),
            "--d-ff",
            str(cfg.d_ff),
            "--fmt",
            cfg.core_fmt,
            "--mlp",
            cfg.mlp,
            "--scale-policy",
            cfg.scale_policy,
            "--delta",
            str(cfg.delta),
            "--ctx",
            str(cfg.ctx),
            "--seed",
            str(seed),
            "--batch",
            "32",
            "--lr",
            str(lr),
            "--wd",
            str(wd),
        ]
        return cmd + (["--qk-norm"] if cfg.qk_norm else [])

    def execute(self, run_id, cmd):
        path = EVIDENCE / "runs" / run_id / "summary.json"
        if not path.exists():
            with (self.root / (run_id + ".log")).open("x") as log:
                subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, check=True)
        if path.exists():
            partial = json.loads(path.read_text())
            if partial["status"] != "completed" and self.recover_trials:
                subprocess.run(
                    [
                        sys.executable,
                        str(ROOT / "experiments/e0_v2.py"),
                        "--resume",
                        run_id,
                        "--xbox-acceptance",
                        str(self.acceptance),
                    ],
                    check=True,
                )
        summary = _summary(run_id)
        if summary.get("backend_name") != "xbox" or not summary.get("backend", {}).get(
            "hardware_gpu"
        ):
            raise RuntimeError("campaign trial lacks hardware provenance")
        verified_branch(selection_branch(summary))
        return summary

    def trial(self, key, cfg, seed, lr=0.003, wd=0.1):
        if runlog.sources(ROOT)["files"] != self.state["sources"]["files"]:
            raise RuntimeError("campaign implementation changed after preregistration")
        record = self.state["trials"].get(key)
        recipe = {"config": cfg.to_dict(), "seed": seed, "lr": lr, "wd": wd}
        if record is None:
            record = {
                "run_id": self.state["id"] + f"-{len(self.state['trials']):03d}",
                "recipe": recipe,
                "status": "reserved",
            }
            self.state["trials"][key] = record
            self.save()
        elif record["recipe"] != recipe:
            raise RuntimeError("reserved trial recipe changed")
        if record["status"] == "excluded-byte-repair":
            return None
        summary = self.execute(record["run_id"], self.command(record["run_id"], cfg, seed, lr, wd))
        if not parity.admissible(
            {"trial": selection_branch(summary)["model_bytes"]}, summary["target_bytes"]
        )[0]:
            if "repair_id" not in record:
                record["repair_id"] = record["run_id"] + "-repair"
                self.save()
            try:
                summary = self.execute(
                    record["repair_id"],
                    self.command(record["repair_id"], cfg, seed, lr, wd, retry=record["run_id"]),
                )
            except subprocess.CalledProcessError:
                # Only declared solver exclusions are admissible; training failures stop.
                log = (self.root / (record["repair_id"] + ".log")).read_text()
                if "S3 adjustment excluded:" not in log:
                    raise
                record["status"] = "excluded-byte-repair"
                self.save()
                return None
        eligible = (
            parity.admissible(
                {"4T": selection_branch(summary)["model_bytes"]}, summary["target_bytes"]
            )[0]
            and summary["saturation"]["verdict"] == "saturo"
        )
        record.update(status="eligible" if eligible else "excluded", result=summary["run_id"])
        self.save()
        return summary if eligible else None

    @staticmethod
    def comparable(summaries):
        if any(s is None for s in summaries):
            return False
        return parity.admissible(
            {s["run_id"]: selection_branch(s)["model_bytes"] for s in summaries},
            summaries[0]["target_bytes"],
        )[0]

    def neutral(self, phase, candidates):
        self.state["phase"] = phase
        self.save()
        groups = []
        for index, cfg in enumerate(candidates):
            groups.append([self.trial(f"{phase}-{index}-{seed}", cfg, seed) for seed in (0, 1)])
        valid = [(index, group) for index, group in enumerate(groups) if self.comparable(group)]
        if not valid or not self.comparable([s for _, group in valid for s in group]):
            raise RuntimeError(phase + ": neutral candidates do not meet byte/saturation gates")
        best = min(
            valid,
            key=lambda item: statistics.fmean(selection_branch(s)["val_bpb"] for s in item[1]),
        )[0]
        self.state["decisions"][phase] = candidates[best].to_dict()
        self.save()
        return candidates[best]

    def report(self):
        trials = []
        for key, record in self.state["trials"].items():
            for run_id in (record["run_id"], record.get("repair_id")):
                if run_id is None:
                    continue
                path = EVIDENCE / "runs" / run_id / "summary.json"
                summary = json.loads(path.read_text()) if path.exists() else {}
                trials.append(
                    {
                        "key": key,
                        "run_id": run_id,
                        "status": summary.get("status", "reserved"),
                        "eligibility": record["status"],
                        "compute": summary.get("compute"),
                        "saturation": summary.get("saturation"),
                        "recipe": record["recipe"],
                    }
                )
        costs = [r["compute"] for r in trials if r["compute"] is not None]
        report = {
            "campaign": self.state["id"],
            "status": self.state["status"],
            "package": self.state["package"],
            "commit": self.state["commit"],
            "trials": trials,
            "original_trials": len(self.state["trials"]),
            "repair_trials": sum("repair_id" in r for r in self.state["trials"].values()),
            "cost": {
                k: sum(c.get(k) or 0 for c in costs)
                for k in (
                    "total_tokens",
                    "total_flops",
                    "wall_seconds",
                    "eval_seconds",
                    "native_execution_seconds",
                )
            },
            "cost_scope": "completed trial compute; host wall per recorded host attempt",
            "cost_unavailable_trials": [r["run_id"] for r in trials if r["compute"] is None],
            "validation_paired": self.state.get("paired"),
            "decisions": self.state["decisions"],
        }
        selection = self.state.get("selection")
        if selection:
            path = EVIDENCE / "selections" / (selection + ".test.json")
            if path.exists():
                final = json.loads(path.read_text())
                scores = {"ternary": {}, "2bit": {}}
                for item in final["results"]:
                    trial = _summary(item["run_id"])
                    scores[trial["config"]["core_fmt"]][trial["spec"]["seed"]] = item["test_bpb"]
                report["test_paired"] = parity.paired_sigma(scores["ternary"], scores["2bit"])
                report["frozen_gate_bpb"] = self.state["paired"]["gate_bpb"]
                report["selection_sha256"] = runlog.sha256_file(
                    EVIDENCE / "selections" / (selection + ".json")
                )
                report["test_report_sha256"] = runlog.sha256_file(path)
        runlog.write_json(self.root / "summary.json", report)
        destination = EVIDENCE / "campaigns" / self.state["id"]
        destination.mkdir(parents=True, exist_ok=True)
        runlog.write_json(destination / "summary.json", report)
        runlog.write_json(destination / "campaign.json", self.state)
        lines = [
            "# " + self.state["id"],
            "",
            "Status: **" + self.state["status"] + "**.",
            "",
            f"Trials: {report['original_trials']}; byte repairs: {report['repair_trials']}.",
            "Costs, exclusions, recipes and hashes are in summary.json.",
            "This campaign establishes a scalar E0 baseline. Vector cores are outside E0.",
        ]
        if "test_paired" in report:
            lines += [
                "",
                f"Test paired ternary minus 2bit bpb: {report['test_paired']['mean']:.6f}; "
                f"sample SD {report['test_paired']['sd']:.6f}; frozen validation gate "
                f"{report['frozen_gate_bpb']:.6f}.",
            ]
        runlog.write_atomic(destination / "notes.md", "\n".join(lines) + "\n")

    def run(self):
        budget = FULL_BUDGET_BITS / 16
        base = GPTConfig(d=96, n_layers=3, n_heads=6, ctx=256)
        scale = self.neutral(
            "neutral-scale",
            [
                shapes.fill_d_ff(replace(base, scale_policy=p), budget)
                for p in self.state["protocol"]["scale_order"]
            ],
        )
        chosen = self.neutral(
            "neutral-mlp",
            [
                shapes.fill_d_ff(replace(scale, mlp=m), budget)
                for m in self.state["protocol"]["mlp_order"]
            ],
        )
        recipes = {}
        for fmt in ("ternary", "2bit"):
            self.state["phase"] = "tuning-" + fmt
            self.save()
            candidates = []
            for lr, axis in itertools.product(
                (0.001, 0.003, 0.01), (0.5, 0.7) if fmt == "ternary" else (0, 0.1)
            ):
                cfg = shapes.fill_d_ff(
                    replace(chosen, core_fmt=fmt, delta=axis if fmt == "ternary" else 0.5), budget
                )
                wd = 0.1 if fmt == "ternary" else axis
                s = self.trial(f"tune-{fmt}-{lr}-{axis}", cfg, 0, lr, wd)
                if s is not None:
                    candidates.append((s, lr, wd, cfg))
            if not candidates or not self.comparable([c[0] for c in candidates]):
                raise RuntimeError("tuning candidates fail comparison gates")
            _, lr, wd, cfg = min(candidates, key=lambda c: selection_branch(c[0])["val_bpb"])
            self.state["phase"] = "grid-" + fmt
            self.save()
            grid = [
                (self.trial(f"grid-{fmt}-{i}", c, 0, lr, wd), c)
                for i, c in enumerate(shapes.grid(cfg, budget))
            ]
            valid = [(s, c) for s, c in grid if s is not None]
            if not valid or not self.comparable([s for s, _ in valid]):
                raise RuntimeError("grid candidates fail comparison gates")
            _, cfg = min(valid, key=lambda item: selection_branch(item[0])["val_bpb"])
            recipes[fmt] = (cfg, lr, wd)
            self.state["decisions"][fmt] = {"config": cfg.to_dict(), "lr": lr, "wd": wd}
            self.save()
        self.state["phase"] = "paired-seeds"
        self.save()
        paired = {
            fmt: [self.trial(f"paired-{fmt}-{seed}", cfg, seed, lr, wd) for seed in range(5)]
            for fmt, (cfg, lr, wd) in recipes.items()
        }
        all_runs = [s for group in paired.values() for s in group]
        if not self.comparable(all_runs):
            raise RuntimeError("paired comparison fails byte/saturation gates")
        sigma = parity.paired_sigma(
            *[
                {seed: selection_branch(s)["val_bpb"] for seed, s in enumerate(paired[fmt])}
                for fmt in ("ternary", "2bit")
            ]
        )
        self.state["paired"] = {**sigma, "gate_bpb": max(0.02, 2 * sigma["sd"])}
        name = self.state["id"]
        selection = EVIDENCE / "selections" / (name + ".json")
        if not selection.exists():
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "experiments/e0_v2.py"),
                    "--freeze",
                    *[s["run_id"] for s in all_runs],
                    "--name",
                    name,
                ],
                check=True,
            )
        final = EVIDENCE / "selections" / (name + ".test.json")
        if not final.exists():
            subprocess.run(
                [sys.executable, str(ROOT / "experiments/e0_v2.py"), "--final-test", name],
                check=True,
            )
        self.state.update(
            status="completed", phase="completed", finished=runlog.now(), selection=name
        )
        self.save()
        self.report()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--acceptance", type=Path, required=True)
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--recover", action="store_true", help="recover existing bound trials")
    a = parser.parse_args()
    campaign = Campaign(a.out, a.acceptance, a.benchmark, recover=a.recover)
    try:
        campaign.run()
    except BaseException as error:
        campaign.state.update(status="stopped", error=repr(error), stopped=runlog.now())
        campaign.save()
        campaign.report()
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
