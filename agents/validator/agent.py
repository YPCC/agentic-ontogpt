"""Modular Validator agent (ADK LlmAgent factory)."""
from __future__ import annotations

from textwrap import dedent
from typing import Any, Optional


def _tools():
    try:
        from tools.linkml_tools import validate_linkml_schema
    except ImportError:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from tools.linkml_tools import validate_linkml_schema

    def validate_schema(schema_yaml: str) -> dict:
        return validate_linkml_schema(schema_yaml)

    return [validate_schema]


INSTRUCTION = dedent(
    """
    Call validate_schema on the FULL generated schema YAML string
    (from generated_schema_yaml / prior agent output).

    Report:
    - VALID if valid==true
    - INVALID plus the errors list and failed stages if valid==false

    Do not soften convention failures; they are errors.
    Note validation_completeness: full | partial | invalid when present.
    """
)


def build_validator(model: Optional[str] = None) -> Any:
    from google.adk.agents import LlmAgent
    try:
        from tools.modes import get_adk_model
        model = model or get_adk_model()
    except Exception:
        model = model or "gemini-2.0-flash"
    return LlmAgent(
        name="ValidatorAgent",
        model=model,
        description="Validates a LinkML/SPIRES schema via the multi-stage ladder.",
        instruction=INSTRUCTION,
        tools=_tools(),
        output_key="validation_result",
    )
