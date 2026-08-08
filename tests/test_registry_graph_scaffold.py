"""Registry + graph scaffold — must not mutate pipeline.agent."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_registry_lists_known_agents():
    from agents.registry import AGENT_META, KNOWN_AGENTS, list_agents

    names = list_agents()
    assert names == KNOWN_AGENTS
    for n in ("ontology_selector", "validator", "spires_extractor", "template_generator"):
        assert n in names
        assert n in AGENT_META


def test_registry_unknown_agent_raises():
    from agents.registry import build

    with pytest.raises(KeyError, match="Unknown agent"):
        build("not_a_real_agent")


def test_graph_workflow_info_without_breaking_pipeline():
    from agents.graph_workflow import build_control_plane_from_registry

    root, info = build_control_plane_from_registry()
    assert info["pipeline_module_touched"] is False
    assert info["source"] == "agents.graph_workflow"
    src = (ROOT / "agents" / "pipeline" / "agent.py").read_text()
    assert "root_agent" in src


def test_scaffold_files_exist():
    assert (ROOT / "agents" / "registry.py").is_file()
    assert (ROOT / "agents" / "graph_workflow.py").is_file()
    assert (ROOT / "demos" / "run_adk_graph_demo.py").is_file()
