"""Shared schema_gate helper — single enforcement story for A/C/modular."""

from __future__ import annotations

import pytest


def test_gate_blocks_invalid_yaml():
    from tools.schema_gate import gate_schema_for_extraction

    d = gate_schema_for_extraction("not: valid: [")
    assert d.allowed is False
    assert d.block_response is not None
    assert d.block_response.get("error_type") == "invalid_schema"
    assert d.block_response.get("outcome") == "REAL_EXTRACTION_FAILED"


def test_gate_allows_valid_made_template():
    from pathlib import Path
    from tools.schema_gate import gate_schema_for_extraction

    tpl = Path("templates/made_1_0.yaml")
    if not tpl.exists():
        pytest.skip("made template missing")
    d = gate_schema_for_extraction(tpl.read_text())
    assert d.allowed is True
    assert d.validation.get("valid") is True
    assert d.block_response is None


def test_spires_uses_shared_gate_on_invalid():
    from tools.spires import run_spires_extraction

    out = run_spires_extraction(
        "broken: [",
        "text",
        require_valid_schema=True,
        validation_result={"valid": True},
    )
    assert out.get("outcome") == "REAL_EXTRACTION_FAILED"
    assert out.get("error_type") == "invalid_schema"


def test_modular_tool_uses_shared_gate():
    from agents.spires_extractor.agent import get_tools

    extract = get_tools()[0]
    out = extract("not: yaml: [[", "text", validation_valid=True)
    assert out.get("outcome") == "REAL_EXTRACTION_FAILED"
    assert out.get("error_type") == "invalid_schema"


def test_ensure_schema_or_block_ok_shape():
    from pathlib import Path
    from tools.schema_gate import ensure_schema_or_block

    tpl = Path("templates/made_1_0.yaml")
    if not tpl.exists():
        pytest.skip("made template missing")
    r = ensure_schema_or_block(tpl.read_text())
    assert r.get("ok") is True
    assert r["validation"].get("valid") is True
