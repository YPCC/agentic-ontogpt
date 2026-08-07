"""Execution mode and extraction outcome contracts for agentic-ontogpt."""

from __future__ import annotations

import os
from enum import Enum
from typing import Any, Dict, Optional


class ExecutionMode(str, Enum):
    REAL = "real"
    SIMULATION = "simulation"


class ExtractionOutcome(str, Enum):
    REAL_SUCCESS = "REAL_SUCCESS"
    SIMULATION_REQUESTED = "SIMULATION_REQUESTED"
    REAL_EXTRACTION_FAILED = "REAL_EXTRACTION_FAILED"


ENV_MODE = "AGENTIC_ONTOGPT_MODE"
ENV_ADK_MODEL = "ADK_LLM_MODEL"
ENV_SPIRES_MODEL = "SPIRES_LLM_MODEL"
DEFAULT_ADK_MODEL = "gemini-2.0-flash"
DEFAULT_SPIRES_MODEL = "gpt-4o"


def get_execution_mode(override: Optional[str] = None) -> ExecutionMode:
    raw = (override or os.environ.get(ENV_MODE) or "real").strip().lower()
    if raw in ("sim", "simulation", "fixture", "demo"):
        return ExecutionMode.SIMULATION
    return ExecutionMode.REAL


def get_adk_model() -> str:
    return os.environ.get(ENV_ADK_MODEL, DEFAULT_ADK_MODEL)


def get_spires_model() -> str:
    return os.environ.get(ENV_SPIRES_MODEL, DEFAULT_SPIRES_MODEL)


def extraction_response(
    outcome: ExtractionOutcome,
    *,
    extracted_object: Any = None,
    named_entities: Any = None,
    template_path: Optional[str] = None,
    error_type: Optional[str] = None,
    message: Optional[str] = None,
    raw_completion: Any = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    status = "success" if outcome in (
        ExtractionOutcome.REAL_SUCCESS,
        ExtractionOutcome.SIMULATION_REQUESTED,
    ) else "error"
    body: Dict[str, Any] = {
        "status": status,
        "outcome": outcome.value,
        "mode": (
            "simulation"
            if outcome == ExtractionOutcome.SIMULATION_REQUESTED
            else ("real_ontogpt" if outcome == ExtractionOutcome.REAL_SUCCESS else "real_failed")
        ),
        "template_path": template_path,
        "extracted_object": extracted_object,
        "named_entities": named_entities or [],
    }
    if message:
        body["message"] = message
    if error_type:
        body["error_type"] = error_type
    if raw_completion is not None:
        body["raw_completion"] = raw_completion
    if extra:
        body.update(extra)
    return body
