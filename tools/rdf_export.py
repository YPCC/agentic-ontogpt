"""Export structured extraction results to RDF Turtle + optional SHACL.

Serialization expands or declares ontology prefixes so CURIEs such as
``MONDO:0005105`` are valid Turtle. Validation always attempts RDFLib parse
before SHACL; without pyshacl/rdflib we report ``structural_skip`` and never
claim SHACL conformance.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import quote

KNOWN_PREFIXES: Dict[str, str] = {
    "MONDO": "http://purl.obolibrary.org/obo/MONDO_",
    "HP": "http://purl.obolibrary.org/obo/HP_",
    "CHEBI": "http://purl.obolibrary.org/obo/CHEBI_",
    "GO": "http://purl.obolibrary.org/obo/GO_",
    "UBERON": "http://purl.obolibrary.org/obo/UBERON_",
    "NCBITaxon": "http://purl.obolibrary.org/obo/NCBITaxon_",
    "PR": "http://purl.obolibrary.org/obo/PR_",
    "SO": "http://purl.obolibrary.org/obo/SO_",
    "CL": "http://purl.obolibrary.org/obo/CL_",
    "MAXO": "http://purl.obolibrary.org/obo/MAXO_",
    "DRON": "http://purl.obolibrary.org/obo/DRON_",
    "RXNORM": "http://purl.bioontology.org/ontology/RXNORM/",
    "MEDDRA": "http://purl.bioontology.org/ontology/MEDDRA/",
    "SNOMEDCT": "http://snomed.info/id/",
    "NCIT": "http://purl.obolibrary.org/obo/NCIT_",
    "HGNC": "http://identifiers.org/hgnc/",
    "MESH": "http://id.nlm.nih.gov/mesh/",
    "UMLS": "http://linkedlifedata.com/resource/umls/id/",
    "OMIM": "http://purl.obolibrary.org/obo/OMIM_",
}


def _curie_match(value: str) -> Optional[Tuple[str, str]]:
    m = re.match(r"^([A-Za-z][A-Za-z0-9_\-]*):([A-Za-z0-9_\-./]+)$", (value or "").strip())
    if not m:
        return None
    return m.group(1), m.group(2)


def _curie_or_iri(
    value: str,
    base: str = "https://w3id.org/agentic-ontogpt/res/",
    used_prefixes: Optional[Set[str]] = None,
    expand_unknown: bool = True,
) -> str:
    v = (value or "").strip()
    if not v:
        return f"<{base}unknown>"
    if v.startswith("http://") or v.startswith("https://"):
        return f"<{v}>"
    cm = _curie_match(v)
    if cm:
        pref, local = cm
        if pref in KNOWN_PREFIXES:
            if used_prefixes is not None:
                used_prefixes.add(pref)
            return f"{pref}:{local}"
        if expand_unknown:
            return f"<{base}curie/{quote(pref, safe='')}/{quote(local, safe='')}>"
        if used_prefixes is not None:
            used_prefixes.add(pref)
        return f"{pref}:{local}"
    safe = quote(v, safe="")
    return f"<{base}{safe}>"


def _lit(s: str) -> str:
    esc = (s or "").replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{esc}"'


def extraction_to_turtle(
    extracted_object: Any,
    *,
    grounded: Optional[List[Dict[str, Any]]] = None,
    named_entities: Optional[List[Dict[str, Any]]] = None,
    base_iri: str = "https://w3id.org/agentic-ontogpt/res/",
    graph_id: str = "https://w3id.org/agentic-ontogpt/graph/run",
) -> str:
    used: Set[str] = set()
    triples: List[str] = [f"<{graph_id}> a ao:ExtractionGraph .", ""]

    def term(val: str) -> str:
        return _curie_or_iri(val, base_iri, used_prefixes=used)

    def emit_entity(node: str, label: str, typ: Optional[str] = None, concept_id: Optional[str] = None) -> None:
        triples.append(f"{node} a ao:Mention ;")
        triples.append(f"    rdfs:label {_lit(label)} ;")
        if typ:
            triples.append(f"    ao:entityType {_lit(typ)} ;")
        if concept_id:
            triples.append(f"    ao:groundedTo {term(concept_id)} ;")
        triples.append(f"    prov:wasDerivedFrom <{graph_id}> .")
        triples.append("")

    for i, g in enumerate(grounded or []):
        label = str(g.get("text") or g.get("label") or g.get("mention") or "")
        cid = g.get("concept_id") or g.get("cui") or g.get("id")
        typ = g.get("entity_type") or g.get("type")
        node = term(str(cid) if cid else f"g/{i}")
        emit_entity(node, label, str(typ) if typ else None, str(cid) if cid else None)

    for i, ne in enumerate(named_entities or []):
        if not isinstance(ne, dict):
            continue
        label = str(ne.get("label") or ne.get("text") or ne.get("name") or "")
        eid = ne.get("id") or ne.get("concept_id") or ne.get("cui")
        node = term(str(eid) if eid else f"ne/{i}")
        emit_entity(node, label, ne.get("entity_type") or ne.get("type"), str(eid) if eid else None)

    def walk(obj: Any, path: str = "root") -> None:
        if isinstance(obj, dict):
            label = obj.get("label") or obj.get("name") or obj.get("text")
            eid = obj.get("id") or obj.get("concept_id") or obj.get("cui")
            if label:
                node = term(str(eid) if eid else f"path/{quote(path, safe='')}")
                emit_entity(node, str(label), path.split(".")[-1], str(eid) if eid else None)
            for k, v in obj.items():
                walk(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                walk(item, f"{path}[{i}]")
        elif isinstance(obj, str) and path != "root":
            node = term(f"path/{quote(path, safe='')}")
            emit_entity(node, obj, path.split(".")[-1], None)

    if extracted_object is not None:
        walk(extracted_object)

    prefixes = [
        "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .",
        "@prefix ao: <https://w3id.org/agentic-ontogpt/vocab/> .",
        "@prefix prov: <http://www.w3.org/ns/prov#> .",
        f"@prefix res: <{base_iri}> .",
    ]
    for pref in sorted(used):
        iri = KNOWN_PREFIXES.get(pref)
        if iri:
            prefixes.append(f"@prefix {pref}: <{iri}> .")
    prefixes.append("")
    return "\n".join(prefixes + triples)


DEFAULT_SHACL = """@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix ao: <https://w3id.org/agentic-ontogpt/vocab/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

