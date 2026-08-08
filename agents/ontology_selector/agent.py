"""Modular OntologySelector agent (ADK LlmAgent factory).

Pipeline integration remains in ``agents.pipeline.agent``. This module is the
standalone definition for reuse and gradual migration.
"""
from __future__ import annotations

from textwrap import dedent
from typing import Any, Optional


def _tools():
    try:
        from tools.bioportal import bioportal_recommend_ontology, bioportal_search_term
        from tools.ontology_policy import apply_ontology_policy as _apply_policy
    except ImportError:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from tools.bioportal import bioportal_recommend_ontology, bioportal_search_term
        from tools.ontology_policy import apply_ontology_policy as _apply_policy

    def recommend_ontologies(entities: str) -> dict:
        return bioportal_recommend_ontology(entities)

    def search_term(query: str, ontologies: str = None) -> dict:
        return bioportal_search_term(query, ontologies=ontologies)

    def apply_policy(
        entity_types: str,
        user_preferences_json: str = "{}",
        recommendations_json: str = "[]",
    ) -> dict:
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

    return [recommend_ontologies, search_term, apply_policy]


INSTRUCTION = dedent(
    """
    You are a biomedical ontology expert.
    Given entity types or concrete clinical terms, call recommend_ontologies
    (and search_term if needed) and return a clear mapping:

        EntityType → OntologyAcronym

    Prefer high-quality ontologies (MONDO, HP, GO, CHEBI, HGNC, NCIT, DRON, …).
    Always give a short justification. Apply policy via apply_policy when
    user preferences or recommendation lists are provided.
    """
)


def build_ontology_selector(model: Optional[str] = None) -> Any:
    """Return an ADK LlmAgent for ontology selection."""
    from google.adk.agents import LlmAgent
    try:
        from tools.modes import get_adk_model
        model = model or get_adk_model()
    except Exception:
        model = model or "gemini-2.0-flash"
    return LlmAgent(
        name="OntologySelectorAgent",
        model=model,
        description="Selects the best BioPortal ontology for each clinical entity type.",
        instruction=INSTRUCTION,
        tools=_tools(),
        output_key="ontology_map",
    )
