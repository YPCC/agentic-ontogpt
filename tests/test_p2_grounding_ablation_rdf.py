"""P2 tests: grounding, metrics, ablation, RDF/SHACL, clinical template."""
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.grounding import ground_mentions_dictionary, ground_extraction_object
from tools.metrics import score_ontology_selection
from tools.ablation import run_ablation_suite, ABLATION_LABELS
from tools.rdf_export import extraction_to_turtle, validate_turtle_shacl, export_and_validate
from tools.linkml_tools import validate_linkml_schema
from tools.repair import fixture_regenerate

def test_grounding_dictionary():
    out = ground_mentions_dictionary([{"text": "carboplatin"}, {"text": "unknown"}],
                                     {"carboplatin": "RXNORM:40048"}, ontology="RXNORM")
    assert out[0].status == "grounded" and out[1].status == "ungrounded"

def test_ground_extraction_object_separates_selection():
    report = ground_extraction_object(
        {"medications": [{"label": "carboplatin"}], "events": ["neutropenia"]},
        {"medications": "RXNORM", "events": "MEDDRA"},
        lexicon={"carboplatin": "RXNORM:40048", "neutropenia": "MEDDRA:10029354"})
    assert report["n_grounded"] >= 1

def test_ontology_selection_metric():
    s = score_ontology_selection({"Disease": "MONDO", "Drug": "CHEBI"},
                                 gold={"Disease": "MONDO", "Drug": "DRON"})
    assert 0.0 <= s["top1_accuracy"] <= 1.0

def test_clinical_modifiers_template_valid():
    r = validate_linkml_schema((ROOT / "templates" / "clinical_modifiers.yaml").read_text())
    assert r["valid"] is True

def test_ablation_suite_a_through_d(monkeypatch):
    monkeypatch.setenv("AGENTIC_ONTOGPT_MODE", "simulation")
    hand = (ROOT / "templates" / "clinical_modifiers.yaml").read_text()
    suite = run_ablation_suite("Patient denies rash after penicillin.", ["ClinicalStatement"],
        hand_authored_schema=hand, oneshot_seed="name: broken\n",
        regenerate_fn=fixture_regenerate, execution_mode="simulation")
    by = {r["config"]: r for r in suite["rows"]}
    assert by["A"]["schema_valid"] is True
    assert by["D"]["schema_valid"] is True

def test_rdf_export_and_shacl():
    extraction = {"extracted_object": {"medications": [{"label": "carboplatin", "id": "RXNORM:40048"}]},
                  "named_entities": [{"id": "RXNORM:40048", "label": "carboplatin"}]}
    ttl = extraction_to_turtle(extraction["extracted_object"], named_entities=extraction["named_entities"])
    assert "ao:Mention" in ttl and "carboplatin" in ttl
    assert "conforms" in validate_turtle_shacl(ttl)
    assert export_and_validate(extraction)["n_chars"] > 0

def test_ablation_labels_complete():
    assert set(ABLATION_LABELS) == {"A", "B", "C", "D"}
