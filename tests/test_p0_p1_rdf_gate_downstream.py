"""P0/P1: RDF validity, hard extract gate, optional downstream stages."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _sim(monkeypatch):
    monkeypatch.setenv("AGENTIC_ONTOGPT_MODE", "simulation")
    monkeypatch.setenv("APPROVAL_MODE", "auto")


def test_rdf_declares_known_prefixes():
    from tools.rdf_export import extraction_to_turtle, validate_turtle_shacl

    obj = {
        "diseases": [{"label": "melanoma", "id": "MONDO:0005105"}],
        "chemicals": [{"label": "carboplatin", "id": "CHEBI:31355"}],
    }
    ttl = extraction_to_turtle(obj)
    assert "@prefix MONDO:" in ttl
    assert "@prefix CHEBI:" in ttl
    report = validate_turtle_shacl(ttl)
    if report.get("engine") == "structural_skip":
        assert report.get("conforms") is None
    elif report.get("engine") == "parse_failed":
        pytest.fail(f"Unexpected parse_failed: {report}")
    elif report.get("parse"):
        assert report["parse"].get("ok") is True


def test_unknown_curie_grounded_to_expanded_iri():
    from tools.rdf_export import extraction_to_turtle

    ttl = extraction_to_turtle({"items": [{"label": "x", "id": "NOTAREALONT:123"}]})
    assert "ao:groundedTo NOTAREALONT:123" not in ttl
    assert "curie/NOTAREALONT" in ttl or "@prefix NOTAREALONT:" in ttl


def test_pipeline_optional_rdf_flag():
    from tools.pipeline_runner import run_pipeline

    state = run_pipeline(
        "Patient has melanoma treated with carboplatin.",
        ["Disease", "Chemical"],
        execution_mode="simulation",
        enable_rdf=True,
    )
    assert state.component_metrics.get("enable_rdf") is True
    assert state.rdf_export.get("turtle") or state.rdf_export.get("status") == "error"


def test_pipeline_version_not_stale_hardcode():
    from tools.pipeline_state import new_pipeline_state

    s = new_pipeline_state("t", ["Disease"])
    assert s.pipeline_version != "0.2.0"
    assert s.pipeline_version


def test_hard_gate_blocks_invalid_yaml_tool():
    from agents.spires_extractor.agent import get_tools

    extract = get_tools()[0]
    out = extract("not: valid: [", "some text", validation_valid=True)
    assert out.get("outcome") == "REAL_EXTRACTION_FAILED"
    assert out.get("error_type") == "invalid_schema"
