"""Export extraction results to RDF Turtle + optional SHACL (P2)."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from urllib.parse import quote


def _curie_or_iri(value, base="https://w3id.org/agentic-ontogpt/res/"):
    v = (value or "").strip()
    if not v:
        return f"<{base}unknown>"
    if v.startswith("http://") or v.startswith("https://"):
        return f"<{v}>"
    if re.match(r"^[A-Za-z][A-Za-z0-9_\-]*:[A-Za-z0-9_\-./]+$", v):
        return v
    return f"<{base}{quote(v, safe='')}>"


def _lit(s):
    esc = (s or "").replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{esc}"'


def extraction_to_turtle(extracted_object, *, grounded=None, named_entities=None,
                         base_iri="https://w3id.org/agentic-ontogpt/res/",
                         graph_id="https://w3id.org/agentic-ontogpt/graph/run"):
    prefixes = [
        "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        "@prefix ao: <https://w3id.org/agentic-ontogpt/vocab/> .",
        "@prefix prov: <http://www.w3.org/ns/prov#> .",
        f"@prefix res: <{base_iri}> .", "",
    ]
    triples = [f"<{graph_id}> a ao:ExtractionGraph .", ""]

    def emit_entity(node, label, typ=None, cui=None):
        triples.append(f"{node} a ao:Mention ;")
        triples.append(f"    rdfs:label {_lit(label)} ;")
        if typ:
            triples.append(f"    ao:entityType {_lit(typ)} ;")
        if cui:
            triples.append(f"    ao:groundedTo {_curie_or_iri(cui, base_iri)} ;")
        triples.append(f"    prov:wasDerivedFrom <{graph_id}> .")
        triples.append("")

    for i, ne in enumerate(named_entities or []):
        if not isinstance(ne, dict):
            continue
        label = str(ne.get("label") or ne.get("text") or f"entity_{i}")
        eid = ne.get("id") or ne.get("cui")
        node = _curie_or_iri(str(eid) if eid else f"ne/{i}", base_iri)
        emit_entity(node, label, ne.get("type"), str(eid) if eid else None)

    for i, g in enumerate(grounded or []):
        if not isinstance(g, dict):
            continue
        label = str(g.get("text") or f"mention_{i}")
        cui = g.get("cui")
        node = _curie_or_iri(str(cui) if cui else f"m/{i}", base_iri)
        emit_entity(node, label, g.get("type_hint") or g.get("semantic_type"), cui)

    def walk(obj, path="root"):
        if isinstance(obj, dict):
            label = obj.get("label") or obj.get("text")
            if isinstance(label, str):
                eid = obj.get("id") or obj.get("cui")
                node = _curie_or_iri(str(eid) if eid else f"path/{quote(path, safe='')}", base_iri)
                emit_entity(node, label, path.split(".")[-1], str(eid) if eid else None)
            for k, v in obj.items():
                walk(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                walk(item, f"{path}[{i}]")

    if extracted_object is not None:
        walk(extracted_object)
    return "\n".join(prefixes + triples)


DEFAULT_SHACL = """@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix ao: <https://w3id.org/agentic-ontogpt/vocab/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
ao:MentionShape a sh:NodeShape ;
  sh:targetClass ao:Mention ;
  sh:property [ sh:path rdfs:label ; sh:minCount 1 ; ] .
"""


def validate_turtle_shacl(data_turtle, shapes_turtle=None):
    shapes = shapes_turtle or DEFAULT_SHACL
    try:
        from pyshacl import validate
    except Exception:
        n_mentions = data_turtle.count("a ao:Mention")
        n_labels = data_turtle.count("rdfs:label")
        return {"conforms": n_mentions == 0 or n_labels >= n_mentions,
                "engine": "structural_fallback", "n_mentions": n_mentions, "n_labels": n_labels,
                "message": "pyshacl not installed; structural label check only"}
    try:
        conforms, _, results_text = validate(
            data_graph=data_turtle, data_graph_format="turtle",
            shacl_graph=shapes, shacl_graph_format="turtle", inference="rdfs")
        return {"conforms": bool(conforms), "engine": "pyshacl",
                "results_text": str(results_text)[:2000]}
    except Exception as e:
        return {"conforms": False, "engine": "pyshacl", "error": str(e)}


def export_and_validate(extraction_result, *, grounding_report=None):
    obj = extraction_result.get("extracted_object")
    named = extraction_result.get("named_entities") or []
    grounded = (grounding_report or {}).get("grounded") or []
    ttl = extraction_to_turtle(obj, grounded=grounded, named_entities=named)
    return {"turtle": ttl, "shacl": validate_turtle_shacl(ttl), "n_chars": len(ttl)}
