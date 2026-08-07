"""Root pipeline agent for agentic-ontogpt (P0/P1: error-directed repair + gated extract + policy).

Orchestrates:
  OntologySelector → (TemplateGenerator ↔ Validator)* → SPIRESExtraction

For pure-Python early-exit repair and full state/provenance, see:
  tools.repair.repair_until_valid
  tools.pipeline_runner.run_pipeline
  demos/failure_modes_repair_loop.ipynb
"""

from __future__ import annotations

from textwrap import dedent
from typing import Any, Dict, Optional

from google.adk.agents import LlmAgent, LoopAgent, SequentialAgent

try:
    from tools.bioportal import bioportal_recommend_ontology, bioportal_search_term
    from tools.linkml_tools import validate_linkml_schema, save_template_yaml
    from tools.spires import run_spires_extraction
    from tools.modes import get_adk_model
    from tools.ontology_policy import apply_ontology_policy as _apply_policy
except ImportError:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tools.bioportal import bioportal_recommend_ontology, bioportal_search_term
    from tools.linkml_tools import validate_linkml_schema, save_template_yaml
    from tools.spires import run_spires_extraction
    from tools.modes import get_adk_model
    from tools.ontology_policy import apply_ontology_policy as _apply_policy


def recommend_ontologies(entities: str) -> dict:
    """Recommend BioPortal ontologies for a comma-separated list of clinical entities."""
    return bioportal_recommend_ontology(entities)


def search_term(query: str, ontologies: str = None) -> dict:
    """Search BioPortal for a clinical term."""
    return bioportal_search_term(query, ontologies=ontologies)


def apply_policy(
    entity_types: str,
    user_preferences_json: str = "{}",
    recommendations_json: str = "[]",
) -> dict:
    """Apply deterministic ontology policy (allow/deny + preferred-by-type)."""
    import json

    entities = [e.strip() for e in entity_types.split(",") if e.strip()]
    try:
        prefs = json.loads(user_preferences_json or "{}")
    except Exception:
        prefs = {}
    try:
        recs = json.loads(recommendations_json or "[]")
    except Exception:
        recs = []
    return _apply_policy(entities, recommendations=recs, user_preferences=prefs)


def validate_schema(schema_yaml: str) -> dict:
    """Run the multi-stage LinkML / OntoGPT validation ladder."""
    return validate_linkml_schema(schema_yaml)


def persist_template(schema_yaml: str, schema_name: str = "clinical_extraction") -> dict:
    """Save the generated YAML template to disk."""
    return save_template_yaml(schema_yaml, schema_name)


def extract_with_spires(
    template_yaml: str,
    text: str,
    schema_name: str = "clinical_extraction",
    validation_valid: bool = True,
    validation_message: str = "",
) -> dict:
    """Run SPIRES extraction. Blocked when validation_valid is false."""
    validation_result: Optional[Dict[str, Any]] = {
        "valid": bool(validation_valid),
        "message": validation_message
        or ("valid" if validation_valid else "validation failed"),
    }
    return run_spires_extraction(
        template_yaml,
        text,
        schema_name=schema_name,
        require_valid_schema=True,
        validation_result=validation_result,
    )


_MODEL = get_adk_model()

ontology_selector = LlmAgent(
    name="OntologySelectorAgent",
    model=_MODEL,
    description="Selects the best BioPortal ontology for each clinical entity type.",
    instruction=dedent(
        """
        You are a biomedical ontology expert.
        Given entity types or concrete clinical terms, call recommend_ontologies
        (and search_term if needed), then call apply_policy so allow/deny lists and
        preferred-by-type rules are enforced. Return EntityType → OntologyAcronym
        with a short justification.
        """
    ),
    tools=[recommend_ontologies, search_term, apply_policy],
    output_key="ontology_map",
)

template_generator = LlmAgent(
    name="TemplateGeneratorAgent",
    model=_MODEL,
    description="Generates or repairs an OntoGPT-compliant LinkML / SPIRES schema YAML.",
    instruction=dedent(
        """
        You are an expert LinkML and OntoGPT schema designer.

        Produce a FULL valid LinkML YAML that follows OntoGPT/SPIRES conventions:
        - imports: linkml:types AND core
        - at least one entity class with is_a: NamedEntity
        - exactly one class with tree_root: true
        - relationships (if any): is_a: CompoundExpression

        Emit ONLY the YAML (no markdown fences).

        ### Error-directed repair
        If session state contains a previous validation_result and it is NOT valid:
        - Read validation_result.errors (and stages) carefully.
        - Preserve all parts of the prior schema that are already correct.
        - Change ONLY what is needed to fix the reported defects.
        - Re-emit the complete corrected YAML.

        If there is no prior validation failure, generate a fresh schema from the
        entity types / ontology map / user request.
        You may call persist_template after emitting YAML.
        """
    ),
    tools=[persist_template],
    output_key="generated_schema_yaml",
)

validator = LlmAgent(
    name="ValidatorAgent",
    model=_MODEL,
    description="Validates a LinkML/SPIRES schema via the multi-stage ladder.",
    instruction=dedent(
        """
        Call validate_schema on the FULL generated schema YAML string.
        Report VALID if valid==true, else INVALID plus the errors list and failed stages.
        Do not soften convention failures; they are errors.
        """
    ),
    tools=[validate_schema],
    output_key="validation_result",
)

extractor = LlmAgent(
    name="SPIRESExtractionAgent",
    model=_MODEL,
    description="Runs OntoGPT SPIRES extraction only after successful validation.",
    instruction=dedent(
        """
        Before extracting, inspect validation_result from session state.
        If validation_result.valid is false, DO NOT call extract_with_spires.
        Reply that extraction is blocked and summarize validation errors.

        If validation_result.valid is true:
        Call extract_with_spires with template_yaml, text, validation_valid=true.

        Present outcome explicitly:
          REAL_SUCCESS | SIMULATION_REQUESTED | REAL_EXTRACTION_FAILED
        Never treat a failure as a successful simulation.
        """
    ),
    tools=[extract_with_spires],
    output_key="extraction_result",
)

repair_loop = LoopAgent(
    name="TemplateRepairLoop",
    sub_agents=[template_generator, validator],
    max_iterations=3,
)

root_agent = SequentialAgent(
    name="OntoGPT_Full_Pipeline",
    sub_agents=[ontology_selector, repair_loop, extractor],
    description=(
        "End-to-end agentic OntoGPT pipeline: "
        "ontology selection + policy → error-directed template generate/validate → "
        "gated SPIRES extraction"
    ),
)
