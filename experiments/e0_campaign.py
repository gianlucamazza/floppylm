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
import os
import signal
import statistics
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from e0_v2 import (
    EVIDENCE,
    FULL_BUDGET_BITS,
    _summary,
    selection_branch,
    verified_branch,
)
from floppylm import parity, runlog, shapes
from floppylm.campaign_protocol import PROTOCOL_ADR, grid_configs, protocol_spec
from floppylm.campaign_report import attempt_record, baseline_complete
from floppylm.model import GPTConfig


class Campaign:
    def __init__(self, root: Path, acceptance: Path, benchmark: Path, *, recover: bool = False):
        self.root, self.acceptance = root, acceptance.resolve()
        self.recover_trials = recover
        self.child = None
        self.stop_signal = None
        self.launching = self.stopping = False
        proof, speed = json.loads(acceptance.read_text()), json.loads(benchmark.read_text())
        if not proof["ok"] or any(proof[k] != speed[k] for k in ("package", "commit")):
            raise RuntimeError("benchmark and acceptance must bind the same hardware package")
        root.mkdir(parents=True, exist_ok=True)
        self.lock = (root / "worker.lock").open("a")
        fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        self.path = root / "campaign.json"
        if self.path.exists():
            self.state = json.loads(self.path.read_text())
            if self.state.get("protocol_adr") != PROTOCOL_ADR:
                raise RuntimeError("campaign protocol differs; no implicit migration")
            if self.state["benchmark_sha256"] != runlog.sha256_file(benchmark):
                raise RuntimeError("campaign benchmark changed")
            if self.state["acceptance_sha256"] != runlog.sha256_file(acceptance):
                raise RuntimeError("campaign acceptance changed")
        else:
            self.state = {
                "schema": "floppylm.e0.campaign.v1",
                "protocol_adr": PROTOCOL_ADR,
                "sources": runlog.sources(ROOT),
                "id": runlog.new_run_id("e0"),
                "created": runlog.now(),
                "status": "running",
                "phase": "neutral-scale",
                "acceptance_sha256": runlog.sha256_file(acceptance),
                "benchmark_sha256": runlog.sha256_file(benchmark),
                "package": proof["package"],
                "commit": proof["commit"],
                "protocol": protocol_spec(),
                "trials": {},
                "decisions": {},
            }
            # Exclusive creation freezes choices before any scientific result.
            with self.path.open("x") as file:
                json.dump(self.state, file, indent=1)
        self.state.update(pid=os.getpid(), process_identity=runlog.process_identity())
        self.save()

    def event(self, event, **fields):
        record = {"at": runlog.now(), "event": event, **fields}
        with (self.root / "runtime-events.jsonl").open("a") as file:
            file.write(json.dumps(record, sort_keys=True) + "\n")
            file.flush()
            os.fsync(file.fileno())
        directory = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)

    def on_signal(self, signum, _frame):
        self.stop_signal = self.stop_signal or signum
        if not self.launching and not self.stopping:
            raise KeyboardInterrupt(f"signal {signum}")

    def run_command(self, command, **kwargs):
        """Keep the campaign lock until an explicitly interrupted child is reaped."""
        was_stopping = self.stopping
        try:
            self.launching = True
            try:
                self.child = subprocess.Popen(command, start_new_session=True, **kwargs)
            finally:
                self.launching = False
            if self.stop_signal is not None:
                raise KeyboardInterrupt(f"signal {self.stop_signal}")
            returncode = self.child.wait()
            if returncode:
                raise subprocess.CalledProcessError(returncode, command)
        except BaseException:
            self.stopping = True
            if self.child is not None and self.child.poll() is None:
                signum = self.stop_signal or signal.SIGTERM
                try:
                    self.state.update(status="stopping", child_pid=self.child.pid, signal=signum)
                    self.save()
                    self.event("child_stop_requested", pid=self.child.pid, signal=signum)
                finally:
                    # Even a journal/disk failure must not orphan the active child.
                    try:
                        os.killpg(self.child.pid, signum)
                    except ProcessLookupError:
                        pass
                    finally:
                        # Cancellation may persist a GPU checkpoint. Keep the lock
                        # until cleanup finishes; never escalate to automatic hard kill.
                        self.child.wait()
                self.event("child_reaped", pid=self.child.pid, returncode=self.child.returncode)
            raise
        finally:
            self.child = None
            self.stopping = was_stopping

    def run_managed(self):
        previous = {s: signal.signal(s, self.on_signal) for s in (signal.SIGINT, signal.SIGTERM)}
        try:
            self.state.update(
                status="running", pid=os.getpid(), process_identity=runlog.process_identity()
            )
            self.save()
            self.event("worker_started", process_identity=self.state["process_identity"])
            self.run()
        except BaseException as error:
            self.stopping = True
            self.state.update(status="stopped", error=repr(error), stopped=runlog.now())
            if self.stop_signal is not None:
                self.state["signal"] = self.stop_signal
            self.save()
            self.event("worker_stopped", error=repr(error), signal=self.stop_signal)
            self.report()
            raise
        finally:
            for signum, handler in previous.items():
                signal.signal(signum, handler)
            self.lock.close()

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
            str(self.state["protocol"]["batch"]),
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
                self.run_command(cmd, stdout=log, stderr=subprocess.STDOUT)
        if path.exists():
            partial = json.loads(path.read_text())
            if partial["status"] != "completed" and self.recover_trials:
                self.run_command(
                    [
                        sys.executable,
                        str(ROOT / "experiments/e0_v2.py"),
                        "--resume",
                        run_id,
                        "--xbox-acceptance",
                        str(self.acceptance),
                    ],
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
        eligible = parity.admissible(
            {"4T": selection_branch(summary)["model_bytes"]}, summary["target_bytes"]
        )[0]
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

    @staticmethod
    def _mean_bpb(summaries, branch):
        return statistics.fmean(s["branches"][branch]["val_bpb"] for s in summaries)

    @classmethod
    def rank_stable(cls, phase, valid):
        """Return the 4T winner index; raise if it is not a minimizer at T and 2T."""
        best = min(valid, key=lambda item: cls._mean_bpb(item[1], 2))[0]
        for branch, label in ((0, "T"), (1, "2T")):
            means = {index: cls._mean_bpb(group, branch) for index, group in valid}
            if means[best] != min(means.values()):
                raise RuntimeError(
                    f"{phase}: rank unstable: 4T winner is not a minimizer at {label}"
                )
        return best

    @classmethod
    def paired_rank_stable(cls, paired):
        def sign(value):
            return (value > 0) - (value < 0)

        delta_4t = cls._mean_bpb(paired["ternary"], 2) - cls._mean_bpb(paired["2bit"], 2)
        for branch, label in ((0, "T"), (1, "2T")):
            delta = cls._mean_bpb(paired["ternary"], branch) - cls._mean_bpb(paired["2bit"], branch)
            if sign(delta) != sign(delta_4t):
                raise RuntimeError(f"paired-seeds: rank unstable at {label}")

    def neutral(self, phase, candidates):
        self.state["phase"] = phase
        self.save()
        groups = []
        for index, cfg in enumerate(candidates):
            groups.append(
                [
                    self.trial(f"{phase}-{index}-{seed}", cfg, seed)
                    for seed in self.state["protocol"]["neutral_seeds"]
                ]
            )
        valid = [(index, group) for index, group in enumerate(groups) if self.comparable(group)]
        best = self.select_winner(phase, valid)
        self.state["decisions"][phase] = candidates[best].to_dict()
        self.save()
        return candidates[best]

    def select_winner(self, phase, candidates):
        """Every selecting phase uses the same byte and rank policy (ADR 0015)."""
        comparable = bool(candidates) and self.comparable(
            [s for _, group in candidates for s in group]
        )
        scores = [
            {
                "candidate": key,
                "run_ids": [s["run_id"] for s in group],
                "mean_val_bpb": [self._mean_bpb(group, i) for i in range(3)],
            }
            for key, group in candidates
        ]
        diagnostic = {"phase": phase, "byte_comparable": comparable, "scores": scores}
        self.state.setdefault("comparisons", {})[phase] = diagnostic
        self.save()
        if not comparable:
            raise RuntimeError(phase + ": candidates fail byte parity")
        try:
            return self.rank_stable(phase, candidates)
        except RuntimeError as error:
            self.state["instability"] = {**diagnostic, "error": str(error)}
            self.save()
            raise

    def report(self):
        trials = []
        for key, record in self.state["trials"].items():
            for run_id in (record["run_id"], record.get("repair_id")):
                if run_id is None:
                    continue
                path = EVIDENCE / "runs" / run_id / "summary.json"
                summary = json.loads(path.read_text()) if path.exists() else {}
                trials.append(attempt_record(key, record, run_id, summary))
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
            "comparisons": self.state.get("comparisons", {}),
            "instability": self.state.get("instability"),
        }
        frozen = final = None
        selection = self.state.get("selection")
        if selection:
            frozen_path = EVIDENCE / "selections" / (selection + ".json")
            if frozen_path.exists():
                frozen = json.loads(frozen_path.read_text())
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
        report["baseline_complete"] = baseline_complete(self.state, frozen, final)
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
            "This campaign establishes a scalar E0 baseline. Vector cores are outside E0."
            if report["baseline_complete"]
            else "Partial campaign evidence; no completed scalar E0 baseline.",
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
        protocol = self.state["protocol"]
        budget = FULL_BUDGET_BITS * protocol["budget_frac"]
        base = GPTConfig(
            d=protocol["neutral_width"],
            n_layers=protocol["neutral_layers"],
            n_heads=protocol["neutral_width"] // shapes.HEAD_DIM,
            ctx=protocol["ctx"],
        )
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
                protocol["lr"],
                protocol["ternary_delta"] if fmt == "ternary" else protocol["2bit_wd"],
            ):
                cfg = shapes.fill_d_ff(
                    replace(chosen, core_fmt=fmt, delta=axis if fmt == "ternary" else 0.5), budget
                )
                wd = protocol["ternary_wd"] if fmt == "ternary" else axis
                s = self.trial(f"tune-{fmt}-{lr}-{axis}", cfg, protocol["tuning_seed"], lr, wd)
                if s is not None:
                    candidates.append((s, lr, wd, cfg))
            winner = self.select_winner(
                "tuning-" + fmt, [(i, [c[0]]) for i, c in enumerate(candidates)]
            )
            _, lr, wd, cfg = candidates[winner]
            self.state["phase"] = "grid-" + fmt
            self.save()
            grid = [
                (self.trial(f"grid-{fmt}-{i}", c, protocol["grid_seed"], lr, wd), c)
                for i, c in enumerate(grid_configs(cfg, budget, protocol))
            ]
            valid = [(s, c) for s, c in grid if s is not None]
            winner = self.select_winner("grid-" + fmt, [(i, [s]) for i, (s, _) in enumerate(valid)])
            _, cfg = valid[winner]
            recipes[fmt] = (cfg, lr, wd)
            self.state["decisions"][fmt] = {"config": cfg.to_dict(), "lr": lr, "wd": wd}
            self.save()
        self.state["phase"] = "paired-seeds"
        self.save()
        paired = {
            fmt: [
                self.trial(f"paired-{fmt}-{seed}", cfg, seed, lr, wd)
                for seed in protocol["paired_seeds"]
            ]
            for fmt, (cfg, lr, wd) in recipes.items()
        }
        all_runs = [s for group in paired.values() for s in group]
        if not self.comparable(all_runs):
            raise RuntimeError("paired comparison fails byte parity")
        self.paired_rank_stable(paired)
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
            self.run_command(
                [
                    sys.executable,
                    str(ROOT / "experiments/e0_v2.py"),
                    "--freeze",
                    *[s["run_id"] for s in all_runs],
                    "--name",
                    name,
                ],
            )
        final = EVIDENCE / "selections" / (name + ".test.json")
        if not final.exists():
            self.run_command(
                [sys.executable, str(ROOT / "experiments/e0_v2.py"), "--final-test", name],
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
    campaign.run_managed()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
