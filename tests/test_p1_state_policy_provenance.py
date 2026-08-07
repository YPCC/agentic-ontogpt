"""P1 tests: pipeline state, ontology policy, provenance, headless runner."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.pipeline_state import new_pipeline_state, PipelineState
from tools.ontology_policy import apply_ontology_policy, load_ontology_policy
from tools.provenance import build_run_manifest, write_manifest
from tools.pipeline_runner import run_pipeline
from tools.modes import ExtractionOutcome


def test_pipeline_state_schema_versioning():
    st = new_pipeline_state(source_text="hello", entity_types=["Drug"])
    assert st.run_id
    st.set_schema("id: a\nname: a\nimports: []\nclasses: {}", from_repair=False)
    v0 = st.schema_version
    st.set_schema("id: b\nname: b\nimports: []\nclasses: {}", from_repair=True)
    assert st.schema_version == v0 + 1
    assert len(st.schema_history) == 2
    st2 = PipelineState.from_dict(st.to_dict())
    assert st2.source_text == "hello"


def test_ontology_policy_prefer_and_deny():
    pol = load_ontology_policy()
    report = apply_ontology_policy(
        ["Disease", "Drug"],
        recommendations=[
            {"acronym": "STY", "score": 0.99, "name": "Semantic Types"},
            {"acronym": "MONDO", "score": 0.5, "name": "Mondo"},
        ],
        user_preferences={"Drug": "RXNORM"},
        policy=pol,
    )
    assert report["selected"].get("Drug") == "RXNORM"
    assert report["selected"].get("Disease") == "MONDO"
    assert "STY" not in report["selected"].values()


def test_ontology_policy_rejects_denylist_preference():
    pol = load_ontology_policy()
    report = apply_ontology_policy(
        ["Disease"], user_preferences={"Disease": "STY"}, policy=pol,
    )
    if "Disease" in report["selected"]:
        assert report["selected"]["Disease"] != "STY"


def test_provenance_manifest_fields(tmp_path):
    st = new_pipeline_state(source_text="pt has fever", entity_types=["Finding"])
    st.set_schema("id: x\nname: x\nimports:\n  - linkml:types\n  - core\nclasses:\n  ExtractionResult:\n    tree_root: true\n  Finding:\n    is_a: NamedEntity\n", from_repair=True)
    st.set_validation({"valid": True, "status": "success", "errors": [], "stages": []})
    st.set_extraction({"outcome": "REAL_EXTRACTION_FAILED", "status": "error"})
    man = build_run_manifest(st)
    assert man["run_id"] and man["schema"]["sha256"]
    path = write_manifest(man, tmp_path / "manifest.json")
    assert json.loads(Path(path).read_text())["schema"]["sha256"] == man["schema"]["sha256"]


def test_run_pipeline_headless_blocks_or_extracts(monkeypatch):
    monkeypatch.setenv("AGENTIC_ONTOGPT_MODE", "real")
    st = run_pipeline(
        "Patient developed neutropenia after carboplatin.",
        ["Medication", "AdverseEvent"],
        ontology_preferences={"Medication": "RXNORM", "AdverseEvent": "MEDDRA"},
        initial_schema_yaml="name: broken\n",
    )
    assert st.selected_ontologies.get("Medication") == "RXNORM"
    assert st.validation_report.get("valid") is True
    assert st.provenance_manifest.get("run_id")
    outcome = st.extraction_result.get("outcome")
    assert outcome in (
        ExtractionOutcome.REAL_EXTRACTION_FAILED.value,
        ExtractionOutcome.REAL_SUCCESS.value,
    )


def test_run_pipeline_simulation_mode(monkeypatch):
    monkeypatch.setenv("AGENTIC_ONTOGPT_MODE", "simulation")
    st = run_pipeline("melanoma text", ["Disease"], execution_mode="simulation")
    assert st.extraction_result.get("outcome") == ExtractionOutcome.SIMULATION_REQUESTED.value
    assert st.extraction_result.get("fixture") is True
