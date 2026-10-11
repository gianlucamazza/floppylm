"""Stop the console app after a campaign completes or the lifecycle unit stops.

Runs the xbox-gpu-training host tool (gianlucamazza/xbox-gpu-training#46):

    python e0_console_lifecycle.py teardown
    python e0_console_lifecycle.py idle-gpu --when after

Settings come from `--lifecycle-config`, campaign.json `console_lifecycle.config`,
and environment variables. See docs/operations/e0-console-lifecycle.md. This
script never prints credentials. An unreachable tool or console is recorded and
does not raise.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from floppylm_xbox.console_lifecycle import (  # noqa: E402
    load_lifecycle_config,
    record_console_lifecycle,
    stop_console,
)


def teardown_campaign(
    root: Path,
    *,
    tool: Path | None = None,
    package: str = "",
    wait_seconds: float | None = None,
    config_path: Path | None = None,
    source: str = "execstop",
    run=None,
) -> dict:
    overrides = {}
    if tool is not None:
        overrides["tool"] = tool
    if package:
        overrides["package"] = package
    if wait_seconds is not None:
        overrides["teardown_wait_seconds"] = wait_seconds
    config = load_lifecycle_config(
        campaign_root=root, config_path=config_path, overrides=overrides or None
    )
    if not config.package:
        try:
            stored = json.loads((root / "campaign.json").read_text()).get("package")
        except (OSError, json.JSONDecodeError):
            stored = None
        if stored:
            config = replace(config, package=stored)
    kwargs = {"config": config}
    if run is not None:
        kwargs["run"] = run
    result = stop_console(**kwargs)
    record_console_lifecycle(
        root,
        {
            "source": source,
            "teardown": result["teardown"],
            "idle_gpu_after": result["idle_gpu_after"],
            "ok": result["ok"],
        },
    )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, required=True)
    parser.add_argument("--lifecycle-tool", type=Path, default=None)
    parser.add_argument("--lifecycle-config", type=Path, default=None)
    parser.add_argument("--package", default="")
    parser.add_argument("--wait-seconds", type=float, default=None)
    args = parser.parse_args(argv)
    result = teardown_campaign(
        args.campaign,
        tool=args.lifecycle_tool,
        package=args.package,
        wait_seconds=args.wait_seconds,
        config_path=args.lifecycle_config,
    )
    print(json.dumps(result, sort_keys=True, default=str), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
