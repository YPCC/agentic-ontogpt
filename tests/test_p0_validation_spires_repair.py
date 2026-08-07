"""P0 tests: validation ladder, extraction outcomes, repair controller."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.linkml_tools import validate_linkml_schema
from tools.spires import run_spires_extraction
from tools.modes import ExtractionOutcome
from tools.repair import repair_until_valid, fixture_regenerate, noop_regenerate

INVALID_YAML = "classes: [\n  this is not valid"
BROKEN_CONVENTIONS = """
id: https://example.org/x
name: x
imports:
  - linkml:types
classes:
  Foo:
    attributes:
      bar:
        range: string
"""
VALID_SPIRES = """
id: https://w3id.org/ontogpt/test
name: test_schema
imports:
  - linkml:types
  - core
classes:
  ExtractionResult:
    tree_root: true
    attributes:
      drugs:
        range: Drug
        multivalued: true
  Drug:
    is_a: NamedEntity
    attributes:
      id:
        identifier: true
        range: uriorcurie
      label:
        range: string
"""


def test_yaml_syntax_failure():
    r = validate_linkml_schema(INVALID_YAML)
    assert r["valid"] is False
    assert any(s["stage"] == "yaml_syntax" and not s["ok"] for s in r["stages"])


def test_convention_failure_is_not_soft_pass():
    r = validate_linkml_schema(BROKEN_CONVENTIONS)
    assert r["valid"] is False
    assert any("NamedEntity" in e or "tree_root" in e or "core" in e for e in r["errors"])


def test_valid_spires_schema_passes_ladder():
    r = validate_linkml_schema(VALID_SPIRES)
    stages = {s["stage"]: s for s in r["stages"]}
    assert stages["yaml_syntax"]["ok"] is True
    assert stages["required_keys"]["ok"] is True
    assert stages["ontogpt_conventions"]["ok"] is True


def test_simulation_only_when_requested(monkeypatch):
    monkeypatch.setenv("AGENTIC_ONTOGPT_MODE", "simulation")
    r = run_spires_extraction(VALID_SPIRES, "patient has melanoma", require_valid_schema=False)
    assert r["outcome"] == ExtractionOutcome.SIMULATION_REQUESTED.value
    assert r["status"] == "success"
    assert r.get("fixture") is True


def test_real_mode_fails_without_ontogpt(monkeypatch):
    monkeypatch.setenv("AGENTIC_ONTOGPT_MODE", "real")
    r = run_spires_extraction(VALID_SPIRES, "patient has melanoma", require_valid_schema=False)
    assert r["outcome"] in (
        ExtractionOutcome.REAL_SUCCESS.value,
        ExtractionOutcome.REAL_EXTRACTION_FAILED.value,
    )
    if r["outcome"] == ExtractionOutcome.REAL_EXTRACTION_FAILED.value:
        assert r["status"] == "error"


def test_extraction_blocked_on_invalid_schema(monkeypatch):
    monkeypatch.setenv("AGENTIC_ONTOGPT_MODE", "real")
    r = run_spires_extraction(
        VALID_SPIRES,
        "text",
        require_valid_schema=True,
        validation_result={"valid": False, "message": "broken", "errors": ["x"]},
    )
    assert r["outcome"] == ExtractionOutcome.REAL_EXTRACTION_FAILED.value
    assert r["error_type"] == "invalid_schema"


def test_repair_loop_fixes_with_fixture_regenerator():
    result = repair_until_valid(BROKEN_CONVENTIONS, fixture_regenerate, max_iterations=3)
    assert result.valid is True
    assert result.stopped_reason == "validation_passed"
    assert result.schema_version >= 1


def test_repair_loop_exhausts_with_noop():
    result = repair_until_valid(BROKEN_CONVENTIONS, noop_regenerate, max_iterations=2)
    assert result.valid is False
    assert result.stopped_reason == "max_iterations"
    assert len(result.history) >= 2
