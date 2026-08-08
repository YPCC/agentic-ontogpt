"""Headless pipeline runner using PipelineState.

Optional downstream stages (off by default; only after successful extraction):
  enable_grounding — requires grounding_mode lexicon|bioportal (default none)
  enable_rdf — Turtle export + parse/SHACL report
"""

from __future__ import annotations

from typing import Any, Callable

from .modes import get_execution_mode
from .ontology_policy import apply_ontology_policy, load_ontology_policy
from .pipeline_state import PipelineState, new_pipeline_state
from .provenance import build_run_manifest
from .repair import fixture_regenerate, repair_until_valid
from .spires import run_spires_extraction
from .schema_gate import gate_schema_for_extraction
from .approval import request_approval, get_approval_mode
from .observability import ObservabilitySession, estimate_tokens_from_text


def run_pipeline(
    source_text: str,
    entity_types: list[str],
    *,
    relation_types: list[str] | None = None,
    ontology_preferences: dict[str, str] | None = None,
    bioportal_recommendations: list[dict[str, Any]] | None = None,
    initial_schema_yaml: str | None = None,
    regenerate_fn: Callable[[str, dict[str, Any], int], str] | None = None,
    max_repair_iterations: int = 3,
    execution_mode: str | None = None,
    policy_path: str | None = None,
    enable_grounding: bool = False,
    enable_rdf: bool = False,
    grounding_mode: str = "none",
) -> PipelineState:
    """Ontology policy → schema repair → gated extract → optional downstream → provenance."""
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

    regen = regenerate_fn or fixture_regenerate
    seed = initial_schema_yaml if initial_schema_yaml else "name: empty\n"
    repair = repair_until_valid(seed, regen, max_iterations=max_repair_iterations)
    state.set_schema(repair.schema_yaml, from_repair=True)
    state.schema_version = repair.schema_version
    state.repair_iterations = repair.iterations
    state.repair_stopped_reason = repair.stopped_reason
    state.set_validation(repair.final_validation)
    state.apply_repair_history(repair.history)
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

    decision = gate_schema_for_extraction(
        state.generated_schema_yaml,
        precomputed_validation=state.validation_report,
        revalidate=True,
    )
    if not decision.allowed:
        state.set_validation(decision.validation)
        state.set_extraction(decision.block_response or {}, blocked=True)
    else:
        state.set_validation(decision.validation)
        result = run_spires_extraction(
            state.generated_schema_yaml,
            state.source_text,
            mode=state.execution_mode,
            require_valid_schema=True,
            validation_result=decision.validation,
        )
        blocked = (
            result.get("error_type") == "invalid_schema"
            or result.get("outcome") == "REAL_EXTRACTION_FAILED"
        )
        state.set_extraction(result, blocked=blocked)

    obs.mark(
        "extract",
        api_calls=0 if state.execution_mode == "simulation" else 1,
        input_tokens=estimate_tokens_from_text(state.source_text),
    )

    outcome = (state.extraction_result or {}).get("outcome")
    extraction_succeeded = outcome in ("REAL_SUCCESS", "SIMULATION_REQUESTED")

    if enable_grounding and extraction_succeeded:
        mode = (grounding_mode or "none").strip().lower()
        if mode in ("", "none", "off", "false", "0"):
            state.grounding_report = {
                "status": "skipped",
                "reason": (
                    "grounding_mode=none; pass grounding_mode='lexicon' with lexicon "
                    "or grounding_mode='bioportal'"
                ),
            }
        else:
            try:
                from .grounding import ground_extraction_object

                obj = state.extraction_result.get("extracted_object")
                report = ground_extraction_object(
                    obj if isinstance(obj, dict) else {},
                    state.selected_ontologies or {},
                    use_bioportal=(mode == "bioportal"),
                )
                state.grounding_report = (
                    report if isinstance(report, dict) else {"result": report}
                )
                obs.mark("grounding", api_calls=1 if mode == "bioportal" else 0)
            except Exception as e:
                state.grounding_report = {"status": "error", "error": str(e)}
    elif enable_grounding and not extraction_succeeded:
        state.grounding_report = {
            "status": "skipped",
            "reason": (
                f"extraction outcome={outcome!r}; grounding requires "
                "REAL_SUCCESS or SIMULATION_REQUESTED"
            ),
        }

    if enable_rdf and extraction_succeeded:
        try:
            from .rdf_export import export_and_validate

            state.rdf_export = export_and_validate(
                state.extraction_result,
                grounding_report=state.grounding_report or None,
            )
            obs.mark("rdf_export")
        except Exception as e:
            state.rdf_export = {"status": "error", "error": str(e)}
    elif enable_rdf and not extraction_succeeded:
        state.rdf_export = {
            "status": "skipped",
            "reason": (
                f"extraction outcome={outcome!r}; RDF requires successful extraction"
            ),
        }

    build_run_manifest(state)
    state.component_metrics = {
        **(state.component_metrics or {}),
        "observability": obs.summary(),
        "approval_mode": get_approval_mode(),
        "enable_grounding": enable_grounding,
        "enable_rdf": enable_rdf,
    }
    return state
