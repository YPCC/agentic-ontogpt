#!/usr/bin/env python3
"""Track 2 BC5CDR (Chemical + Disease)."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from tools.track2_eval import load_jsonl, run_track2


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", default=str(REPO / "data/bc5cdr/docs_test.jsonl"))
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--oracle", action="store_true")
    ap.add_argument("--out", default=str(REPO / "benchmarking/bc5cdr/results_track2"))
    ap.add_argument("--mode", default=None)
    args = ap.parse_args()
    if args.mode:
        os.environ["AGENTIC_ONTOGPT_MODE"] = args.mode
    docs_path = Path(args.docs)
    if not docs_path.exists():
        print("ERROR: run download_bc5cdr.py && convert_bc5cdr.py first", file=sys.stderr)
        return 1
    tpl = REPO / "templates" / "bc5cdr.yaml"
    run_track2(
        benchmark="BC5CDR",
        docs=load_jsonl(docs_path, limit=args.limit),
        template_yaml=tpl.read_text(),
        schema_name="bc5cdr",
        out_dir=Path(args.out),
        oracle=args.oracle,
        slot_type_map={"chemicals": "Chemical", "diseases": "Disease"},
        template_path=tpl,
        script_path=Path(__file__),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
