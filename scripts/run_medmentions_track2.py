#!/usr/bin/env python3
"""Track 2 — MedMentions ST21pv evaluation with shared SPIRES outcomes.

Measures: schema gate validity, outcome distribution, failure visibility,
mention-level micro P/R/F1 (text + primary semantic type). Not official CUI linking.

  AGENTIC_ONTOGPT_MODE=simulation python scripts/run_medmentions_track2.py --limit 50
  AGENTIC_ONTOGPT_MODE=real python scripts/run_medmentions_track2.py --limit 20
  python scripts/run_medmentions_track2.py --limit 20 --oracle
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def normalize(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def load_docs(path: Path, limit: int | None = None) -> list[dict]:
    docs: list[dict] = []
    with path.open() as f:
        for i, line in enumerate(f):
            if limit is not None and i >= limit:
                break
            docs.append(json.loads(line))
    return docs


def gold_keys(doc: dict) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for m in doc.get("mentions") or []:
        st = (m.get("semantic_type") or "").split(",")[0].strip()
        keys.add((normalize(m.get("text") or ""), st))
    return keys


def pred_keys(mentions: list[dict]) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for m in mentions:
        st = (m.get("semantic_type") or m.get("type") or "").split(",")[0].strip()
        keys.add((normalize(m.get("text") or m.get("label") or ""), st))
    return keys


def score(gold: set[tuple[str, str]], pred: set[tuple[str, str]]) -> dict[str, float | int]:
    tp = len(gold & pred)
    fp = len(pred - gold)
    fn = len(gold - pred)
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": p, "recall": r, "f1": f1}


def mentions_from_extracted(obj: Any) -> list[dict]:
    mentions: list[dict] = []
    if not isinstance(obj, dict):
        return mentions
    raw = obj.get("mentions")
    if isinstance(raw, list):
        for m in raw:
            if isinstance(m, dict):
                mentions.append(
                    {
                        "text": m.get("label") or m.get("text") or m.get("name") or str(m),
                        "semantic_type": m.get("semantic_type") or m.get("type") or "",
                    }
                )
            elif isinstance(m, str):
                mentions.append({"text": m, "semantic_type": ""})
        return mentions
    for slot, val in obj.items():
        if not isinstance(val, list):
            continue
        for item in val:
            if isinstance(item, dict):
                mentions.append(
                    {
                        "text": item.get("label") or item.get("text") or str(item),
                        "semantic_type": item.get("semantic_type")
                        or item.get("type")
                        or slot,
                    }
                )
            elif isinstance(item, str):
                mentions.append({"text": item, "semantic_type": slot})
    return mentions


def extract_one(text: str, template_yaml: str, *, oracle_mentions: list[dict] | None = None) -> dict:
    if oracle_mentions is not None:
        return {
            "outcome": "ORACLE",
            "mode": "oracle_gold",
            "mentions": oracle_mentions,
            "error_type": None,
            "message": "oracle from gold spans (plumbing only)",
        }
    from tools.spires import run_spires_extraction

    result = run_spires_extraction(
        template_yaml,
        text,
        schema_name="medmentions_st21pv",
        require_valid_schema=True,
    )
    outcome = result.get("outcome") or "REAL_EXTRACTION_FAILED"
    return {
        "outcome": outcome,
        "mode": result.get("mode"),
        "mentions": mentions_from_extracted(result.get("extracted_object")),
        "error_type": result.get("error_type"),
        "message": result.get("message"),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Track 2 MedMentions ST21pv evaluation")
    ap.add_argument("--docs", default=str(REPO / "data/medmentions/docs_test.jsonl"))
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--oracle", action="store_true")
    ap.add_argument("--out", default=str(REPO / "benchmarking/medmentions/results_track2"))
    ap.add_argument("--mode", default=None, help="Override AGENTIC_ONTOGPT_MODE")
    args = ap.parse_args()
    if args.mode:
        os.environ["AGENTIC_ONTOGPT_MODE"] = args.mode

    docs_path = Path(args.docs)
    if not docs_path.exists():
        print("ERROR: run download + convert_medmentions first", file=sys.stderr)
        return 1
    tpl_path = REPO / "templates" / "medmentions_st21pv.yaml"
    if not tpl_path.exists():
        print("ERROR: missing template", tpl_path, file=sys.stderr)
        return 1
    template_yaml = tpl_path.read_text()

    from tools.schema_gate import gate_schema_for_extraction

    gate = gate_schema_for_extraction(template_yaml, revalidate=True)
    schema_valid = gate.allowed
    docs = load_docs(docs_path, limit=args.limit)
    now = datetime.now(timezone.utc)
    run_id = now.strftime("%Y%m%dT%H%M%SZ")

    outcome_counts: Counter[str] = Counter()
    total_tp = total_fp = total_fn = 0
    per_doc: list[dict] = []

    for doc in docs:
        gkeys = gold_keys(doc)
        if args.oracle:
            oracle = [
                {
                    "text": m["text"],
                    "semantic_type": (m.get("semantic_type") or "").split(",")[0],
                }
                for m in doc.get("mentions") or []
            ]
            ext = extract_one(doc["text"], template_yaml, oracle_mentions=oracle)
        else:
            ext = extract_one(doc["text"], template_yaml)
        outcome_counts[ext["outcome"]] += 1
        pkeys = pred_keys(ext["mentions"])
        s = score(gkeys, pkeys)
        total_tp += int(s["tp"])
        total_fp += int(s["fp"])
        total_fn += int(s["fn"])
        per_doc.append(
            {
                "pmid": doc.get("pmid"),
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
        "benchmark": "MedMentions ST21pv",
        "track": 2,
        "run_id": run_id,
        "timestamp_utc": now.isoformat(),
        "n_docs": n,
        "control_plane": {
            "schema_gate_valid": schema_valid,
            "outcome_counts": dict(outcome_counts),
            "failure_visibility": failure_visibility,
            "pct_real_failed": outcome_counts.get("REAL_EXTRACTION_FAILED", 0) / n if n else 0.0,
        },
        "scores": {
            "micro_precision": micro_p,
            "micro_recall": micro_r,
            "micro_f1": micro_f1,
            "tp": total_tp,
            "fp": total_fp,
            "fn": total_fn,
            "not_official_cui_linking": True,
        },
        "per_doc": per_doc,
        "limits": [
            "Not official MedMentions CUI-linking evaluation",
            "Simulation fixture is not quality evidence",
            "Real mode requires ontogpt + API key",
        ],
    }
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "medmentions_track2_results.json").write_text(json.dumps(results, indent=2))
    (out_dir / "provenance.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "template_sha256": sha256_file(tpl_path),
                "script_sha256": sha256_file(Path(__file__)),
                "n_docs": n,
                "env_mode": os.environ.get("AGENTIC_ONTOGPT_MODE", "real"),
                "dataset": "MedMentions ST21pv (CC0)",
            },
            indent=2,
        )
    )
    print(f"Schema gate valid: {schema_valid}")
    print(f"Outcomes: {dict(outcome_counts)}")
    print(f"Micro P/R/F1: {micro_p:.4f} / {micro_r:.4f} / {micro_f1:.4f}")
    print(f"Wrote {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
