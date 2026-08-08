#!/usr/bin/env python3
"""Download BioCreative V CDR (BC5CDR) corpus."""
from __future__ import annotations

import argparse
import urllib.request
import zipfile
from pathlib import Path

URL = "https://github.com/JHnlp/BioCreative-V-CDR-Corpus/raw/master/CDR_Data.zip"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/bc5cdr")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    zpath = out / "CDR_Data.zip"
    print(f"GET {URL}")
    urllib.request.urlretrieve(URL, zpath)
    with zipfile.ZipFile(zpath) as zf:
        zf.extractall(out)
    print(f"Extracted under {out}")
    print("Next: python scripts/convert_bc5cdr.py --data", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
