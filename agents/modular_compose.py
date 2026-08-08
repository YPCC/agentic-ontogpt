"""Headless composition of *modular* agents (not ``agents.pipeline``).

Uses the same underlying tools exposed by each package's ``get_tools()``,
and the same repair / SPIRES / policy stack as ``tools.pipeline_runner``,
so outcomes stay comparable without importing the ADK SequentialAgent graph.

The canonical ADK graph remains in ``agents.pipeline.agent`` and is unchanged.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from tools.linkml_tools import validate_linkml_schema
from tools.modes import get_execution_mode
from tools.ontology_policy import apply_ontology_policy, load_ontology_policy
from tools.pipeline_state import PipelineState, new_pipeline_state
from tools.provenance import build_run_manifest
from tools.repair import fixture_regenerate, repair_until_valid
from tools.spires import run_spires_extraction


def _tool_by_name(tools: list, name: str):
    for t in tools:
        if getattr(t, "__name__", None) == name:
            return t
    raise KeyError(f"tool {name!r} not found in {[getattr(x,'__name__',x) for x in tools]}")


def run_modular_pipeline(
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
    use_modular_tools: bool = True,
) -> PipelineState:
    """Run ontology policy → schema repair → gated extract via modular packages.

    Parameters mirror ``tools.pipeline_runner.run_pipeline`` for parity tests.
    """
    state = new_pipeline_state(
        source_text=source_text,
        entity_types=entity_types,
        relation_types=relation_types,
        ontology_preferences=ontology_preferences,
        execution_mode=execution_mode or get_execution_mode().value,
    )
    state.component_metrics = {
        **(state.component_metrics or {}),
        "composer": "modular",
        "pipeline_path": "agents.modular_compose",
    }

    if use_modular_tools:
        from agents.ontology_selector import get_tools as ont_tools
        import json

        apply_policy_tool = _tool_by_name(ont_tools(), "apply_policy")
        report = apply_policy_tool(
            ",".join(entity_types),
            user_preferences_json=json.dumps(ontology_preferences or {}),
            recommendations_json=json.dumps(bioportal_recommendations or []),
        )
        state.selected_ontologies = dict(report.get("selected") or {})
        state.ontology_policy_report = report
    else:
        policy = load_ontology_policy(policy_path) if policy_path else load_ontology_policy()
        policy_report = apply_ontology_policy(
            entity_types,
            recommendations=bioportal_recommendations,
            user_preferences=ontology_preferences,
            policy=policy,
        )
        state.selected_ontologies = dict(policy_report.get("selected") or {})
        state.ontology_policy_report = policy_report

    state.ontology_candidates = {"recommendations": bioportal_recommendations or []}

    if use_modular_tools:
        from agents.validator import get_tools as val_tools

        validate_schema = _tool_by_name(val_tools(), "validate_schema")
    else:
        validate_schema = validate_linkml_schema

    def _validate_wrapper(yaml_str: str) -> Dict[str, Any]:
        return validate_schema(yaml_str)

    schema = initial_schema_yaml or ""
    regen = regenerate_fn or fixture_regenerate
    seed = schema if schema else "name: empty\n"
    repair = repair_until_valid(seed, regen, max_iterations=max_repair_iterations)
    modular_val = _validate_wrapper(repair.schema_yaml)
    state.set_schema(repair.schema_yaml, from_repair=True)
    state.schema_version = repair.schema_version
    state.repair_iterations = repair.iterations
    state.repair_stopped_reason = repair.stopped_reason
    final_val = modular_val if isinstance(modular_val, dict) else repair.final_validation
    if not final_val.get("valid") and repair.final_validation.get("valid"):
        final_val = repair.final_validation
    state.set_validation(final_val)
    state.apply_repair_history(repair.history)
    state.component_metrics["modular_validator_agrees"] = (
        bool(modular_val.get("valid")) == bool(repair.final_validation.get("valid"))
    )

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
        if use_modular_tools:
            from agents.spires_extractor import get_tools as sp_tools

            extract_with_spires = _tool_by_name(sp_tools(), "extract_with_spires")
            result = extract_with_spires(
                state.generated_schema_yaml,
                state.source_text,
                schema_name="clinical_extraction",
                validation_valid=True,
                validation_message="valid",
            )
        else:
            result = run_spires_extraction(
                state.generated_schema_yaml,
                state.source_text,
                mode=state.execution_mode,
                require_valid_schema=True,
                validation_result=state.validation_report,
            )
        blocked = result.get("error_type") == "invalid_schema"
        state.set_extraction(result, blocked=blocked)

    build_run_manifest(state)
    state.component_metrics["composer"] = "modular"
    return state
