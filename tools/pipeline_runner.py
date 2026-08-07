"""Headless pipeline runner using PipelineState (P1+P3)."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from .modes import get_execution_mode
from .ontology_policy import apply_ontology_policy, load_ontology_policy
from .pipeline_state import PipelineState, new_pipeline_state
from .provenance import build_run_manifest
from .repair import fixture_regenerate, repair_until_valid
from .spires import run_spires_extraction
from .approval import request_approval, get_approval_mode
from .observability import ObservabilitySession, estimate_tokens_from_text


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
    """Execute ontology policy → schema repair → gated extract → provenance."""
    state = new_pipeline_state(
        source_text=source_text,
        entity_types=entity_types,
        relation_types=relation_types,
        ontology_preferences=ontology_preferences,
        execution_mode=execution_mode or get_execution_mode().value,
    )
    obs = ObservabilitySession(run_id=state.run_id)

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
    obs.mark("ontology", api_calls=1 if bioportal_recommendations else 0)
    dec = request_approval(
        "after_ontology_selection",
        state.run_id,
        f"selected={state.selected_ontologies}",
        {"selected": state.selected_ontologies},
    )
    if not dec.approved:
        state.set_extraction(
            {
                "status": "error",
                "outcome": "REAL_EXTRACTION_FAILED",
                "error_type": "approval_denied",
                "message": dec.comment,
            },
            blocked=True,
        )
        build_run_manifest(state)
        state.component_metrics = {
            "approval": dec.to_dict(),
            "observability": obs.summary(),
        }
        return state

    schema = initial_schema_yaml or ""
    regen = regenerate_fn or fixture_regenerate
    seed = schema if schema else "name: empty\n"
    repair = repair_until_valid(seed, regen, max_iterations=max_repair_iterations)
    state.set_schema(repair.schema_yaml, from_repair=True)
    state.schema_version = repair.schema_version
    state.repair_iterations = repair.iterations
    state.repair_stopped_reason = repair.stopped_reason
    state.set_validation(repair.final_validation)
    obs.mark(
        "schema_repair",
        input_tokens=estimate_tokens_from_text(state.generated_schema_yaml),
    )
    dec2 = request_approval(
        "after_schema_validation",
        state.run_id,
        f"valid={state.schema_is_valid()}",
        {
            "valid": state.schema_is_valid(),
            "errors": state.validation_report.get("errors"),
        },
    )
    if not dec2.approved:
        state.set_extraction(
            {
                "status": "error",
                "outcome": "REAL_EXTRACTION_FAILED",
                "error_type": "approval_denied",
                "message": dec2.comment,
            },
            blocked=True,
        )
        build_run_manifest(state)
        state.component_metrics = {
            "approval": dec2.to_dict(),
            "observability": obs.summary(),
        }
        return state

    if not state.schema_is_valid():
        state.set_extraction(
            {
                "status": "error",
                "outcome": "REAL_EXTRACTION_FAILED",
                "error_type": "invalid_schema",
                "message": "Extraction blocked: schema did not pass validation ladder",
                "errors": state.validation_report.get("errors"),
            },
            blocked=True,
        )
    else:
        result = run_spires_extraction(
            state.generated_schema_yaml,
            state.source_text,
            mode=state.execution_mode,
            require_valid_schema=True,
            validation_result=state.validation_report,
        )
        state.set_extraction(
            result, blocked=result.get("error_type") == "invalid_schema"
        )

    obs.mark(
        "extract",
        api_calls=0 if state.execution_mode == "simulation" else 1,
        input_tokens=estimate_tokens_from_text(state.source_text),
    )
    build_run_manifest(state)
    state.component_metrics = {
        **(state.component_metrics or {}),
        "observability": obs.summary(),
        "approval_mode": get_approval_mode(),
    }
    return state
