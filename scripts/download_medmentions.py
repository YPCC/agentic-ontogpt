#!/usr/bin/env python3
"""Download MedMentions ST21pv corpus + PMID splits from GitHub."""
from __future__ import annotations
import argparse, urllib.request
from pathlib import Path

BASE = "https://raw.githubusercontent.com/chanzuckerberg/MedMentions/master"
FILES = {
    "st21pv/data/corpus_pubtator.txt.gz": "corpus_pubtator.txt.gz",
    "full/data/corpus_pubtator_pmids_trng.txt": "corpus_pubtator_pmids_trng.txt",
    "full/data/corpus_pubtator_pmids_dev.txt": "corpus_pubtator_pmids_dev.txt",
    "full/data/corpus_pubtator_pmids_test.txt": "corpus_pubtator_pmids_test.txt",
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/medmentions")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for remote, local in FILES.items():
        url = f"{BASE}/{remote}"
        dest = out / local
        print(f"GET {url}")
        urllib.request.urlretrieve(url, dest)
        print(f"  -> {dest} ({dest.stat().st_size} bytes)")
    print("Done. Next: python scripts/convert_medmentions.py --data", out)

if __name__ == "__main__":
    main()
