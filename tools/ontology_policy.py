"""Deterministic ontology policy engine (P1)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

DEFAULT_POLICY_PATH = Path(__file__).resolve().parents[1] / "configs" / "ontology_policy.yaml"


def load_ontology_policy(path: Optional[str | Path] = None) -> Dict[str, Any]:
    p = Path(path) if path else DEFAULT_POLICY_PATH
    if not p.exists():
        return {"version": "0.0.0", "allowlist": [], "denylist": [],
                "preferred_by_entity_type": {}, "min_recommender_score": 0.0,
                "fallback_to_preferred": True}
    return yaml.safe_load(p.read_text()) or {}


def _norm_key(s: str) -> str:
    return "".join(ch for ch in (s or "").lower() if ch.isalnum())


def apply_ontology_policy(
    entity_types: List[str],
    recommendations: Optional[List[Dict[str, Any]]] = None,
    user_preferences: Optional[Dict[str, str]] = None,
    policy: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    pol = policy or load_ontology_policy()
    allow = {a.upper() for a in (pol.get("allowlist") or [])}
    deny = {a.upper() for a in (pol.get("denylist") or [])}
    preferred = {_norm_key(k): str(v).upper()
                 for k, v in (pol.get("preferred_by_entity_type") or {}).items()}
    min_score = float(pol.get("min_recommender_score") or 0.0)
    user_preferences = {k: str(v).upper() for k, v in (user_preferences or {}).items()}

    def allowed(acro: str):
        a = (acro or "").upper()
        if not a:
            return False, "empty_acronym"
        if a in deny:
            return False, "denylist"
        if allow and a not in allow:
            return False, "not_on_allowlist"
        return True, "ok"

    ranked = []
    for item in recommendations or []:
        acro = (item.get("acronym") or "").upper()
        score = float(item.get("score") or 0.0)
        ok, _ = allowed(acro)
        if ok and score >= min_score:
            ranked.append({"acronym": acro, "score": score, "name": item.get("name")})
    ranked.sort(key=lambda x: x["score"], reverse=True)

    selected, rejected, reasons = {}, [], {}
    for et in entity_types:
        key = _norm_key(et)
        if et in user_preferences or key in {_norm_key(k) for k in user_preferences}:
            pref = user_preferences.get(et) or next(
                (user_preferences[k] for k in user_preferences if _norm_key(k) == key), None)
            if pref:
                ok, reason = allowed(pref)
                if ok:
                    selected[et] = pref
                    reasons[et] = "user_preference"
                    continue
                rejected.append({"entity": et, "acronym": pref, "reason": reason})
        if key in preferred:
            pref = preferred[key]
            ok, reason = allowed(pref)
            if ok:
                selected[et] = pref
                reasons[et] = "preferred_by_entity_type"
                continue
            rejected.append({"entity": et, "acronym": pref, "reason": reason})
        if ranked:
            selected[et] = ranked[0]["acronym"]
            reasons[et] = f"bioportal_score:{ranked[0]['score']}"
            continue
        reasons[et] = "unresolved"
    return {
        "status": "success",
        "selected": selected,
        "rejected": rejected,
        "reasons": reasons,
        "ranked_allowed_recommendations": ranked[:10],
        "policy_version": pol.get("version"),
    }
