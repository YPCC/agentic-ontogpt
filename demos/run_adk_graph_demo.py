#!/usr/bin/env python3
"""Showcase: registry + graph assembly (does NOT load agents.pipeline.agent).

Original product path: adk run agents/pipeline
This demo only proves build_* factories compose into an ADK-ready root.

Usage::

    python demos/run_adk_graph_demo.py
"""

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
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    from agents.registry import AGENT_META, list_agents
    from agents.graph_workflow import (
        adk_available,
        build_control_plane_from_registry,
        workflow_api_available,
    )

    print("=== Agent registry (factories) ===")
    for name in list_agents():
        meta = AGENT_META.get(name, {})
        print(f"  - {name}: {meta.get('role', '')} [{meta.get('kind', '?')}]")

    print("\n=== Runtime capability ===")
    print(f"  google-adk installed: {adk_available()}")
    print(f"  ADK Workflow API:     {workflow_api_available()}")

    root, info = build_control_plane_from_registry()
    print("\n=== Graph assembly ===")
    print(json.dumps({k: v for k, v in info.items() if k != "agent_meta"}, indent=2))

    if root is None:
        print("\nNo ADK root built (install google-adk to materialize the graph).")
        print("Headless alternative: python demos/run_modular_agents_demo.py --compare")
        return 0

    print(f"\nroot_agent type: {type(root).__name__}")
    print(f"root_agent name: {getattr(root, 'name', None)}")
    print("\nNote: agents/pipeline/agent.py was not used. Product path: adk run agents/pipeline")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
