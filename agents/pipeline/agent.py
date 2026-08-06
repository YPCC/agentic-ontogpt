"""Root pipeline agent for agentic-ontogpt.

Orchestrates:
  OntologySelector -> (TemplateGenerator <-> Validator)* -> SPIRESExtraction
"""

from __future__ import annotations

from textwrap import dedent

from google.adk.agents import LlmAgent, LoopAgent, SequentialAgent

try:
    from tools.bioportal import bioportal_recommend_ontology, bioportal_search_term
    from tools.linkml_tools import validate_linkml_schema, save_template_yaml
    from tools.spires import run_spires_extraction
except ImportError:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tools.bioportal import bioportal_recommend_ontology, bioportal_search_term
    from tools.linkml_tools import validate_linkml_schema, save_template_yaml
    from tools.spires import run_spires_extraction


def recommend_ontologies(entities: str) -> dict:
    """Recommend BioPortal ontologies for a comma-separated list of clinical entities."""
    return bioportal_recommend_ontology(entities)


def search_term(query: str, ontologies: str = None) -> dict:
    """Search BioPortal for a clinical term."""
    return bioportal_search_term(query, ontologies=ontologies)


def validate_schema(schema_yaml: str) -> dict:
    """Validate a LinkML / SPIRES schema YAML string."""
    return validate_linkml_schema(schema_yaml)


def persist_template(schema_yaml: str, schema_name: str = "clinical_extraction") -> dict:
    """Save the generated YAML template to disk."""
    return save_template_yaml(schema_yaml, schema_name)


def extract_with_spires(
    template_yaml: str, text: str, schema_name: str = "clinical_extraction"
) -> dict:
    """Run SPIRES extraction (OntoGPT) on the given text using the provided template."""
    return run_spires_extraction(template_yaml, text, schema_name=schema_name)


ontology_selector = LlmAgent(
    name="OntologySelectorAgent",
    model="gemini-2.0-flash",
    description="Selects the best BioPortal ontology for each clinical entity type.",
    instruction=dedent(
        """
        You are a biomedical ontology expert.
        Given entity types or concrete clinical terms, call recommend_ontologies
        (and search_term if needed) and return a clear mapping:

            EntityType -> OntologyAcronym

        Prefer high-quality ontologies (MONDO, HP, GO, CHEBI, HGNC, NCIT, DRON, ...).
        Always give a short justification.
        """
    ),
    tools=[recommend_ontologies, search_term],
    output_key="ontology_map",
)

template_generator = LlmAgent(
    name="TemplateGeneratorAgent",
    model="gemini-2.0-flash",
    description="Generates an OntoGPT-compliant LinkML / SPIRES schema YAML.",
    instruction=dedent(
        """
        You are an expert LinkML and OntoGPT schema designer.
        Produce a FULL valid LinkML YAML that follows OntoGPT/SPIRES conventions:

        - imports: linkml:types AND core
        - entity classes: is_a: NamedEntity + annotations.annotators: bioportal:ONTOLOGY
        - root class: tree_root: true
        - relationships: is_a: CompoundExpression

        Emit ONLY the YAML (no markdown fences). You may call persist_template after.
        """
    ),
    tools=[persist_template],
    output_key="generated_schema_yaml",
)

validator = LlmAgent(
    name="ValidatorAgent",
    model="gemini-2.0-flash",
    description="Validates a LinkML/SPIRES schema.",
    instruction=dedent(
        """
        Call validate_schema on the full YAML string.
        Reply VALID if valid==true, otherwise INVALID + the error messages.
        """
    ),
    tools=[validate_schema],
    output_key="validation_result",
)

extractor = LlmAgent(
    name="SPIRESExtractionAgent",
    model="gemini-2.0-flash",
    description="Runs OntoGPT SPIRES extraction using a validated template.",
    instruction=dedent(
        """
        Call extract_with_spires with the validated template YAML and the clinical text.
        Present the structured extracted_object and grounded named_entities clearly.
        State whether real OntoGPT or simulation mode was used.
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
        "ontology selection -> template generation/repair -> SPIRES extraction"
    ),
)
