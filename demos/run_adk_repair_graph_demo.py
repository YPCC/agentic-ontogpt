#!/usr/bin/env python3
"""Showcase multi-iteration repair on ADK graph patterns — not pipeline.agent."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-iterations", type=int, default=3)
    args = ap.parse_args()

    from agents.graph_repair import (
        adk_available,
        build_dynamic_repair_orchestrator,
        build_workflow_with_repair_gate,
        describe_patterns,
        make_repair_gate,
    )

    print("=== Patterns (product pipeline unchanged) ===")
    for k, v in describe_patterns().items():
        print(f"\n[{k}]\n  {v}")

    print("\n=== Gate unit demo (no ADK required) ===")
    gate = make_repair_gate(max_iterations=args.max_iterations)
    for sample in (
        {"valid": False, "iteration": 1},
        {"valid": False, "iteration": args.max_iterations},
        {"valid": True, "iteration": 2},
    ):
        out = gate(sample)
        route = out.get("route") if isinstance(out, dict) else getattr(out, "route", out)
        print(f"  input={sample} → route={route}")

    print(f"\n=== ADK available: {adk_available()} ===")
    _, dyn_info = build_dynamic_repair_orchestrator(max_iterations=args.max_iterations)
    print("\n--- Dynamic repair ---")
    print(json.dumps({k: v for k, v in dyn_info.items() if k not in ("orchestrator_fn", "generator", "validator")}, indent=2))

    wf_root, wf_info = build_workflow_with_repair_gate(max_iterations=args.max_iterations)
    print("\n--- Workflow + repair gate ---")
    print(json.dumps({k: v for k, v in wf_info.items() if k != "gate"}, indent=2))
    if wf_root is not None:
        print(f"  materialised: {type(wf_root).__name__}")

    print("\nProduct path still: adk run agents/pipeline (LoopAgent). Showcase only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
