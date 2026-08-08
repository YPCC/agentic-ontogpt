"""Modular SPIRES extraction agent (ADK LlmAgent factory)."""
from __future__ import annotations

from textwrap import dedent
from typing import Any, Optional


def get_tools():
    try:
        from tools.spires import run_spires_extraction
        from tools.schema_gate import gate_schema_for_extraction
    except ImportError:
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from tools.spires import run_spires_extraction
        from tools.schema_gate import gate_schema_for_extraction

    def extract_with_spires(
        template_yaml: str,
        text: str,
        schema_name: str = "clinical_extraction",
        validation_valid: bool = True,
        validation_message: str = "",
    ) -> dict:
        """Deterministic gate via tools.schema_gate before SPIRES."""
        decision = gate_schema_for_extraction(template_yaml or "", revalidate=True)
        if not decision.allowed:
            return decision.block_response or {
                "status": "error",
                "outcome": "REAL_EXTRACTION_FAILED",
                "error_type": "invalid_schema",
            }
        return run_spires_extraction(
            template_yaml,
            text,
            schema_name=schema_name,
            require_valid_schema=True,
            validation_result=decision.validation,
        )

    return [extract_with_spires]


INSTRUCTION = dedent(
    """
    Before extracting, inspect validation_result from session state.
    If validation_result.valid is false, DO NOT call extract_with_spires.
    Instead reply that extraction is blocked until the schema is valid,
    and summarize validation errors.

    If validation_result.valid is true:
    Call extract_with_spires with template_yaml, text, validation_valid=true.

    Present outcome explicitly:
      REAL_SUCCESS | SIMULATION_REQUESTED | REAL_EXTRACTION_FAILED
    Never treat a failure as a successful simulation.
    """
)


def build_spires_extractor(model: Optional[str] = None) -> Any:
    from google.adk.agents import LlmAgent

    try:
        from tools.modes import get_adk_model

        model = model or get_adk_model()
    except Exception:
        model = model or "gemini-2.0-flash"
    return LlmAgent(
        name="SPIRESExtractionAgent",
        model=model,
        description="Runs OntoGPT SPIRES extraction only after successful validation.",
        instruction=INSTRUCTION,
        tools=get_tools(),
        output_key="extraction_result",
    )
