"""Mention grounding — distinct from ontology selection (P2)."""

from __future__ import annotations

import os
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

import requests

BIOPORTAL_BASE = "https://data.bioontology.org"


@dataclass
class GroundedMention:
    text: str
    start: Optional[int] = None
    end: Optional[int] = None
    semantic_type: Optional[str] = None
    ontology: Optional[str] = None
    cui: Optional[str] = None
    preferred_label: Optional[str] = None
    score: Optional[float] = None
    status: str = "ungrounded"
    candidates: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _api_key() -> Optional[str]:
    return os.environ.get("BIOPORTAL_API_KEY")


def ground_mention_bioportal(text: str, ontology: str, *, longest_only: bool = True) -> List[GroundedMention]:
    key = _api_key()
    if not key:
        return [GroundedMention(text=text, ontology=ontology, status="ungrounded",
                                candidates=[{"error": "BIOPORTAL_API_KEY not set"}])]
    try:
        r = requests.get(
            f"{BIOPORTAL_BASE}/annotator",
            params={"apikey": key, "text": text, "ontologies": ontology.upper(),
                    "longest_only": str(longest_only).lower()},
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return [GroundedMention(text=text, ontology=ontology, status="ungrounded",
                                candidates=[{"error": str(e)}])]
    if not data:
        return [GroundedMention(text=text, ontology=ontology, status="ungrounded")]
    results = []
    for hit in data:
        classes = hit.get("annotatedClass") or {}
        cui = classes.get("@id") or classes.get("id")
        if isinstance(cui, str) and "/" in cui:
            short = cui.rstrip("/").split("/")[-1]
            if short:
                cui = f"{ontology.upper()}:{short}" if ":" not in short else short
        for ann in hit.get("annotations") or [{"text": text}]:
            results.append(GroundedMention(
                text=ann.get("text") or text, start=ann.get("from"), end=ann.get("to"),
                ontology=ontology.upper(), cui=cui,
                status="grounded" if cui else "ungrounded",
                candidates=[{"id": classes.get("@id")}]))
    return results or [GroundedMention(text=text, ontology=ontology, status="ungrounded")]


def ground_mentions_dictionary(mentions, lexicon, *, ontology="LOCAL"):
    out = []
    for m in mentions:
        text = m.get("text") or m.get("label") or ""
        key = re.sub(r"\s+", " ", text.strip().lower())
        cui = lexicon.get(key)
        out.append(GroundedMention(
            text=text, start=m.get("start"), end=m.get("end"),
            semantic_type=m.get("semantic_type") or m.get("type"),
            ontology=ontology if cui else (m.get("ontology") or ontology),
            cui=cui, preferred_label=text if cui else None,
            status="grounded" if cui else "ungrounded"))
    return out


def ground_extraction_object(extracted_object, ontology_map, *, use_bioportal=False, lexicon=None):
    lexicon = lexicon or {}
    grounded, ungrounded = [], []

    def _ground_label(label, type_hint, extra=None):
        extra = extra or {}
        ont = ontology_map.get(type_hint or "") or ontology_map.get((type_hint or "").lower()) or extra.get("ontology")
        if use_bioportal and ont:
            for h in ground_mention_bioportal(label, str(ont)):
                d = h.to_dict(); d["type_hint"] = type_hint
                (grounded if h.status in ("grounded", "ambiguous") else ungrounded).append(d)
            return
        key = re.sub(r"\s+", " ", label.strip().lower())
        cui = lexicon.get(key) or extra.get("id") or extra.get("cui")
        gm = GroundedMention(text=label, ontology=str(ont) if ont else None, cui=cui if cui else None,
                             status="grounded" if cui else "ungrounded", semantic_type=type_hint)
        d = gm.to_dict(); d["type_hint"] = type_hint
        (grounded if gm.status == "grounded" else ungrounded).append(d)

    def walk(obj, type_hint=None):
        if isinstance(obj, dict):
            label = obj.get("label") or obj.get("text") or obj.get("name")
            if label and isinstance(label, str):
                _ground_label(label, type_hint, obj)
            for k, v in obj.items():
                if k in ("label", "text", "name", "id", "cui", "ontology"):
                    continue
                walk(v, type_hint=k if isinstance(k, str) else type_hint)
        elif isinstance(obj, list):
            for item in obj:
                walk(item, type_hint=type_hint)
        elif isinstance(obj, str) and type_hint:
            _ground_label(obj, type_hint)

    if isinstance(extracted_object, dict):
        walk(extracted_object)
    n = len(grounded) + len(ungrounded)
    return {"grounded": grounded, "ungrounded": ungrounded, "n_grounded": len(grounded),
            "n_ungrounded": len(ungrounded), "grounding_rate": (len(grounded) / n) if n else 0.0,
            "note": "Ontology selection chooses the vocabulary; grounding links spans to concepts."}
