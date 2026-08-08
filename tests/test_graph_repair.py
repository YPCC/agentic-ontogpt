"""Multi-iter repair graph showcase — pipeline.agent construction untouched."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_describe_patterns_mentions_pipeline_unchanged():
    from agents.graph_repair import describe_patterns

    p = describe_patterns()
    assert "dynamic_repair" in p and "workflow_repair_gate" in p
    assert "pipeline" in p["pipeline_loopagent"].lower()


def test_repair_gate_routes():
    from agents.graph_repair import make_repair_gate

    gate = make_repair_gate(max_iterations=3)

    def route_of(x):
        return x.get("route") if isinstance(x, dict) else getattr(x, "route", x)

    assert route_of(gate({"valid": False, "iteration": 1})) == "REFINE"
    assert route_of(gate({"valid": False, "iteration": 3})) == "DONE"
    assert route_of(gate({"valid": True, "iteration": 1})) == "DONE"


def test_builders_report_pipeline_not_touched():
    from agents.graph_repair import (
        build_dynamic_repair_orchestrator,
        build_workflow_with_repair_gate,
    )

    _, d = build_dynamic_repair_orchestrator(max_iterations=2)
    _, w = build_workflow_with_repair_gate(max_iterations=2)
    assert d["pipeline_module_touched"] is False
    assert w["pipeline_module_touched"] is False


def test_pipeline_agent_source_still_has_loop():
    src = (ROOT / "agents" / "pipeline" / "agent.py").read_text()
    assert "LoopAgent" in src or "repair_loop" in src
    assert "root_agent" in src
