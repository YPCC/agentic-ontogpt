"""Grounding benchmark against gold CUIs (MedMentions-style)."""
from __future__ import annotations
import json, re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from .grounding import ground_mention_bioportal, ground_mentions_dictionary
from .metrics import Timer

def _norm_cui(c):
    c = (c or "").strip().upper().replace("UMLS:", "")
    if c.startswith("C") and c[1:].isdigit(): return c
    if ":" in c:
        tail = c.split(":")[-1]
        if tail.startswith("C") and tail[1:].isdigit(): return tail
    return c

def _norm_text(t):
    return re.sub(r"\s+", " ", (t or "").strip().lower())

def load_docs_jsonl(path, limit=None):
    docs = []
    with Path(path).open() as f:
        for i, line in enumerate(f):
            if limit is not None and i >= limit: break
            docs.append(json.loads(line))
    return docs

def build_train_lexicon(train_docs):
    counts = defaultdict(lambda: defaultdict(int))
    for d in train_docs:
        for m in d.get("mentions") or []:
            t, c = _norm_text(m.get("text") or ""), _norm_cui(m.get("cui") or "")
            if t and c: counts[t][c] += 1
    return {t: max(ctr.items(), key=lambda x: x[1])[0] for t, ctr in counts.items()}

def gold_pairs(doc):
    return {(_norm_text(m.get("text") or ""), _norm_cui(m.get("cui") or ""))
            for m in doc.get("mentions") or [] if m.get("text") and m.get("cui")}

def pred_pairs_lexicon(doc, lexicon):
    grounded = ground_mentions_dictionary([{"text": m.get("text")} for m in doc.get("mentions") or []], lexicon)
    return {(_norm_text(g.text), _norm_cui(g.cui)) for g in grounded if g.status == "grounded" and g.cui}

def pred_pairs_bioportal(doc, ontology="MSH"):
    out = set()
    for m in doc.get("mentions") or []:
        text = m.get("text") or ""
        if not text: continue
        for h in ground_mention_bioportal(text, ontology):
            if h.cui:
                out.add((_norm_text(text), _norm_cui(h.cui))); break
    return out

def score_sets(gold, pred):
    tp, fp, fn = len(gold & pred), len(pred - gold), len(gold - pred)
    p = tp/(tp+fp) if tp+fp else 0.0
    r = tp/(tp+fn) if tp+fn else 0.0
    f1 = 2*p*r/(p+r) if p+r else 0.0
    return {"precision": p, "recall": r, "f1": f1, "tp": tp, "fp": fp, "fn": fn}

def run_grounding_benchmark(test_docs, *, train_docs=None, mode="lexicon", bioportal_ontology="MSH", limit=None):
    if limit: test_docs = test_docs[:limit]
    timer = Timer()
    lexicon = build_train_lexicon(train_docs or []) if train_docs is not None else {}
    timer.mark("lexicon_build")
    modes = ["lexicon", "bioportal"] if mode == "both" else [mode]
    results = {"n_docs": len(test_docs), "modes": {},
               "protocol": "Linking given gold spans; exact CUI match after normalization."}
    for m in modes:
        tp = fp = fn = 0
        for doc in test_docs:
            g = gold_pairs(doc)
            p = pred_pairs_lexicon(doc, lexicon) if m == "lexicon" else pred_pairs_bioportal(doc, bioportal_ontology)
            tp += len(g & p); fp += len(p - g); fn += len(g - p)
        ip = tp/(tp+fp) if tp+fp else 0.0
        ir = tp/(tp+fn) if tp+fn else 0.0
        if1 = 2*ip*ir/(ip+ir) if ip+ir else 0.0
        results["modes"][m] = {"instance_micro": {"precision": ip, "recall": ir, "f1": if1, "tp": tp, "fp": fp, "fn": fn},
                               "lexicon_size": len(lexicon) if m == "lexicon" else None,
                               "bioportal_ontology": bioportal_ontology if m == "bioportal" else None}
        timer.mark(m)
    results["timing"] = timer.as_dict()
    return results
