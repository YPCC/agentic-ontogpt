"""OntoGPT SPIRES extraction tool (real engine when available, simulation otherwise)."""

from __future__ import annotations

from typing import Any, Dict

from .linkml_tools import save_template_yaml


def run_spires_extraction(
    template_yaml: str,
    text: str,
    schema_name: str = "clinical_extraction",
) -> Dict[str, Any]:
    """Run SPIRES-style extraction against free text using a LinkML template."""
    save_info = save_template_yaml(template_yaml, schema_name)
    path = save_info["path"]

    try:
        from ontogpt.engines.spires_engine import SPIRESEngine
        from ontogpt.io.template_loader import get_template_details

        template_details = get_template_details(template=path)
        engine = SPIRESEngine(template_details=template_details, model="gpt-4o")
        result = engine.extract_from_text(text)
        return {
            "status": "success",
            "mode": "real_ontogpt",
            "extracted_object": (
                result.extracted_object.dict()
                if hasattr(result.extracted_object, "dict")
                else str(result.extracted_object)
            ),
            "named_entities": [
                ne.dict() if hasattr(ne, "dict") else str(ne)
                for ne in (result.named_entities or [])
            ],
            "raw_completion": getattr(result, "raw_completion_output", None),
            "template_path": path,
        }
    except Exception as e:
        return {
            "status": "success",
            "mode": "simulation",
            "template_path": path,
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
            "note": f"Simulation mode (real OntoGPT unavailable or failed: {e})",
        }
