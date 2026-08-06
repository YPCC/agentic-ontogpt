"""BioPortal API tools (Recommender + Search)."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests

BIOPORTAL_BASE = "https://data.bioontology.org"


def _api_key() -> str:
    key = os.environ.get("BIOPORTAL_API_KEY")
    if not key:
        raise RuntimeError("BIOPORTAL_API_KEY environment variable is required")
    return key


def bioportal_recommend_ontology(entities: str, max_results: int = 5) -> Dict[str, Any]:
    """Recommend the best BioPortal ontologies for clinical entities (keywords)."""
    url = f"{BIOPORTAL_BASE}/recommender"
    params = {
        "apikey": _api_key(),
        "input": entities,
        "input_type": 2,
        "output_type": 1,
        "wc": 0.55,
        "wa": 0.15,
        "wd": 0.15,
        "ws": 0.15,
    }
    try:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        recs = []
        for item in data[:max_results]:
            ont = item.get("ontology", {})
            recs.append(
                {
                    "acronym": ont.get("acronym"),
                    "name": ont.get("name"),
                    "score": item.get("score"),
                }
            )
        return {"status": "success", "recommendations": recs}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def bioportal_search_term(
    query: str, ontologies: Optional[str] = None, pagesize: int = 5
) -> Dict[str, Any]:
    """Search BioPortal for a clinical term."""
    url = f"{BIOPORTAL_BASE}/search"
    params = {
        "apikey": _api_key(),
        "q": query,
        "pagesize": pagesize,
        "display_context": "false",
        "include": "prefLabel,synonym",
    }
    if ontologies:
        params["ontologies"] = ontologies
    try:
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        results = []
        for item in r.json().get("collection", []):
            results.append(
                {
                    "id": item.get("@id"),
                    "prefLabel": item.get("prefLabel"),
                    "ontology": item.get("links", {}).get("ontology", "").split("/")[-1],
                }
            )
        return {"status": "success", "results": results}
    except Exception as e:
        return {"status": "error", "error": str(e)}
