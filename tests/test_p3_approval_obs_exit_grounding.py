"""P3 tests: approval, observability, exit agent, grounding benchmark."""
from __future__ import annotations
import importlib.util, os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.approval import request_approval, write_decision, gate_or_raise
from tools.observability import ObservabilitySession, render_dashboard_html, write_dashboard, estimate_tokens_from_text
from tools.grounding_benchmark import run_grounding_benchmark

_exit_path = ROOT / "agents" / "pipeline" / "exit_agent.py"
_spec = importlib.util.spec_from_file_location("exit_agent", _exit_path)
_exit = importlib.util.module_from_spec(_spec)
sys.modules["exit_agent"] = _exit
_spec.loader.exec_module(_exit)
build_repair_loop = _exit.build_repair_loop
ADK_AVAILABLE = _exit.ADK_AVAILABLE
_parse_valid_from_state = _exit._parse_valid_from_state

def test_approval_auto():
    d = request_approval("before_extraction", "run1", "ok", mode="auto")
    assert d.approved is True

def test_approval_reject_mode():
    assert request_approval("before_extraction", "run1", "ok", mode="reject").approved is False

def test_approval_file_workflow(tmp_path, monkeypatch):
    monkeypatch.setenv("APPROVAL_DIR", str(tmp_path))
    d = request_approval("after_schema_validation", "run42", "schema ready", mode="require")
    assert d.approved is False
    write_decision("run42", "after_schema_validation", True, reviewer="tester")
    assert request_approval("after_schema_validation", "run42", "schema ready", mode="require").approved is True

def test_gate_or_raise():
    try:
        gate_or_raise("before_extraction", "r", "x", mode="reject"); assert False
    except PermissionError:
        pass
    gate_or_raise("before_extraction", "r", "x", mode="auto")

def test_observability_session(tmp_path):
    s = ObservabilitySession(run_id="obs1")
    s.mark("ontology", api_calls=1)
    s.mark("extract", model="gpt-4o", input_tokens=200, output_tokens=80, api_calls=1)
    assert s.summary()["n_stages"] == 2
    assert "obs1" in render_dashboard_html([s.summary()])
    write_dashboard([s.summary()], tmp_path / "dash.html")

def test_estimate_tokens():
    assert estimate_tokens_from_text("abcd" * 10) >= 1

def test_parse_valid_from_state():
    assert _parse_valid_from_state({"validation_result": {"valid": True}}) is True
    assert _parse_valid_from_state({"validation_result": {"valid": False}}) is False

def test_build_repair_loop_stub_or_adk():
    class Dummy: name = "X"
    loop = build_repair_loop(Dummy(), Dummy(), max_iterations=3)
    if not ADK_AVAILABLE:
        assert isinstance(loop, dict) and loop["adk_available"] is False

def test_grounding_benchmark_lexicon_smoke():
    train = [{"pmid": "1", "mentions": [{"text": "melanoma", "cui": "C0025202"}]}]
    test = [{"pmid": "2", "mentions": [{"text": "melanoma", "cui": "C0025202"},
                                        {"text": "unknownxyz", "cui": "C9999999"}]}]
    res = run_grounding_benchmark(test, train_docs=train, mode="lexicon")
    assert res["modes"]["lexicon"]["instance_micro"]["tp"] >= 1
