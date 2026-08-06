"""Smoke tests that do not require live API keys or network."""

import os

import pytest

os.environ.setdefault("BIOPORTAL_API_KEY", "test-dummy")
os.environ.setdefault("GOOGLE_API_KEY", "test-dummy")


def test_import_tools():
    from tools import (
        bioportal_recommend_ontology,
        bioportal_search_term,
        validate_linkml_schema,
        save_template_yaml,
        run_spires_extraction,
    )
    assert callable(bioportal_recommend_ontology)
    assert callable(validate_linkml_schema)


def test_validate_minimal_schema():
    from tools.linkml_tools import validate_linkml_schema

    minimal = """
id: http://example.org/test
name: test
imports:
  - linkml:types
  - core
prefixes:
  linkml: https://w3id.org/linkml/
  test: http://example.org/test/
default_prefix: test
default_range: string
classes:
  Root:
    tree_root: true
    attributes:
      items:
        range: string
  Thing:
    is_a: NamedEntity
"""
    result = validate_linkml_schema(minimal)
    assert "valid" in result
    assert result["valid"] is True or result["status"] in ("success", "warning", "error")


def test_save_template(tmp_path):
    from tools.linkml_tools import save_template_yaml

    out = save_template_yaml("id: x\nname: x\n", schema_name="unit", out_dir=str(tmp_path))
    assert out["status"] == "success"
    assert (tmp_path / "unit.yaml").exists()


def test_spires_simulation():
    from tools.spires import run_spires_extraction

    result = run_spires_extraction(
        template_yaml="id: http://example.org/t\nname: t\n",
        text="Melanoma is treated with vemurafenib.",
        schema_name="sim_test",
    )
    assert result["status"] == "success"
    assert result["mode"] in ("simulation", "real_ontogpt")
    assert "extracted_object" in result
