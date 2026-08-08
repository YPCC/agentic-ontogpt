"""Track 1: success-gated downstream; grounding_mode default; shared outcomes."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("APPROVAL_MODE", "auto")


def test_rdf_skipped_after_failed_extraction(monkeypatch):
    monkeypatch.setenv("AGENTIC_ONTOGPT_MODE", "real")
    from tools.pipeline_runner import run_pipeline

    state = run_pipeline(
        "Patient has melanoma.",
        ["Disease"],
        execution_mode="real",
        enable_rdf=True,
        enable_grounding=True,
        grounding_mode="lexicon",
    )
    outcome = (state.extraction_result or {}).get("outcome")
    if outcome == "REAL_SUCCESS":
        pytest.skip("OntoGPT available in environment")
    assert state.rdf_export.get("status") == "skipped"
    assert state.grounding_report.get("status") == "skipped"


def test_grounding_mode_none_skips_even_on_success(monkeypatch):
    monkeypatch.setenv("AGENTIC_ONTOGPT_MODE", "simulation")
    from tools.pipeline_runner import run_pipeline

    state = run_pipeline(
        "Patient has melanoma.",
        ["Disease"],
        execution_mode="simulation",
        enable_grounding=True,
        grounding_mode="none",
        enable_rdf=False,
    )
    assert (state.extraction_result or {}).get("outcome") == "SIMULATION_REQUESTED"
    assert state.grounding_report.get("status") == "skipped"
    assert "grounding_mode=none" in (state.grounding_report.get("reason") or "")


def test_rdf_runs_on_simulation_success(monkeypatch):
    monkeypatch.setenv("AGENTIC_ONTOGPT_MODE", "simulation")
    from tools.pipeline_runner import run_pipeline

    state = run_pipeline(
        "Patient has melanoma.",
        ["Disease"],
        execution_mode="simulation",
        enable_rdf=True,
    )
    assert (state.extraction_result or {}).get("outcome") == "SIMULATION_REQUESTED"
    assert state.rdf_export.get("turtle") or state.rdf_export.get("status") != "skipped"


def test_made_run_spires_uses_shared_contract(monkeypatch):
    monkeypatch.setenv("AGENTIC_ONTOGPT_MODE", "simulation")
    import scripts.run_made_eval as made

    r = made.run_spires("name: empty\nid: empty\n", "note")
    assert r.get("outcome") in (
        "REAL_EXTRACTION_FAILED",
        "SIMULATION_REQUESTED",
        "REAL_SUCCESS",
    )
    assert "outcome" in r
