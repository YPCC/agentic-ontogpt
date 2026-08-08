#!/usr/bin/env python3
"""Demo: modular agents composition (NOT agents.pipeline SequentialAgent).

Reproduces the same headless flow as ``tools.pipeline_runner.run_pipeline``
using packages under ``agents/{ontology_selector,validator,spires_extractor}/``.

Usage (from repo root)::

    export AGENTIC_ONTOGPT_MODE=simulation
    python demos/run_modular_agents_demo.py

    # Compare modular vs pipeline on MADE-style text
    python demos/run_modular_agents_demo.py --compare

    # Use the checked-in MADE 1.0 template as initial schema
    python demos/run_modular_agents_demo.py --made-template
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("AGENTIC_ONTOGPT_MODE", "simulation")

SAMPLE_TEXT = (
    "Patient developed severe neutropenia after receiving carboplatin. "
    "Dose was 300 mg IV every 3 weeks for 6 cycles. Indication: ovarian cancer."
)
ENTITY_TYPES = ["Medication", "AdverseEvent", "Dosage", "Route", "Frequency", "Indication"]
PREFS = {
    "Medication": "RXNORM",
    "AdverseEvent": "MEDDRA",
    "Dosage": "NCIT",
    "Route": "NCIT",
    "Frequency": "NCIT",
    "Indication": "MONDO",
}


def main() -> int:
    ap = argparse.ArgumentParser(description="Modular agents demo (not pipeline ADK graph)")
    ap.add_argument("--compare", action="store_true", help="Also run tools.pipeline_runner and diff outcomes")
    ap.add_argument("--made-template", action="store_true", help="Seed repair with templates/made_1_0.yaml")
    ap.add_argument("--text", default=SAMPLE_TEXT)
    args = ap.parse_args()

    initial = None
    if args.made_template:
        tpl = ROOT / "templates" / "made_1_0.yaml"
        if tpl.exists():
            initial = tpl.read_text()
            print(f"Using MADE template: {tpl}")
        else:
            print(f"WARN: {tpl} missing; generating from fixtures")

    from agents.modular_compose import run_modular_pipeline

    mod = run_modular_pipeline(
        args.text,
        ENTITY_TYPES,
        ontology_preferences=PREFS,
        initial_schema_yaml=initial,
        execution_mode="simulation",
    )

    print("=== Modular composition ===")
    print("composer:", (mod.component_metrics or {}).get("composer"))
    print("selected_ontologies:", mod.selected_ontologies)
    print("schema_valid:", mod.schema_is_valid())
    print("repair_iterations:", mod.repair_iterations)
    print("extraction_outcome:", (mod.extraction_result or {}).get("outcome"))
    print("modular_validator_agrees:", (mod.component_metrics or {}).get("modular_validator_agrees"))

    if not args.compare:
        return 0

    from tools.pipeline_runner import run_pipeline

    pipe = run_pipeline(
        args.text,
        ENTITY_TYPES,
        ontology_preferences=PREFS,
        initial_schema_yaml=initial,
        execution_mode="simulation",
    )

    print("\n=== Pipeline runner (reference) ===")
    print("selected_ontologies:", pipe.selected_ontologies)
    print("schema_valid:", pipe.schema_is_valid())
    print("extraction_outcome:", (pipe.extraction_result or {}).get("outcome"))

    same_ont = mod.selected_ontologies == pipe.selected_ontologies
    same_valid = mod.schema_is_valid() == pipe.schema_is_valid()
    same_outcome = (mod.extraction_result or {}).get("outcome") == (
        pipe.extraction_result or {}
    ).get("outcome")
    print("\n=== Parity ===")
    print(json.dumps({
        "ontologies_match": same_ont,
        "validity_match": same_valid,
        "outcome_match": same_outcome,
        "all_match": same_ont and same_valid and same_outcome,
    }, indent=2))
    return 0 if (same_ont and same_valid and same_outcome) else 1


if __name__ == "__main__":
    raise SystemExit(main())
