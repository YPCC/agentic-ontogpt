#!/usr/bin/env python3
"""Smoke PII/PHI extraction + F1 on PIIMB (HF) and ASQ-PHI (local/GitHub).

Usage:
  python scripts/run_pii_smoke.py --limit 50
  OPENAI_API_KEY=... python scripts/run_pii_smoke.py --backend gpt --limit 20

Heuristic regex is the default offline baseline. GPT path is optional.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def extract_heuristic(text: str):
    found = []
    patterns = [
        ("EMAIL_ADDRESS", r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        ("EMAIL", r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        ("PHONE_NUMBER", r"\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b"),
        ("TELEPHONENUM", r"\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b"),
        ("SOCIAL_SECURITY_NUMBER", r"\b\d{3}-\d{2}-\d{4}\b"),
        ("SOCIALNUM", r"\b\d{3}-\d{2}-\d{4}\b"),
        (
            "DATE",
            r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
            r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|"
            r"Dec(?:ember)?)\.?\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}\b",
        ),
        ("DATE", r"\b\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b"),
        ("MEDICAL_RECORD_NUMBER", r"\b(?:MRN|ID)[:\s#]*([A-Za-z0-9-]{5,})\b"),
    ]
    for label, pat in patterns:
        for m in re.finditer(pat, text, flags=re.I):
            val = m.group(1) if m.lastindex else m.group(0)
            found.append({"label": label, "value": val})
    for m in re.finditer(
        r"\b((?:Mr|Mrs|Ms|Miss|Dr|Prof)\.?)\s+([A-Z][a-z]+(?:\s+[A-Z]\.?)?(?:\s+[A-Z][a-z]+)?)\b",
        text,
    ):
        found.append({"label": "NAME", "value": m.group(2)})
        found.append({"label": "GIVENNAME", "value": m.group(2).split()[0]})
    for m in re.finditer(r"\b([A-Z][a-z]+)\s+([A-Z])\.\b", text):
        found.append({"label": "NAME", "value": m.group(0)})
        found.append({"label": "GIVENNAME", "value": m.group(1)})
        found.append({"label": "SURNAME", "value": m.group(2) + "."})
    for m in re.finditer(
        r"\b((?:[A-Z][A-Za-z'\.]+(?:\s+|&\s+)?){1,4}"
        r"(?:Hospital|Medical Center|Clinic|Health(?:care)?|Mt\.?\s+Sinai|UCLA|Mayo Clinic))\b",
        text,
    ):
        found.append({"label": "GEOGRAPHIC_LOCATION", "value": m.group(1)})
    for m in re.finditer(r"\b(?:in|on|since)\s+((?:19|20)\d{2})\b", text, re.I):
        found.append({"label": "DATE", "value": m.group(1)})
    return found


def extract_gpt(text: str, labels: list):
    import os

    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        return None
    from openai import OpenAI

    client = OpenAI(api_key=key)
    prompt = (
        "Extract PII/PHI spans. Return ONLY a JSON array of "
        '{"label": "...", "value": "..."}. Preferred labels: '
        f"{labels}.\n\nText:\n{text}"
    )
    resp = client.chat.completions.create(
        model=os.environ.get("SPIRES_LLM_MODEL", "gpt-4o-mini"),
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    content = resp.choices[0].message.content or "[]"
    m = re.search(r"\[.*\]", content, re.S)
    if not m:
        return []
    return [
        {"label": i.get("label") or i.get("type") or "UNKNOWN", "value": str(i.get("value") or i.get("text") or "")}
        for i in json.loads(m.group(0))
        if i.get("value") or i.get("text")
    ]


def score(gold, pred):
    gv = [norm(e.get("value") or "") for e in gold]
    gv = [x for x in gv if x]
    pv = [norm(e.get("value") or "") for e in pred]
    pv = [x for x in pv if x]
    gset, pset = Counter(gv), Counter(pv)
    tp = sum(min(gset[k], pset.get(k, 0)) for k in gset)
    fp, fn = sum(pset.values()) - tp, sum(gset.values()) - tp
    soft_tp, used_p = 0, set()
    for g in gv:
        for j, p in enumerate(pv):
            if j in used_p:
                continue
            if g == p or (len(g) >= 4 and (g in p or p in g)):
                soft_tp += 1
                used_p.add(j)
                break
    soft_fp, soft_fn = len(pv) - soft_tp, len(gv) - soft_tp

    def pack(tp_, fp_, fn_):
        p = tp_ / (tp_ + fp_) if (tp_ + fp_) else 0.0
        r = tp_ / (tp_ + fn_) if (tp_ + fn_) else 0.0
        f = 2 * p * r / (p + r) if (p + r) else 0.0
        return {
            "tp": tp_,
            "fp": fp_,
            "fn": fn_,
            "precision": round(p, 4),
            "recall": round(r, 4),
            "f1": round(f, 4),
        }

    return {"value_exact": pack(tp, fp, fn), "value_soft": pack(soft_tp, soft_fp, soft_fn)}


def load_rows(path: Path, limit: int):
    rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    return rows[:limit]


def normalize_gold(row):
    text = row["text"]
    gold = []
    for e in row["entities"]:
        if "identifier_type" in e:
            gold.append({"label": e["identifier_type"], "value": e.get("value", "")})
        else:
            val = text[e["start"] : e["end"]] if "start" in e else e.get("value", "")
            gold.append({"label": e.get("label", ""), "value": val})
    return gold


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--backend", choices=["heuristic", "gpt"], default="heuristic")
    args = ap.parse_args()
    labels = [
        "NAME", "GIVENNAME", "SURNAME", "DATE", "EMAIL", "EMAIL_ADDRESS",
        "PHONE_NUMBER", "TELEPHONENUM", "GEOGRAPHIC_LOCATION",
        "SOCIAL_SECURITY_NUMBER", "MEDICAL_RECORD_NUMBER",
    ]

    def _resolve(name: str) -> Path:
        base = ROOT / "benchmarking/pii" / name
        for cand in ("smoke_50.jsonl", "smoke_sample.jsonl"):
            path = base / cand
            if path.exists():
                return path
        return base / "smoke_50.jsonl"

    datasets = {
        "piimb": _resolve("piimb"),
        "asq_phi": _resolve("asq_phi"),
    }
    out = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "backend": args.backend,
        "limit": args.limit,
        "results": {},
    }
    for name, path in datasets.items():
        if not path.exists():
            out["results"][name] = {"error": f"missing {path}"}
            continue
        rows = load_rows(path, args.limit)
        agg = {"value_exact": {"tp": 0, "fp": 0, "fn": 0}, "value_soft": {"tp": 0, "fp": 0, "fn": 0}}
        for row in rows:
            gold = normalize_gold(row)
            if args.backend == "gpt":
                pred = extract_gpt(row["text"], labels) or extract_heuristic(row["text"])
            else:
                pred = extract_heuristic(row["text"])
            sc = score(gold, pred)
            for k in agg:
                for m in ("tp", "fp", "fn"):
                    agg[k][m] += sc[k][m]

        def fin(a):
            p = a["tp"] / (a["tp"] + a["fp"]) if (a["tp"] + a["fp"]) else 0
            r = a["tp"] / (a["tp"] + a["fn"]) if (a["tp"] + a["fn"]) else 0
            f = 2 * p * r / (p + r) if (p + r) else 0
            return {
                "tp": a["tp"], "fp": a["fp"], "fn": a["fn"],
                "precision": round(p, 4), "recall": round(r, 4), "f1": round(f, 4),
            }

        out["results"][name] = {"n": len(rows), "metrics": {k: fin(v) for k, v in agg.items()}}
    dest = ROOT / "benchmarking/pii/results/smoke_pii_f1.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
