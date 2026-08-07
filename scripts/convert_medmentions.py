#!/usr/bin/env python3
"""Convert MedMentions PubTator.gz to JSONL documents for agentic-ontogpt."""
from __future__ import annotations
import argparse, gzip, json
from pathlib import Path
from typing import Dict, List

def parse_pubtator(path: Path) -> List[dict]:
    open_fn = gzip.open if str(path).endswith(".gz") else open
    docs: Dict[str, dict] = {}
    order: List[str] = []
    with open_fn(path, "rt", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            if "|t|" in line[:20]:
                pmid, _, title = line.split("|", 2)
                if pmid not in docs:
                    docs[pmid] = {"pmid": pmid, "title": title, "abstract": "", "mentions": []}
                    order.append(pmid)
                else:
                    docs[pmid]["title"] = title
            elif "|a|" in line[:20]:
                pmid, _, abstract = line.split("|", 2)
                if pmid not in docs:
                    docs[pmid] = {"pmid": pmid, "title": "", "abstract": abstract, "mentions": []}
                    order.append(pmid)
                else:
                    docs[pmid]["abstract"] = abstract
            else:
                parts = line.split("\t")
                if len(parts) < 6:
                    continue
                pmid, start, end, text, stype, cui = parts[0], parts[1], parts[2], parts[3], parts[4], parts[5]
                if pmid not in docs:
                    docs[pmid] = {"pmid": pmid, "title": "", "abstract": "", "mentions": []}
                    order.append(pmid)
                docs[pmid]["mentions"].append({
                    "start": int(start),
                    "end": int(end),
                    "text": text,
                    "semantic_type": stype,
                    "cui": cui.replace("UMLS:", "") if cui.startswith("UMLS:") else cui,
                })
    out = []
    for pmid in order:
        d = docs[pmid]
        d["text"] = ((d.get("title") or "") + " " + (d.get("abstract") or "")).strip()
        out.append(d)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/medmentions")
    ap.add_argument("--out", default="data/medmentions/docs.jsonl")
    ap.add_argument("--pmids", default=None)
    args = ap.parse_args()
    data = Path(args.data)
    corpus = data / "corpus_pubtator.txt.gz"
    if not corpus.exists():
        corpus = data / "corpus_pubtator.txt"
    docs = parse_pubtator(corpus)
    if args.pmids:
        allow = set(Path(args.pmids).read_text().split())
        docs = [d for d in docs if d["pmid"] in allow]
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as f:
        for d in docs:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    print(f"Wrote {len(docs)} docs -> {out}")

if __name__ == "__main__":
    main()
