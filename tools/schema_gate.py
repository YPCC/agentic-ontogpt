"""Shared deterministic schema gate for SPIRES extraction (Paths A / C / modular).

Governance rule: extraction must not run on an invalid LinkML/SPIRES schema.
Callers must not rely on LLM-supplied ``validation_valid`` alone.

Usage::

    from tools.schema_gate import gate_schema_for_extraction

    decision = gate_schema_for_extraction(schema_yaml)
    if not decision.allowed:
        return decision.block_response
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .linkml_tools import validate_linkml_schema
from .modes import ExtractionOutcome, extraction_response


@dataclass
class SchemaGateDecision:
    allowed: bool
    validation: Dict[str, Any] = field(default_factory=dict)
    block_response: Optional[Dict[str, Any]] = None

    @property
    def valid(self) -> bool:
        return bool(self.validation.get("valid"))


def blocked_extraction_response(
    validation: Dict[str, Any],
    *,
    message: Optional[str] = None,
) -> Dict[str, Any]:
    errors = validation.get("errors")
    msg = message or "Extraction blocked: schema failed deterministic validation gate"
    if errors and not message:
        msg = f"{msg}. errors={errors}"
    resp = extraction_response(
        ExtractionOutcome.REAL_EXTRACTION_FAILED,
        error_type="invalid_schema",
        message=msg,
    )
    resp["status"] = "error"
    resp["errors"] = errors
    resp["validation"] = validation
    return resp


def gate_schema_for_extraction(
    template_yaml: str,
    *,
    precomputed_validation: Optional[Dict[str, Any]] = None,
    revalidate: bool = True,
) -> SchemaGateDecision:
    """Decide whether extract may proceed.

    When ``revalidate`` is True (default), always re-run the LinkML ladder on
    ``template_yaml`` so a false ``valid=True`` cannot bypass the gate.
    """
    if revalidate or precomputed_validation is None:
        validation = validate_linkml_schema(template_yaml or "")
    else:
        validation = dict(precomputed_validation)

    if validation.get("valid"):
        return SchemaGateDecision(allowed=True, validation=validation)

    return SchemaGateDecision(
        allowed=False,
        validation=validation,
        block_response=blocked_extraction_response(validation),
    )


def ensure_schema_or_block(
    template_yaml: str,
    *,
    precomputed_validation: Optional[Dict[str, Any]] = None,
    revalidate: bool = True,
) -> Dict[str, Any]:
    decision = gate_schema_for_extraction(
        template_yaml,
        precomputed_validation=precomputed_validation,
        revalidate=revalidate,
    )
    if not decision.allowed:
        return decision.block_response or blocked_extraction_response(decision.validation)
    return {"ok": True, "validation": decision.validation}
