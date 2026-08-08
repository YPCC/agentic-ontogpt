"""Shared Track-2 evaluation helpers (BC5CDR, BC2GM, MedMentions-style)."""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def normalize(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def load_jsonl(path: Path, limit: int | None = None) -> list[dict]:
    docs: list[dict] = []
    with path.open() as f:
        for i, line in enumerate(f):
            if limit is not None and i >= limit:
                break
            docs.append(json.loads(line))
    return docs


def gold_keys(doc: dict, type_field: str = "type") -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for m in doc.get("entities") or doc.get("mentions") or []:
        typ = (m.get(type_field) or m.get("semantic_type") or m.get("type") or "").strip()
        keys.add((normalize(m.get("text") or m.get("label") or ""), typ))
    return keys


def pred_keys(mentions: list[dict], type_field: str = "type") -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for m in mentions:
        typ = (m.get(type_field) or m.get("semantic_type") or m.get("type") or "").strip()
        keys.add((normalize(m.get("text") or m.get("label") or ""), typ))
    return keys


def score(gold: set[tuple[str, str]], pred: set[tuple[str, str]]) -> dict[str, float | int]:
    tp = len(gold & pred)
    fp = len(pred - gold)
    fn = len(gold - pred)
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": p, "recall": r, "f1": f1}


def mentions_from_extracted(obj: Any, slot_type_map: dict[str, str] | None = None) -> list[dict]:
    mentions: list[dict] = []
    slot_type_map = slot_type_map or {}
    if not isinstance(obj, dict):
        return mentions
    if isinstance(obj.get("mentions"), list):
        for m in obj["mentions"]:
            if isinstance(m, dict):
                mentions.append(
                    {
                        "text": m.get("label") or m.get("text") or str(m),
                        "type": m.get("type") or m.get("semantic_type") or "",
                    }
                )
            elif isinstance(m, str):
                mentions.append({"text": m, "type": ""})
        return mentions
    for slot, val in obj.items():
        if not isinstance(val, list):
            continue
        default_type = slot_type_map.get(slot, slot)
        for item in val:
            if isinstance(item, dict):
                mentions.append(
                    {
                        "text": item.get("label") or item.get("text") or str(item),
                        "type": item.get("type") or item.get("semantic_type") or default_type,
                    }
                )
            elif isinstance(item, str):
                mentions.append({"text": item, "type": default_type})
    return mentions


def extract_one(
    text: str,
    template_yaml: str,
    *,
    schema_name: str,
    oracle_entities: list[dict] | None = None,
    slot_type_map: dict[str, str] | None = None,
) -> dict[str, Any]:
    if oracle_entities is not None:
        return {
            "outcome": "ORACLE",
            "mode": "oracle_gold",
            "mentions": [
                {"text": e.get("text") or "", "type": e.get("type") or e.get("semantic_type") or ""}
                for e in oracle_entities
            ],
            "error_type": None,
            "message": "oracle from gold spans",
        }
    from tools.spires import run_spires_extraction

    result = run_spires_extraction(
        template_yaml, text, schema_name=schema_name, require_valid_schema=True
    )
    return {
        "outcome": result.get("outcome") or "REAL_EXTRACTION_FAILED",
        "mode": result.get("mode"),
        "mentions": mentions_from_extracted(result.get("extracted_object"), slot_type_map),
        "error_type": result.get("error_type"),
        "message": result.get("message"),
    }


def run_track2(
    *,
    benchmark: str,
    docs: list[dict],
    template_yaml: str,
    schema_name: str,
    out_dir: Path,
    oracle: bool = False,
    slot_type_map: dict[str, str] | None = None,
    type_field: str = "type",
    extra_limits: list[str] | None = None,
    template_path: Path | None = None,
    script_path: Path | None = None,
) -> dict[str, Any]:
    from tools.schema_gate import gate_schema_for_extraction

    gate = gate_schema_for_extraction(template_yaml, revalidate=True)
    schema_valid = gate.allowed
    now = datetime.now(timezone.utc)
    run_id = now.strftime("%Y%m%dT%H%M%SZ")
    outcome_counts: Counter[str] = Counter()
    total_tp = total_fp = total_fn = 0
    per_doc: list[dict] = []

    for doc in docs:
        gkeys = gold_keys(doc, type_field=type_field)
        if oracle:
            ents = doc.get("entities") or doc.get("mentions") or []
            ext = extract_one(
                doc.get("text") or "",
                template_yaml,
                schema_name=schema_name,
                oracle_entities=ents,
                slot_type_map=slot_type_map,
            )
        else:
            ext = extract_one(
                doc.get("text") or "",
                template_yaml,
                schema_name=schema_name,
                slot_type_map=slot_type_map,
            )
        outcome_counts[ext["outcome"]] += 1
        pkeys = pred_keys(ext["mentions"])
        s = score(gkeys, pkeys)
        total_tp += int(s["tp"])
        total_fp += int(s["fp"])
        total_fn += int(s["fn"])
        per_doc.append(
            {
                "id": doc.get("id") or doc.get("pmid"),
                "n_gold": len(gkeys),
                "n_pred": len(pkeys),
                "outcome": ext["outcome"],
                "error_type": ext.get("error_type"),
                "f1": s["f1"],
            }
        )

    n = len(docs)
    micro_p = total_tp / (total_tp + total_fp) if (total_tp + total_fp) else 0.0
    micro_r = total_tp / (total_tp + total_fn) if (total_tp + total_fn) else 0.0
    micro_f1 = 2 * micro_p * micro_r / (micro_p + micro_r) if (micro_p + micro_r) else 0.0
    failure_visibility = 1.0 if all(d.get("outcome") for d in per_doc) else 0.0

    results = {
        "benchmark": benchmark,
        "track": 2,
        "run_id": run_id,
        "timestamp_utc": now.isoformat(),
        "n_docs": n,
        "execution": {
            "AGENTIC_ONTOGPT_MODE": os.environ.get("AGENTIC_ONTOGPT_MODE", "real"),
            "oracle": oracle,
        },
        "control_plane": {
            "schema_gate_valid": schema_valid,
            "outcome_counts": dict(outcome_counts),
            "failure_visibility": failure_visibility,
        },
        "scores": {
            "micro_precision": micro_p,
            "micro_recall": micro_r,
            "micro_f1": micro_f1,
            "tp": total_tp,
            "fp": total_fp,
            "fn": total_fn,
        },
        "per_doc": per_doc,
        "limits": extra_limits
        or ["Simulation is not quality evidence", "Real mode requires ontogpt + API key"],
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = benchmark.lower().replace(" ", "_")
    (out_dir / f"{slug}_track2_results.json").write_text(json.dumps(results, indent=2))
    (out_dir / "provenance.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "benchmark": benchmark,
                "n_docs": n,
                "env_mode": os.environ.get("AGENTIC_ONTOGPT_MODE", "real"),
                "schema_gate_valid": schema_valid,
            },
            indent=2,
        )
    )
    (out_dir / "comparison_table.md").write_text(
        f"# {benchmark} Track 2\n\n"
        f"schema_gate={schema_valid} outcomes={dict(outcome_counts)}\n"
        f"P/R/F1={micro_p:.4f}/{micro_r:.4f}/{micro_f1:.4f}\n"
    )
    print(f"[{benchmark}] schema_gate={schema_valid} outcomes={dict(outcome_counts)}")
    print(f"[{benchmark}] micro P/R/F1={micro_p:.4f}/{micro_r:.4f}/{micro_f1:.4f}")
    print(f"[{benchmark}] wrote {out_dir}")
    return results
