"""Ablation configurations A–D (P2)."""

from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional

from .linkml_tools import validate_linkml_schema
from .metrics import Timer, build_component_metrics
from .modes import get_execution_mode
from .ontology_policy import apply_ontology_policy, load_ontology_policy
from .pipeline_state import new_pipeline_state
from .provenance import build_run_manifest
from .repair import fixture_regenerate, repair_until_valid
from .spires import run_spires_extraction

ABLATION_LABELS = {
    "A": "hand_authored_template",
    "B": "oneshot_generate_no_validate",
    "C": "generate_validate_once",
    "D": "full_agentic_policy_repair_gate",
}


def run_ablation(config, source_text, entity_types, *, hand_authored_schema=None,
                 oneshot_schema=None, ontology_preferences=None,
                 bioportal_recommendations=None, regenerate_fn=None, execution_mode=None):
    config = config.upper().strip()
    if config not in ABLATION_LABELS:
        raise ValueError(f"Unknown ablation config {config}")
    timer = Timer()
    mode = execution_mode or get_execution_mode().value
    state = new_pipeline_state(source_text=source_text, entity_types=entity_types,
                               ontology_preferences=ontology_preferences, execution_mode=mode)
    regen = regenerate_fn or fixture_regenerate
    first_pass_valid = None

    if config == "D":
        report = apply_ontology_policy(entity_types, recommendations=bioportal_recommendations,
                                       user_preferences=ontology_preferences,
                                       policy=load_ontology_policy())
        state.selected_ontologies = dict(report.get("selected") or {})
        state.ontology_policy_report = report
    else:
        state.selected_ontologies = {et: (ontology_preferences or {}).get(et, "") for et in entity_types}
        state.ontology_policy_report = {"status": "skipped", "config": config}
    timer.mark("ontology")

    if config == "A":
        if not hand_authored_schema:
            raise ValueError("Config A requires hand_authored_schema")
        state.set_schema(hand_authored_schema, from_repair=False)
        val = validate_linkml_schema(hand_authored_schema)
        first_pass_valid = bool(val.get("valid"))
        state.set_validation(val)
        state.repair_stopped_reason = "hand_authored"
    elif config == "B":
        seed = oneshot_schema or "name: oneshot_seed\n"
        schema = regen(seed, {"valid": False, "errors": ["oneshot"]}, 1)
        state.set_schema(schema, from_repair=False)
        val = validate_linkml_schema(schema)
        first_pass_valid = bool(val.get("valid"))
        state.set_validation(val)
        state.repair_stopped_reason = "oneshot_no_repair"
    elif config == "C":
        seed = oneshot_schema or "name: broken\n"
        schema = regen(seed, {"valid": False, "errors": ["initial"]}, 1)
        state.set_schema(schema, from_repair=False)
        val = validate_linkml_schema(schema)
        first_pass_valid = bool(val.get("valid"))
        state.set_validation(val)
        state.repair_stopped_reason = "validate_once_no_loop"
    else:
        seed = oneshot_schema or hand_authored_schema or "name: broken\n"
        first = validate_linkml_schema(seed)
        first_pass_valid = bool(first.get("valid"))
        repair = repair_until_valid(seed, regen, max_iterations=3)
        state.set_schema(repair.schema_yaml, from_repair=True)
        state.schema_version = repair.schema_version
        state.repair_iterations = repair.iterations
        state.repair_stopped_reason = repair.stopped_reason
        state.set_validation(repair.final_validation)
    timer.mark("schema")

    gate = config in ("A", "C", "D")
    if gate and not state.schema_is_valid():
        state.set_extraction({"status": "error", "outcome": "REAL_EXTRACTION_FAILED",
                              "error_type": "invalid_schema",
                              "message": f"Ablation {config}: extraction blocked"}, blocked=True)
    else:
        result = run_spires_extraction(
            state.generated_schema_yaml or "name: empty\n", state.source_text,
            mode=state.execution_mode, require_valid_schema=gate,
            validation_result=state.validation_report if gate else {"valid": True})
        state.set_extraction(result, blocked=result.get("error_type") == "invalid_schema")
    timer.mark("extract")
    build_run_manifest(state)
    metrics = build_component_metrics(
        selected_ontologies=state.selected_ontologies,
        policy_rejected=(state.ontology_policy_report or {}).get("rejected"),
        validation_report=state.validation_report, repair_iterations=state.repair_iterations,
        first_pass_valid=first_pass_valid, schema_version=state.schema_version,
        extraction_result=state.extraction_result, timer=timer)
    return {"config": config, "label": ABLATION_LABELS[config],
            "state": state.to_dict(), "metrics": metrics.to_dict()}


def run_ablation_suite(source_text, entity_types, *, hand_authored_schema, oneshot_seed=None,
                       ontology_preferences=None, regenerate_fn=None, execution_mode=None, configs=None):
    configs = configs or ["A", "B", "C", "D"]
    rows, results = [], {}
    for c in configs:
        r = run_ablation(c, source_text, entity_types, hand_authored_schema=hand_authored_schema,
                         oneshot_schema=oneshot_seed, ontology_preferences=ontology_preferences,
                         regenerate_fn=regenerate_fn, execution_mode=execution_mode)
        results[c] = r
        m = r["metrics"]
        rows.append({"config": c, "label": r["label"], "schema_valid": m["template"].get("valid"),
                     "first_pass_valid": m["template"].get("first_pass_valid"),
                     "repair_iterations": m["template"].get("repair_iterations"),
                     "extraction_outcome": m["extraction"].get("outcome"),
                     "extraction_blocked": m["extraction"].get("blocked"),
                     "total_sec": m["operational"].get("total_sec")})
    return {"rows": rows, "results": results}
