#!/usr/bin/env python3
"""MedMentions-style grounding benchmark with gold CUIs."""
from __future__ import annotations
import argparse, json, os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.grounding_benchmark import load_docs_jsonl, run_grounding_benchmark
from tools.observability import ObservabilitySession, write_dashboard

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", default=str(ROOT / "data/medmentions/docs_test.jsonl"))
    ap.add_argument("--train", default=str(ROOT / "data/medmentions/docs.jsonl"))
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--mode", default="lexicon", choices=["lexicon", "bioportal", "both"])
    ap.add_argument("--ontology", default="MSH")
    ap.add_argument("--out", default=str(ROOT / "benchmarking/grounding/results.json"))
    args = ap.parse_args()
    test_path = Path(args.test)
    if not test_path.exists():
        print(f"Missing {test_path}", file=sys.stderr); return 1
    train_docs = []
    train_path = Path(args.train)
    pmids_trng = ROOT / "data/medmentions/corpus_pubtator_pmids_trng.txt"
    if train_path.exists():
        all_docs = load_docs_jsonl(train_path)
        if pmids_trng.exists():
            allow = set(pmids_trng.read_text().split())
            train_docs = [d for d in all_docs if d.get("pmid") in allow]
        else:
            train_docs = all_docs
    test_docs = load_docs_jsonl(test_path, limit=args.limit)
    if args.mode in ("bioportal", "both") and not os.environ.get("BIOPORTAL_API_KEY"):
        print("WARN: BIOPORTAL_API_KEY unset", file=sys.stderr)
    obs = ObservabilitySession(run_id=f"grounding-{args.limit}-{args.mode}")
    results = run_grounding_benchmark(test_docs, train_docs=train_docs, mode=args.mode,
                                      bioportal_ontology=args.ontology, limit=args.limit)
    obs.mark("benchmark", api_calls=results["n_docs"] if args.mode != "lexicon" else 0)
    results["observability"] = obs.summary()
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2))
    print(f"Docs: {results['n_docs']}  mode={args.mode}")
    for m, block in results["modes"].items():
        inst = block["instance_micro"]
        print(f"  {m:10} instance F1={inst['f1']:.4f}  P={inst['precision']:.4f} R={inst['recall']:.4f}")
    print(f"Wrote {out}")
    write_dashboard([obs.summary()], out.parent / "dashboard.html")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
