"""Shared pipeline state contract for agentic-ontogpt."""

from __future__ import annotations

try:
    from importlib.metadata import version as _pkg_version
except ImportError:  # pragma: no cover
    from importlib_metadata import version as _pkg_version  # type: ignore


def _package_version() -> str:
    try:
        return _pkg_version("agentic-ontogpt")
    except Exception:
        return "0.1.0"


import copy
import hashlib
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_text(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


@dataclass
class PipelineState:
    source_text: str = ""
    entity_types: List[str] = field(default_factory=list)
    relation_types: List[str] = field(default_factory=list)
    ontology_preferences: Dict[str, str] = field(default_factory=dict)
    ontology_candidates: Dict[str, Any] = field(default_factory=dict)
    selected_ontologies: Dict[str, str] = field(default_factory=dict)
    ontology_policy_report: Dict[str, Any] = field(default_factory=dict)
    generated_schema_yaml: str = ""
    schema_version: int = 0
    schema_history: List[Dict[str, Any]] = field(default_factory=list)
    validation_report: Dict[str, Any] = field(default_factory=dict)
    repair_iterations: int = 0
    repair_stopped_reason: str = ""
    extraction_result: Dict[str, Any] = field(default_factory=dict)
    extraction_blocked: bool = False
    grounding_report: Dict[str, Any] = field(default_factory=dict)
    component_metrics: Dict[str, Any] = field(default_factory=dict)
    rdf_export: Dict[str, Any] = field(default_factory=dict)
    execution_mode: str = "real"
    adk_model: str = ""
    spires_model: str = ""
    pipeline_version: str = field(default_factory=_package_version)
    provenance_manifest: Dict[str, Any] = field(default_factory=dict)
    run_id: str = ""
    created_at: str = field(default_factory=_utc_now)
    updated_at: str = field(default_factory=_utc_now)

    def touch(self) -> None:
        self.updated_at = _utc_now()

    def set_schema(self, yaml_text: str, *, from_repair: bool = False) -> None:
        prev = self.generated_schema_yaml
        self.generated_schema_yaml = yaml_text
        if from_repair or prev:
            self.schema_version += 1
        self.schema_history.append(
            {
                "version": self.schema_version,
                "sha256": _sha256_text(yaml_text),
                "length": len(yaml_text or ""),
                "at": _utc_now(),
            }
        )
        self.touch()

    def set_validation(self, report: Dict[str, Any]) -> None:
        self.validation_report = report or {}
        self.touch()

    def schema_is_valid(self) -> bool:
        return bool((self.validation_report or {}).get("valid"))

    def set_extraction(self, result: Dict[str, Any], *, blocked: bool = False) -> None:
        self.extraction_result = result or {}
        self.extraction_blocked = blocked
        self.touch()

    def apply_repair_history(self, history: List[Dict[str, Any]]) -> None:
        if not history:
            return
        self.schema_history = []
        for h in history:
            self.schema_history.append(
                {
                    "version": h.get("version", h.get("iteration", 0)),
                    "sha256": h.get("schema_sha256") or _sha256_text(h.get("schema_yaml") or ""),
                    "valid": h.get("valid"),
                    "completeness": h.get("completeness"),
                    "errors": h.get("errors") or [],
                    "at": h.get("at") or _utc_now(),
                }
            )
        self.schema_version = max(h.get("version", 0) for h in self.schema_history)
        self.touch()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def new_pipeline_state(
    source_text: str,
    entity_types: List[str],
    *,
    relation_types: Optional[List[str]] = None,
    ontology_preferences: Optional[Dict[str, str]] = None,
    execution_mode: str = "real",
) -> PipelineState:
    import uuid

    return PipelineState(
        source_text=source_text,
        entity_types=list(entity_types or []),
        relation_types=list(relation_types or []),
        ontology_preferences=dict(ontology_preferences or {}),
        execution_mode=execution_mode,
        run_id=str(uuid.uuid4()),
    )
