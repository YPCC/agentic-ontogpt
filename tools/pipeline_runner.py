"""Headless pipeline runner using PipelineState (P1)."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from .modes import get_execution_mode
from .ontology_policy import apply_ontology_policy, load_ontology_policy
from .pipeline_state import PipelineState, new_pipeline_state
from .provenance import build_run_manifest
from .repair import fixture_regenerate, repair_until_valid
from .spires import run_spires_extraction


def run_pipeline(
    source_text: str,
    entity_types: List[str],
    *,
    relation_types: Optional[List[str]] = None,
    ontology_preferences: Optional[Dict[str, str]] = None,
    bioportal_recommendations: Optional[List[Dict[str, Any]]] = None,
    initial_schema_yaml: Optional[str] = None,
    regenerate_fn: Optional[Callable[[str, Dict[str, Any], int], str]] = None,
    max_repair_iterations: int = 3,
    execution_mode: Optional[str] = None,
    policy_path: Optional[str] = None,
) -> PipelineState:
    state = new_pipeline_state(
        source_text=source_text,
        entity_types=entity_types,
        relation_types=relation_types,
        ontology_preferences=ontology_preferences,
        execution_mode=execution_mode or get_execution_mode().value,
    )
    policy = load_ontology_policy(policy_path) if policy_path else load_ontology_policy()
    policy_report = apply_ontology_policy(
        entity_types,
        recommendations=bioportal_recommendations,
        user_preferences=ontology_preferences,
        policy=policy,
    )
    state.ontology_candidates = {"recommendations": bioportal_recommendations or []}
    state.selected_ontologies = dict(policy_report.get("selected") or {})
    state.ontology_policy_report = policy_report

    schema = initial_schema_yaml or "name: empty\n"
    regen = regenerate_fn or fixture_regenerate
    repair = repair_until_valid(schema, regen, max_iterations=max_repair_iterations)
    state.set_schema(repair.schema_yaml, from_repair=True)
    state.schema_version = repair.schema_version
    state.repair_iterations = repair.iterations
    state.repair_stopped_reason = repair.stopped_reason
    state.set_validation(repair.final_validation)

    if not state.schema_is_valid():
        state.set_extraction({
            "status": "error",
            "outcome": "REAL_EXTRACTION_FAILED",
            "error_type": "invalid_schema",
            "message": "Extraction blocked: schema did not pass validation ladder",
            "errors": state.validation_report.get("errors"),
        }, blocked=True)
    else:
        result = run_spires_extraction(
            state.generated_schema_yaml,
            state.source_text,
            mode=state.execution_mode,
            require_valid_schema=True,
            validation_result=state.validation_report,
        )
        state.set_extraction(result, blocked=result.get("error_type") == "invalid_schema")

    build_run_manifest(state)
    return state