ao:MentionShape a sh:NodeShape ;
  sh:targetClass ao:Mention ;
  sh:property [
    sh:path rdfs:label ;
    sh:minCount 1 ;
    sh:datatype <http://www.w3.org/2001/XMLSchema#string> ;
  ] .
"""


def parse_turtle(data_turtle: str) -> Dict[str, Any]:
    try:
        from rdflib import Graph  # type: ignore
    except Exception as e:
        return {"ok": False, "engine": "rdflib_missing", "error": str(e), "n_triples": 0}
    try:
        g = Graph()
        g.parse(data=data_turtle, format="turtle")
        return {"ok": True, "engine": "rdflib", "n_triples": len(g)}
    except Exception as e:
        return {"ok": False, "engine": "rdflib", "error": str(e), "n_triples": 0}


def validate_turtle_shacl(
    data_turtle: str,
    shapes_turtle: Optional[str] = None,
) -> Dict[str, Any]:
    shapes = shapes_turtle or DEFAULT_SHACL
    parsed = parse_turtle(data_turtle)
    if not parsed.get("ok"):
        if parsed.get("engine") == "rdflib_missing":
            return {
                "conforms": None,
                "engine": "structural_skip",
                "parse": parsed,
                "n_mentions": data_turtle.count("a ao:Mention"),
                "n_labels": data_turtle.count("rdfs:label"),
                "message": "rdflib not installed; cannot parse or run SHACL; no conformance claim",
            }
        return {
            "conforms": False,
            "engine": "parse_failed",
            "parse": parsed,
            "message": "Turtle did not parse; cannot claim SHACL conformance",
        }
    try:
        from pyshacl import validate  # type: ignore
    except Exception:
        return {
            "conforms": None,
            "engine": "structural_skip",
            "parse": parsed,
            "n_mentions": data_turtle.count("a ao:Mention"),
            "n_labels": data_turtle.count("rdfs:label"),
            "message": "pyshacl not installed; RDF parsed OK; SHACL not evaluated",
        }
    try:
        conforms, _, results_text = validate(
            data_graph=data_turtle,
            data_graph_format="turtle",
            shacl_graph=shapes,
            shacl_graph_format="turtle",
            inference="rdfs",
            abort_on_first=False,
            meta_shacl=False,
            advanced=True,
            inplace=False,
        )
        return {
            "conforms": bool(conforms),
            "engine": "pyshacl",
            "parse": parsed,
            "results_text": str(results_text)[:2000],
        }
    except Exception as e:
        return {"conforms": False, "engine": "pyshacl", "parse": parsed, "error": str(e)}


def export_and_validate(
    extraction_result: Dict[str, Any],
    *,
    grounding_report: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    obj = extraction_result.get("extracted_object")
    named = extraction_result.get("named_entities") or []
    grounded = (grounding_report or {}).get("grounded") or []
    ttl = extraction_to_turtle(obj, grounded=grounded, named_entities=named)
    shacl = validate_turtle_shacl(ttl)
    return {"turtle": ttl, "shacl": shacl, "n_chars": len(ttl)}
