#!/usr/bin/env python3
"""Smoke / pilot benchmark of agentic-ontogpt on MedMentions ST21pv."""
from __future__ import annotations
import argparse, json, re, sys, tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

REPO = Path(__file__).resolve().parents[1]

def load_docs(path, limit=None):
    docs = []
    with Path(path).open() as f:
        for i, line in enumerate(f):
            if limit is not None and i >= limit: break
            docs.append(json.loads(line))
    return docs

def normalize(s):
    return re.sub(r"\s+", " ", s.strip().lower())

def gold_keys(doc):
    keys = set()
    for m in doc.get("mentions") or []:
        st = (m.get("semantic_type") or "").split(",")[0].strip()
        keys.add((normalize(m["text"]), st))
    return keys

def run_spires_extract(text, template_yaml):
    try:
        from ontogpt.engines.spires_engine import SPIRESEngine
        from ontogpt.io.template_loader import get_template_details
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
            f.write(template_yaml); tpl = f.name
        details = get_template_details(template=tpl)
        engine = SPIRESEngine(template_details=details, model="gpt-4o")
        result = engine.extract_from_text(text)
        obj = result.extracted_object
        if hasattr(obj, "dict"): obj = obj.dict()
        elif hasattr(obj, "model_dump"): obj = obj.model_dump()
        mentions = []
        for m in (obj or {}).get("mentions") or []:
            if isinstance(m, dict):
                mentions.append({"text": m.get("label") or m.get("text") or str(m),
                                 "semantic_type": m.get("semantic_type") or ""})
        return mentions, "real_ontogpt"
    except Exception as e:
        return [], f"simulation:{e}"

def pred_keys(mentions):
    keys = set()
    for m in mentions:
        st = (m.get("semantic_type") or "").split(",")[0].strip()
        keys.add((normalize(m.get("text") or ""), st))
    return keys

def score(gold, pred):
    tp, fp, fn = len(gold & pred), len(pred - gold), len(gold - pred)
    p = tp/(tp+fp) if tp+fp else 0.0
    r = tp/(tp+fn) if tp+fn else 0.0
    f1 = 2*p*r/(p+r) if p+r else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": p, "recall": r, "f1": f1}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", default=str(REPO / "data/medmentions/docs_test.jsonl"))
    ap.add_argument("--template", default=str(REPO / "templates/medmentions_st21pv.yaml"))
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--out", default=str(REPO / "benchmarking/medmentions/results/medmentions_eval_results.json"))
    ap.add_argument("--simulate-oracle", action="store_true",
                    help="Plumbing check: predict gold spans (not a real model)")
    args = ap.parse_args()
    docs_path = Path(args.docs)
    if not docs_path.exists():
        print(f"Missing {docs_path}. Run download + convert first.", file=sys.stderr)
        return 1
    docs = load_docs(docs_path, limit=args.limit)
    tpl = Path(args.template).read_text() if Path(args.template).exists() else ""
    agg_g, agg_p = set(), set()
    modes = []
    for doc in docs:
        g = gold_keys(doc)
        if args.simulate_oracle:
            preds = [{"text": m["text"], "semantic_type": m.get("semantic_type", "")}
                     for m in doc.get("mentions") or []]
            mode = "oracle"
        else:
            preds, mode = run_spires_extract(doc.get("text") or "", tpl)
        modes.append(mode)
        p = pred_keys(preds)
        agg_g |= g; agg_p |= p
    metrics = score(agg_g, agg_p)
    out = {
        "n_docs": len(docs),
        "metrics": metrics,
        "modes": list(set(modes)),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "note": "Smoke eval; use lexicon/grounding benchmarks for offline baselines.",
    }
    out_path = Path(args.out); out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2))
    print(json.dumps(metrics, indent=2))
    print(f"Wrote {out_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
