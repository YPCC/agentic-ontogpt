#!/usr/bin/env python3
"""Run ablation suite A–D and print a comparison table."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.ablation import run_ablation_suite
from tools.repair import fixture_regenerate
HAND = (ROOT / "templates" / "clinical_modifiers.yaml").read_text()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", default="The patient denies rash, but her mother previously developed a rash after penicillin.")
    ap.add_argument("--entities", default="ClinicalStatement,Medication,AdverseEvent")
    ap.add_argument("--mode", default="simulation", choices=["real", "simulation"])
    ap.add_argument("--out", default=str(ROOT / "benchmarking" / "ablation" / "results.json"))
    args = ap.parse_args()
    entities = [e.strip() for e in args.entities.split(",") if e.strip()]
    suite = run_ablation_suite(args.text, entities, hand_authored_schema=HAND,
        oneshot_seed="name: broken\nimports: []\n",
        ontology_preferences={"Medication": "RXNORM", "AdverseEvent": "MEDDRA"},
        regenerate_fn=fixture_regenerate, execution_mode=args.mode)
    print(f"{'Cfg':3} {'Label':40} {'Valid':6} {'1st':5} {'Rep':4} {'Outcome':28} {'Blocked'}")
    print("-" * 100)
    for row in suite["rows"]:
        print(f"{row['config']:3} {row['label'][:40]:40} {str(row['schema_valid']):6} "
              f"{str(row['first_pass_valid']):5} {str(row['repair_iterations']):4} "
              f"{str(row['extraction_outcome'])[:28]:28} {row['extraction_blocked']}")
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    slim = {"rows": suite["rows"], "configs": {}}
    for k, v in suite["results"].items():
        slim["configs"][k] = {"label": v["label"], "metrics": v["metrics"],
            "extraction_outcome": (v["state"].get("extraction_result") or {}).get("outcome"),
            "schema_valid": (v["state"].get("validation_report") or {}).get("valid")}
    out.write_text(json.dumps(slim, indent=2))
    print(f"\nWrote {out}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
