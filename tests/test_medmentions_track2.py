"""Track 2 MedMentions harness smoke (offline)."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def test_medmentions_template_passes_schema_gate():
    from tools.schema_gate import gate_schema_for_extraction

    tpl = REPO / "templates" / "medmentions_st21pv.yaml"
    if not tpl.exists():
        pytest.skip("template missing")
    d = gate_schema_for_extraction(tpl.read_text())
    assert d.allowed is True


def test_track2_script_oracle_smoke(tmp_path, monkeypatch):
    docs = REPO / "data/medmentions/docs_test.jsonl"
    if not docs.exists():
        pytest.skip("docs_test.jsonl missing")
    monkeypatch.setenv("AGENTIC_ONTOGPT_MODE", "simulation")
    import subprocess
    import sys

    out = tmp_path / "out"
    r = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts/run_medmentions_track2.py"),
            "--limit",
            "3",
            "--oracle",
            "--out",
            str(out),
        ],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stderr
    import json

    data = json.loads((out / "medmentions_track2_results.json").read_text())
    assert data["scores"]["micro_f1"] == 1.0
    assert data["control_plane"]["schema_gate_valid"] is True
