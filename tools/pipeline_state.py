"""Shared pipeline state contract for agentic-ontogpt."""

from __future__ import annotations

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
    execution_mode: str = "real"
    adk_model: str = ""
    spires_model: str = ""
    pipeline_version: str = "0.2.0"
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
        self.schema_history.append({
            "version": self.schema_version,
            "sha256": _sha256_text(yaml_text),
            "length": len(yaml_text or ""),
            "at": _utc_now(),
        })
        self.touch()

    def set_validation(self, report: Dict[str, Any]) -> None:
        self.validation_report = report or {}
        self.touch()

    def schema_is_valid(self) -> bool:
        return bool(self.validation_report.get("valid"))

    def set_extraction(self, result: Dict[str, Any], *, blocked: bool = False) -> None:
        self.extraction_result = result or {}
        self.extraction_blocked = blocked
        self.touch()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineState":
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore
        filtered = {k: v for k, v in (data or {}).items() if k in known}
        return cls(**filtered)

    def snapshot(self) -> Dict[str, Any]:
        return copy.deepcopy(self.to_dict())


def new_pipeline_state(
    source_text: str = "",
    entity_types: Optional[List[str]] = None,
    relation_types: Optional[List[str]] = None,
    ontology_preferences: Optional[Dict[str, str]] = None,
    execution_mode: str = "real",
) -> PipelineState:
    from .modes import get_adk_model, get_spires_model, get_execution_mode
    mode = get_execution_mode(execution_mode).value
    run_id = f"run-{_utc_now().replace(':', '').replace('+', 'Z')[:18]}"
    return PipelineState(
        source_text=source_text or "",
        entity_types=list(entity_types or []),
        relation_types=list(relation_types or []),
        ontology_preferences=dict(ontology_preferences or {}),
        execution_mode=mode,
        adk_model=get_adk_model(),
        spires_model=get_spires_model(),
        run_id=run_id,
    )
