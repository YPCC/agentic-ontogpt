"""OntoGPT SPIRES extraction with explicit outcomes (no silent simulation)."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .linkml_tools import save_template_yaml
from .modes import (
    ExecutionMode,
    ExtractionOutcome,
    extraction_response,
    get_execution_mode,
    get_spires_model,
)

_SIMULATION_FIXTURE = {
    "extracted_object": {
        "diseases": ["melanoma"],
        "genes": ["BRAF"],
        "drugs": ["vemurafenib"],
        "disease_gene_associations": [{"disease": "melanoma", "gene": "BRAF"}],
        "drug_disease_associations": [
            {"drug": "vemurafenib", "disease": "melanoma", "relation": "treats"}
        ],
    },
    "named_entities": [
        {"id": "MONDO:0005105", "label": "melanoma"},
        {"id": "HGNC:1097", "label": "BRAF"},
        {"id": "CHEBI:63637", "label": "vemurafenib"},
    ],
}


def run_spires_extraction(
    template_yaml: str,
    text: str,
    schema_name: str = "clinical_extraction",
    mode: Optional[str] = None,
    *,
    require_valid_schema: bool = True,
    validation_result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Run SPIRES with explicit outcomes. Simulation is opt-in only."""
    exec_mode = get_execution_mode(mode)

    if require_valid_schema and validation_result is not None:
        if validation_result.get("valid") is False:
            return extraction_response(
                ExtractionOutcome.REAL_EXTRACTION_FAILED,
                error_type="invalid_schema",
                message=(
                    "Extraction blocked: schema validation failed. "
                    + str(validation_result.get("message") or validation_result.get("errors"))
                ),
            )

    save_info = save_template_yaml(template_yaml, schema_name)
    path = save_info["path"]

    if exec_mode == ExecutionMode.SIMULATION:
        return extraction_response(
            ExtractionOutcome.SIMULATION_REQUESTED,
            extracted_object=_SIMULATION_FIXTURE["extracted_object"],
            named_entities=_SIMULATION_FIXTURE["named_entities"],
            template_path=path,
            message=(
                "Simulation fixture (AGENTIC_ONTOGPT_MODE=simulation). "
                "Not a measure of extraction quality."
            ),
            extra={"fixture": True, "source_text_preview": (text or "")[:120]},
        )

    try:
        from ontogpt.engines.spires_engine import SPIRESEngine
        from ontogpt.io.template_loader import get_template_details
    except Exception as e:
        return extraction_response(
            ExtractionOutcome.REAL_EXTRACTION_FAILED,
            template_path=path,
            error_type="ontogpt_not_available",
            message=f"OntoGPT not available in real mode: {e}",
        )

    try:
        template_details = get_template_details(template=path)
        engine = SPIRESEngine(
            template_details=template_details,
            model=get_spires_model(),
        )
        result = engine.extract_from_text(text)
        extracted = result.extracted_object
        if hasattr(extracted, "model_dump"):
            extracted = extracted.model_dump()
        elif hasattr(extracted, "dict"):
            extracted = extracted.dict()
        else:
            extracted = str(extracted)
        named = []
        for ne in result.named_entities or []:
            if hasattr(ne, "model_dump"):
                named.append(ne.model_dump())
            elif hasattr(ne, "dict"):
                named.append(ne.dict())
            else:
                named.append(str(ne))
        return extraction_response(
            ExtractionOutcome.REAL_SUCCESS,
            extracted_object=extracted,
            named_entities=named,
            template_path=path,
            raw_completion=getattr(result, "raw_completion_output", None),
        )
    except Exception as e:
        return extraction_response(
            ExtractionOutcome.REAL_EXTRACTION_FAILED,
            template_path=path,
            error_type=type(e).__name__,
            message=f"SPIRES extraction failed: {e}",
        )
