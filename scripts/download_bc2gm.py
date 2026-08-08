#!/usr/bin/env python3
"""Download BC2GM IOBES splits."""
from __future__ import annotations

import argparse
import urllib.request
from pathlib import Path

BASE = "https://raw.githubusercontent.com/cambridgeltl/MTL-Bioinformatics-2016/master/data/BC2GM-IOBES"
FILES = ["train.tsv", "devel.tsv", "test.tsv"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/bc2gm")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        url = f"{BASE}/{name}"
        dest = out / name
        print(f"GET {url}")
        urllib.request.urlretrieve(url, dest)
        print(f"  -> {dest} ({dest.stat().st_size} bytes)")
    print("Next: python scripts/convert_bc2gm.py --data", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
