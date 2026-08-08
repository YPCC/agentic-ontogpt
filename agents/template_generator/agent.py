"""Modular TemplateGenerator agent (ADK LlmAgent factory)."""
from __future__ import annotations

from textwrap import dedent
from typing import Any, Optional


def _tools():
    try:
        from tools.linkml_tools import save_template_yaml
    except ImportError:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from tools.linkml_tools import save_template_yaml

    def persist_template(schema_yaml: str, schema_name: str = "clinical_extraction") -> dict:
        return save_template_yaml(schema_yaml, schema_name)

    return [persist_template]


INSTRUCTION = dedent(
    """
    You are an expert LinkML and OntoGPT schema designer.

    Produce a FULL valid LinkML YAML that follows OntoGPT/SPIRES conventions:
    - imports: linkml:types AND core
    - at least one entity class with is_a: NamedEntity
    - exactly one class with tree_root: true
    - relationships (if any): is_a: CompoundExpression
    - optional annotations.annotators: bioportal:ONTOLOGY on entities

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
)


def build_template_generator(model: Optional[str] = None) -> Any:
    from google.adk.agents import LlmAgent
    try:
        from tools.modes import get_adk_model
        model = model or get_adk_model()
    except Exception:
        model = model or "gemini-2.0-flash"
    return LlmAgent(
        name="TemplateGeneratorAgent",
        model=model,
        description="Generates or repairs an OntoGPT-compliant LinkML / SPIRES schema YAML.",
        instruction=INSTRUCTION,
        tools=_tools(),
        output_key="generated_schema_yaml",
    )
