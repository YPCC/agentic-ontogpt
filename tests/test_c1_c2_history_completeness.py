"""C1 schema_history from repair; C2 validation_completeness."""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.linkml_tools import validate_linkml_schema
from tools.repair import repair_until_valid, fixture_regenerate
from tools.pipeline_runner import run_pipeline
from tools.pipeline_state import new_pipeline_state


def test_skipped_stages_not_ok_true():
    yaml_text = """id: http://example.org/t
name: t
imports:
  - linkml:types
  - core
classes:
  Root:
    tree_root: true
  Thing:
    is_a: NamedEntity
"""
    r = validate_linkml_schema(yaml_text)
    for s in r["stages"]:
        if s.get("skipped"):
            assert s.get("ok") is None, s
    assert "validation_completeness" in r
    assert r["validation_completeness"] in ("full", "partial", "invalid")
    if r.get("skipped_stages"):
        assert r["validation_completeness"] == "partial" or not r["valid"]


def test_convention_failure_invalid_completeness():
    r = validate_linkml_schema("id: x\nname: x\nimports: []\nclasses: {}")
    assert r["valid"] is False
    assert r["validation_completeness"] == "invalid"


def test_repair_history_in_pipeline_state(monkeypatch):
    monkeypatch.setenv("AGENTIC_ONTOGPT_MODE", "simulation")
    monkeypatch.setenv("APPROVAL_MODE", "auto")
    st = run_pipeline(
        "text",
        ["Medication"],
        initial_schema_yaml="name: broken\n",
        execution_mode="simulation",
    )
    assert st.schema_history, "expected repair history entries"
    assert any("sha256" in h for h in st.schema_history)
    assert len(st.schema_history) >= 1


def test_apply_repair_history_direct():
    repair = repair_until_valid("name: broken\n", fixture_regenerate, max_iterations=3)
    st = new_pipeline_state(source_text="x", entity_types=["Drug"])
    st.apply_repair_history(repair.history)
    assert len(st.schema_history) == len(repair.history)
    assert st.schema_history[0]["iteration"] == 1
