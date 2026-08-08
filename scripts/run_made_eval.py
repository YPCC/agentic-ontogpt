#!/usr/bin/env python3
"""Run MADE 1.0 SPIRES extraction + offline evaluation on a synthetic note.

Produces metrics comparable in *format* to the official MADE micro-F1 tables.
Full official benchmark requires the request-based MADE release + organizers' BioC eval script.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import yaml

REPO = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = REPO / "templates" / "made_1_0.yaml"

SAMPLE_NOTE = """
ALLERGIES: Bleomycin.

Patient denies any fevers, chills or weight loss.

PAST MEDICAL HISTORY: Hodgkin lymphoma as noted above.

MEDICATIONS: Zofran 8 mg p.o. every 8 hours as needed for nausea.
Patient also takes atenolol 50 mg daily for hypertension.

Hospital course: After paclitaxel infusion the patient developed severe diarrhea
and mild fever which were attributed to the chemotherapy. Ondansetron was continued.
""".strip()

GOLD = {
    "entities": [
        {"type": "Drug", "text": "Bleomycin"},
        {"type": "SSLIF", "text": "fevers"},
        {"type": "SSLIF", "text": "chills"},
        {"type": "SSLIF", "text": "weight loss"},
        {"type": "SSLIF", "text": "Hodgkin lymphoma"},
        {"type": "Drug", "text": "Zofran"},
        {"type": "Dosage", "text": "8 mg"},
        {"type": "Route", "text": "p.o."},
        {"type": "Frequency", "text": "every 8 hours as needed"},
        {"type": "Indication", "text": "nausea"},
        {"type": "Drug", "text": "atenolol"},
        {"type": "Dosage", "text": "50 mg"},
        {"type": "Frequency", "text": "daily"},
        {"type": "Indication", "text": "hypertension"},
        {"type": "Drug", "text": "paclitaxel"},
        {"type": "ADE", "text": "diarrhea"},
        {"type": "Severity", "text": "severe"},
        {"type": "ADE", "text": "fever"},
        {"type": "Severity", "text": "mild"},
        {"type": "Drug", "text": "Ondansetron"},
    ],
    "relations": [
        {"type": "Dosage", "arg1_text": "Zofran", "arg2_text": "8 mg"},
        {"type": "Manner/Route", "arg1_text": "Zofran", "arg2_text": "p.o."},
        {"type": "Frequency", "arg1_text": "Zofran", "arg2_text": "every 8 hours as needed"},
        {"type": "Reason", "arg1_text": "Zofran", "arg2_text": "nausea"},
        {"type": "Dosage", "arg1_text": "atenolol", "arg2_text": "50 mg"},
        {"type": "Frequency", "arg1_text": "atenolol", "arg2_text": "daily"},
        {"type": "Reason", "arg1_text": "atenolol", "arg2_text": "hypertension"},
        {"type": "Adverse", "arg1_text": "paclitaxel", "arg2_text": "diarrhea"},
        {"type": "Adverse", "arg1_text": "paclitaxel", "arg2_text": "fever"},
        {"type": "Severity", "arg1_text": "diarrhea", "arg2_text": "severe"},
        {"type": "Severity", "arg1_text": "fever", "arg2_text": "mild"},
    ],
}

PUBLIC_BASELINES = {
    "NER_best_team": 0.82,
    "RI_best_team": 0.86,
    "E2E_best_team": 0.61,
    "NER_ensemble": 0.85,
    "RI_ensemble": 0.87,
    "E2E_ensemble": 0.66,
}


def run_spires(template_yaml: str, text: str) -> dict[str, Any]:
    """Delegate to shared tools.spires (explicit outcomes; no silent simulation)."""
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    from tools.spires import run_spires_extraction

    result = run_spires_extraction(
        template_yaml,
        text,
        schema_name="made_1_0",
        require_valid_schema=True,
    )
    outcome = result.get("outcome")
    if outcome == "REAL_SUCCESS":
        return {
            "mode": "real_ontogpt",
            "outcome": outcome,
            "extracted_object": result.get("extracted_object") or {},
        }
    if outcome == "SIMULATION_REQUESTED":
        return {
            "mode": "simulation",
            "outcome": outcome,
            "extracted_object": result.get("extracted_object") or {},
            "note": result.get("message"),
        }
    return {
        "mode": "real_failed",
        "outcome": outcome or "REAL_EXTRACTION_FAILED",
        "extracted_object": {},
        "error": result.get("message") or result.get("error_type"),
        "note": "No silent simulation; shared SPIRES contract",
    }


def _label(x: Any) -> str:
    if isinstance(x, dict):
        return str(x.get("label") or x.get("id") or x)
    return str(x)


def spires_to_ann(extracted: dict) -> dict:
    entities = []
    type_map = {
        "drugs": "Drug",
        "dosages": "Dosage",
        "routes": "Route",
        "durations": "Duration",
        "frequencies": "Frequency",
        "indications": "Indication",
        "ades": "ADE",
        "severities": "Severity",
        "sslifs": "SSLIF",
    }
    for slot, etype in type_map.items():
        for item in extracted.get(slot) or []:
            entities.append({"type": etype, "text": _label(item)})

    relations = []
    specs = [
        ("drug_dosage_relations", "Dosage", "drug", "dosage"),
        ("drug_route_relations", "Manner/Route", "drug", "route"),
        ("drug_frequency_relations", "Frequency", "drug", "frequency"),
        ("drug_duration_relations", "Duration", "drug", "duration"),
        ("drug_indication_relations", "Reason", "drug", "indication"),
        ("drug_ade_relations", "Adverse", "drug", "ade"),
        ("severity_relations", "Severity", "target", "severity"),
    ]
    for slot, rtype, a1, a2 in specs:
        for item in extracted.get(slot) or []:
            if not isinstance(item, dict):
                continue
            relations.append(
                {
                    "type": rtype,
                    "arg1_text": _label(item.get(a1)),
                    "arg2_text": _label(item.get(a2)),
                }
            )
    return {"entities": entities, "relations": relations}


def score_sets(gold_keys, pred_keys):
    g, p = set(gold_keys), set(pred_keys)
    tp = len(g & p)
    fp = len(p - g)
    fn = len(g - p)
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": prec, "recall": rec, "f1": f1}


def evaluate(gold: dict, pred: dict) -> dict:
    def ek(e):
        return (e["type"], e["text"].strip().lower())

    def rk(r):
        return (
            r["type"],
            r.get("arg1_text", "").strip().lower(),
            r.get("arg2_text", "").strip().lower(),
        )

    ent = score_sets([ek(e) for e in gold["entities"]], [ek(e) for e in pred["entities"]])
    rel = score_sets([rk(r) for r in gold["relations"]], [rk(r) for r in pred["relations"]])
    by_type = {}
    types = sorted(
        {e["type"] for e in gold["entities"]} | {e["type"] for e in pred["entities"]}
    )
    for t in types:
        by_type[t] = score_sets(
            [ek(e) for e in gold["entities"] if e["type"] == t],
            [ek(e) for e in pred["entities"] if e["type"] == t],
        )
    return {"entities_micro": ent, "relations_micro": rel, "entities_by_type": by_type}


def main() -> int:
    if not TEMPLATE_PATH.exists():
        print("ERROR: template not found:", TEMPLATE_PATH, file=sys.stderr)
        return 1
    template_yaml = TEMPLATE_PATH.read_text()
    schema = yaml.safe_load(template_yaml)
    print("=" * 60)
    print("MADE 1.0 — agentic OntoGPT / SPIRES evaluation")
    print("=" * 60)
    print(f"Template: {TEMPLATE_PATH}")
    print(f"Classes:  {len(schema.get('classes', {}))}")
    print()
    print("Note: Official MADE test data is request-based (DUA/permissions).")
    print("      This script is a synthetic pilot only.\n")

    result = run_spires(template_yaml, SAMPLE_NOTE)
    print(f"Extraction mode: {result['mode']}")
    if result.get("outcome"):
        print(f"  outcome: {result['outcome']}")
    if result.get("error") or result.get("note"):
        print(f"  detail: {(result.get('error') or result.get('note') or '')[:160]}")
    pred = spires_to_ann(result.get("extracted_object") or {})
    print(f"Predicted entities:  {len(pred['entities'])}")
    print(f"Predicted relations: {len(pred['relations'])}")
    print(f"Gold entities:       {len(GOLD['entities'])}")
    print(f"Gold relations:      {len(GOLD['relations'])}")
    print()

    metrics = evaluate(GOLD, pred)
    em, rm = metrics["entities_micro"], metrics["relations_micro"]

    print("--- Entity micro (text+type match) ---")
    print(
        f"  P={em['precision']:.4f}  R={em['recall']:.4f}  F1={em['f1']:.4f}  "
        f"(tp={em['tp']} fp={em['fp']} fn={em['fn']})"
    )
    print("--- Relation micro ---")
    print(
        f"  P={rm['precision']:.4f}  R={rm['recall']:.4f}  F1={rm['f1']:.4f}  "
        f"(tp={rm['tp']} fp={rm['fp']} fn={rm['fn']})"
    )

    e2e_approx = min(em["f1"], rm["f1"])
    print()
    print("=" * 60)
    print("COMPARISON vs MADE 1.0 public baselines (reference only)")
    print("=" * 60)
    print(f"{'System':40} {'NER F1':>8} {'RI F1':>8} {'E2E F1':>8}")
    print("-" * 68)
    print(
        f"{'MADE best team (official test)':40} {PUBLIC_BASELINES['NER_best_team']:8.2f} "
        f"{PUBLIC_BASELINES['RI_best_team']:8.2f} {PUBLIC_BASELINES['E2E_best_team']:8.2f}"
    )
    print(
        f"{'agentic-ontogpt SPIRES (this run)*':40} {em['f1']:8.3f} {rm['f1']:8.3f} {e2e_approx:8.3f}"
    )
    print("-" * 68)
    print("* Synthetic single-note pilot (not official MADE test set).")
    print("  Mode:", result["mode"], "outcome:", result.get("outcome"))

    out = {
        "mode": result["mode"],
        "outcome": result.get("outcome"),
        "template": str(TEMPLATE_PATH),
        "predicted": pred,
        "gold": GOLD,
        "metrics": metrics,
        "e2e_approx_f1": e2e_approx,
        "public_baselines": PUBLIC_BASELINES,
        "disclaimer": (
            "Pilot on synthetic note with MADE-faithful schema. "
            "Not comparable to official test-set scores without full MADE release (DUA)."
        ),
    }
    out_path = REPO / "demos" / "made" / "made_eval_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2))
    print(f"Wrote results: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
