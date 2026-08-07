# agentic-ontogpt

**Agentic control layer around OntoGPT / SPIRES** — ontology selection, LinkML template generation & validation, bounded repair, and gated extraction — with explicit outcomes, policy, and provenance.

Repository: https://github.com/YPCC/agentic-ontogpt

---

## Thesis

[OntoGPT](https://github.com/monarch-initiative/ontogpt) + **SPIRES** already perform schema-guided extraction. **agentic-ontogpt does not replace SPIRES.** It automates and governs the work *around* it:

1. Choose (and policy-filter) ontologies per entity type  
2. Generate OntoGPT-compliant LinkML templates  
3. Validate with a multi-stage ladder and repair on error  
4. Extract only when the schema is valid  
5. Record provenance for every run  

Simulation is **opt-in** (`AGENTIC_ONTOGPT_MODE=simulation`). Real failures are never silently converted into simulated success.

---

## Architecture

```
Clinical / PubMed text + entity types (± preferred ontologies)
        │
        ▼
 OntologySelector  → BioPortal recommend/search
        │
        ▼
 Ontology policy   → allow/deny + preferred-by-type
        │
        ▼
 TemplateRepairLoop (≤ 3) → gated SPIRES extraction
        │
        ▼
 Grounding (span→CUI) → RDF Turtle (+ SHACL) + provenance + component metrics
```

---

## Quick start

```bash
git clone https://github.com/YPCC/agentic-ontogpt.git
cd agentic-ontogpt
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"   # or: pip install pyyaml requests linkml pytest
cp .env.example .env
python -m pytest tests/ -q
```

### Configuration

| Variable | Purpose |
|----------|---------|
| `GOOGLE_API_KEY` | ADK / Gemini agents |
| `BIOPORTAL_API_KEY` | Recommend, search, annotator grounding |
| `OPENAI_API_KEY` | Optional real OntoGPT SPIRES |
| `AGENTIC_ONTOGPT_MODE` | `real` (default) or `simulation` |
| `ADK_LLM_MODEL` / `SPIRES_LLM_MODEL` | Model overrides |

---

## How to run

**Tests:** `python -m pytest tests/ -q`

**Headless pipeline:**
```python
from tools.pipeline_runner import run_pipeline
state = run_pipeline(
    "Patient developed severe neutropenia after carboplatin.",
    ["Medication", "AdverseEvent"],
    ontology_preferences={"Medication": "RXNORM", "AdverseEvent": "MEDDRA"},
)
print(state.selected_ontologies, state.extraction_result["outcome"])
```

**Failure modes:** `jupyter notebook demos/failure_modes_repair_loop.ipynb`

**ADK:** `adk run agents/pipeline`

**MADE:** `python scripts/run_made_eval.py`

**MedMentions:** see scripts `download_medmentions.py` → `convert_medmentions.py` → `run_medmentions_benchmark.py`

**Ablations A–D:** `python scripts/run_ablation.py --mode simulation`

---

## P0 — Outcomes & validation

| Outcome | When |
|---------|------|
| `REAL_SUCCESS` | OntoGPT succeeded |
| `SIMULATION_REQUESTED` | `MODE=simulation` only |
| `REAL_EXTRACTION_FAILED` | Real error or invalid schema gate |

Validation ladder: YAML → keys → LinkML → OntoGPT conventions (hard fail) → optional template load.

---

## P1 — Policy, state, provenance

- `configs/ontology_policy.yaml` — allow/deny + preferred-by-type
- `PipelineState` — shared run state
- Provenance manifest — models, hashes, validation, outcomes

---

## P2 — Grounding, metrics, ablations, clinical context, RDF

### Selection vs grounding

| Step | Question | Module |
|------|----------|--------|
| Selection | Which ontology fits this *type*? | policy / BioPortal recommender |
| Grounding | Which *concept* is this span? | `tools.grounding` |

```python
from tools.grounding import ground_extraction_object
report = ground_extraction_object(extracted, {"medications": "RXNORM"},
                                  lexicon={"carboplatin": "RXNORM:40048"})
```

### Component metrics

`tools.metrics.build_component_metrics` — selection coverage, template validity & repair iterations, extraction outcome, grounding rate, timings.

### Ablations

| Config | Meaning |
|--------|---------|
| A | Hand-authored template |
| B | One-shot generate (no validate gate) |
| C | Generate + validate once |
| D | Policy + repair loop + gated extract |

Results: `benchmarking/ablation/results.json`

### Clinical modifiers

`templates/clinical_modifiers.yaml` — assertion, temporality, experiencer, certainty.

### RDF + SHACL

```python
from tools.rdf_export import export_and_validate
out = export_and_validate(extraction_result, grounding_report=report)
# out["turtle"], out["shacl"] (pyshacl or structural fallback)
```

---

## Benchmarking

| Track | Path |
|-------|------|
| MADE 1.0 | `benchmarking/made/` |
| MedMentions ST21pv | `benchmarking/medmentions/` |
| Ablations | `benchmarking/ablation/` |

---

## Status & limitations

- Prototype / PoC — not clinical decision support
- Validate extractions before clinical use; protect PHI on external APIs
- Ontology selection ≠ mention grounding
- Full pyshacl optional; structural SHACL fallback always available

---

## References

- OntoGPT / SPIRES — https://github.com/monarch-initiative/ontogpt
- LinkML — https://linkml.io/
- BioPortal — https://data.bioontology.org/documentation
- MedMentions — https://github.com/chanzuckerberg/MedMentions
- MADE 1.0 — https://pmc.ncbi.nlm.nih.gov/articles/PMC6860017/
- Google ADK — https://google.github.io/adk-docs/
