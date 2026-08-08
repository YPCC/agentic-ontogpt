"""Parity tests: modular composition vs pipeline_runner (pipeline agent graph untouched)."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _sim_mode(monkeypatch):
    monkeypatch.setenv("AGENTIC_ONTOGPT_MODE", "simulation")
    monkeypatch.setenv("APPROVAL_MODE", "auto")


def test_modular_packages_export_tools_and_instructions():
    from agents.ontology_selector import INSTRUCTION as oi, get_tools as ot
    from agents.template_generator import INSTRUCTION as ti, get_tools as tt
    from agents.validator import INSTRUCTION as vi, get_tools as vt
    from agents.spires_extractor import INSTRUCTION as si, get_tools as st

    assert "ontology" in oi.lower() or "BioPortal" in oi or "EntityType" in oi
    assert "LinkML" in ti or "YAML" in ti
    assert "validate" in vi.lower()
    assert "SPIRES" in si or "extract" in si.lower()
    assert len(ot()) >= 1 and len(tt()) >= 1 and len(vt()) >= 1 and len(st()) >= 1


def test_modular_compose_parity_with_pipeline_runner_made_style():
    from agents.modular_compose import run_modular_pipeline
    from tools.pipeline_runner import run_pipeline

    text = (
        "Patient developed severe neutropenia after carboplatin. "
        "Dose 300 mg IV q3 weeks. Indication ovarian cancer."
    )
    entities = ["Medication", "AdverseEvent", "Dosage"]
    prefs = {"Medication": "RXNORM", "AdverseEvent": "MEDDRA", "Dosage": "NCIT"}
    made = ROOT / "templates" / "made_1_0.yaml"
    initial = made.read_text() if made.exists() else None

    mod = run_modular_pipeline(
        text, entities, ontology_preferences=prefs,
        initial_schema_yaml=initial, execution_mode="simulation",
    )
    pipe = run_pipeline(
        text, entities, ontology_preferences=prefs,
        initial_schema_yaml=initial, execution_mode="simulation",
    )

    assert mod.selected_ontologies == pipe.selected_ontologies
    assert mod.schema_is_valid() is pipe.schema_is_valid()
    assert (mod.extraction_result or {}).get("outcome") == (
        pipe.extraction_result or {}
    ).get("outcome")
    assert (mod.component_metrics or {}).get("composer") == "modular"
    assert (pipe.component_metrics or {}).get("composer") != "modular"


def test_modular_compose_blocks_on_invalid_schema():
    from agents.modular_compose import run_modular_pipeline

    def bad_regen(schema_yaml, validation, iteration):
        return "not: valid: yaml: [["

    state = run_modular_pipeline(
        "text", ["Disease"],
        initial_schema_yaml="broken: [",
        regenerate_fn=bad_regen,
        max_repair_iterations=2,
        execution_mode="simulation",
    )
    assert state.schema_is_valid() is False
    assert (state.extraction_result or {}).get("outcome") == "REAL_EXTRACTION_FAILED"
    assert state.extraction_blocked is True


def test_pipeline_agent_module_still_importable():
    """Regression: modular work must not break agents.pipeline."""
    path = ROOT / "agents" / "pipeline" / "agent.py"
    assert path.is_file()
    try:
        import agents.pipeline.agent as pipeline_agent
    except ModuleNotFoundError as e:
        assert "google.adk" in str(e) or "adk" in str(e).lower()
        src = path.read_text()
        assert "root_agent" in src
        assert "def recommend_ontologies" in src
        assert "def validate_schema" in src
        return
    assert hasattr(pipeline_agent, "root_agent") or hasattr(pipeline_agent, "ontology_selector")
    assert pipeline_agent.recommend_ontologies is not None
    assert pipeline_agent.validate_schema is not None
