#!/usr/bin/env python3
"""Convert BC2GM IOBES TSV to JSONL."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_iobes(path: Path) -> list[dict]:
    sentences: list[dict] = []
    tokens: list[str] = []
    tags: list[str] = []

    def flush() -> None:
        nonlocal tokens, tags
        if not tokens:
            return
        entities: list[dict] = []
        i = 0
        while i < len(tokens):
            tag = tags[i]
            if tag.startswith("S-"):
                entities.append({"text": tokens[i], "type": "GeneProtein"})
                i += 1
            elif tag.startswith("B-"):
                buf = [tokens[i]]
                i += 1
                while i < len(tokens) and tags[i].startswith(("I-", "E-")):
                    buf.append(tokens[i])
                    end = tags[i].startswith("E-")
                    i += 1
                    if end:
                        break
                entities.append({"text": " ".join(buf), "type": "GeneProtein"})
            else:
                i += 1
        text = " ".join(tokens)
        text = text.replace(" .", ".").replace(" ,", ",").replace(" )", ")").replace("( ", "(")
        sentences.append({"id": f"bc2gm-{len(sentences)}", "text": text, "entities": entities})
        tokens, tags = [], []

    with path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip():
                flush()
                continue
            parts = line.split("\t")
            if len(parts) >= 2:
                tokens.append(parts[0])
                tags.append(parts[1])
        flush()
    return sentences


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/bc2gm")
    ap.add_argument("--split", default="test", choices=["train", "devel", "test", "all"])
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    data = Path(args.data)
    names = {"train": "train.tsv", "devel": "devel.tsv", "test": "test.tsv"}
    files = list(names.values()) if args.split == "all" else [names[args.split]]
    out_path = Path(args.out or data / ("docs_all.jsonl" if args.split == "all" else f"docs_{args.split}.jsonl"))
    docs: list[dict] = []
    for name in files:
        path = data / name
        if not path.exists():
            raise SystemExit(f"Missing {path}; run download_bc2gm.py")
        docs.extend(parse_iobes(path))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        for d in docs:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    print(f"Wrote {len(docs)} sentences -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
