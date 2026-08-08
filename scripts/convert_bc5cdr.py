#!/usr/bin/env python3
"""Convert BC5CDR PubTator files to JSONL for Track 2."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_pubtator(path: Path) -> list[dict]:
    docs: dict[str, dict] = {}
    order: list[str] = []
    with path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            if "|t|" in line[:20]:
                pmid, _, title = line.split("|", 2)
                if pmid not in docs:
                    docs[pmid] = {"id": pmid, "pmid": pmid, "title": title, "abstract": "", "entities": []}
                    order.append(pmid)
                else:
                    docs[pmid]["title"] = title
            elif "|a|" in line[:20]:
                pmid, _, abstract = line.split("|", 2)
                if pmid not in docs:
                    docs[pmid] = {"id": pmid, "pmid": pmid, "title": "", "abstract": abstract, "entities": []}
                    order.append(pmid)
                else:
                    docs[pmid]["abstract"] = abstract
            else:
                parts = line.split("\t")
                if len(parts) < 5 or parts[1] == "CID":
                    continue
                pmid, start, end, text, etype = parts[0], parts[1], parts[2], parts[3], parts[4]
                if etype not in ("Chemical", "Disease"):
                    continue
                if pmid not in docs:
                    docs[pmid] = {"id": pmid, "pmid": pmid, "title": "", "abstract": "", "entities": []}
                    order.append(pmid)
                docs[pmid]["entities"].append(
                    {"start": int(start), "end": int(end), "text": text, "type": etype,
                     "id": parts[5] if len(parts) > 5 else None}
                )
    out = []
    for pmid in order:
        d = docs[pmid]
        d["text"] = f"{d.get('title') or ''} {d.get('abstract') or ''}".strip()
        out.append(d)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/bc5cdr")
    ap.add_argument("--split", default="test", choices=["train", "dev", "test", "all"])
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    data = Path(args.data)
    names = {
        "train": "CDR_TrainingSet.PubTator.txt",
        "dev": "CDR_DevelopmentSet.PubTator.txt",
        "test": "CDR_TestSet.PubTator.txt",
    }
    files = list(names.values()) if args.split == "all" else [names[args.split]]
    out_path = Path(args.out or data / ("docs_all.jsonl" if args.split == "all" else f"docs_{args.split}.jsonl"))
    docs: list[dict] = []
    for name in files:
        path = data / "CDR_Data" / "CDR.Corpus.v010516" / name
        if not path.exists():
            alt = list(data.rglob(name))
            if not alt:
                raise SystemExit(f"Missing {name}; run download_bc5cdr.py")
            path = alt[0]
        docs.extend(parse_pubtator(path))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        for d in docs:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    print(f"Wrote {len(docs)} docs -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
