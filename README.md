# agentic-ontogpt

**Agentic control layer around OntoGPT / SPIRES** — ontology selection, LinkML template generation & validation, bounded repair, gated extraction, grounding, RDF, and observability.

Repository: https://github.com/YPCC/agentic-ontogpt

---

## Thesis

[OntoGPT](https://github.com/monarch-initiative/ontogpt) + **SPIRES** already perform schema-guided extraction. **agentic-ontogpt does not replace SPIRES.** It automates and governs the work *around* it:

1. Choose (and policy-filter) ontologies per entity type  
2. Generate OntoGPT-compliant LinkML templates  
3. Validate with a multi-stage ladder and repair on error  
4. Extract only when the schema is valid  
5. Ground mentions to CUIs; export RDF; record provenance  

Simulation is **opt-in** (`AGENTIC_ONTOGPT_MODE=simulation`). Real failures are never silently converted into simulated success.

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

| Variable | Purpose |
|----------|---------|
| `GOOGLE_API_KEY` | ADK / Gemini agents |
| `BIOPORTAL_API_KEY` | Recommend, search, annotator grounding |
| `OPENAI_API_KEY` | Optional real OntoGPT SPIRES |
| `AGENTIC_ONTOGPT_MODE` | `real` (default) or `simulation` |
| `APPROVAL_MODE` | `auto` / `require` / `reject` |

---

## How to run

```bash
python -m pytest tests/ -q
python scripts/run_ablation.py --mode simulation
python scripts/run_grounding_benchmark.py --limit 50 --mode lexicon
# Live Annotator:
# python scripts/run_grounding_benchmark.py --limit 20 --mode bioportal --ontology MSH
```

Headless pipeline:
```python
from tools.pipeline_runner import run_pipeline
state = run_pipeline(
    "Patient developed severe neutropenia after carboplatin.",
    ["Medication", "AdverseEvent"],
    ontology_preferences={"Medication": "RXNORM", "AdverseEvent": "MEDDRA"},
)
print(state.selected_ontologies, state.extraction_result["outcome"])
print(state.component_metrics.get("observability"))
```

ADK: `adk run agents/pipeline`  
Failure modes: `demos/failure_modes_repair_loop.ipynb`

---

## Capability layers

| Layer | Features |
|-------|----------|
| **P0** | Explicit outcomes, validation ladder, error-directed repair, extract gate |
| **P1** | Ontology policy, PipelineState, provenance manifest |
| **P2** | Grounding ≠ selection, metrics, ablations A–D, clinical modifiers, RDF+SHACL |
| **P3** | Gold-CUI grounding benchmark, ADK ValidationExitAgent, human approval, cost/latency dashboard |

### P3 highlights

**Grounding benchmark** (`benchmarking/grounding/`): linking given gold spans on MedMentions test; lexicon F1 ≈ 0.57 on 50 docs.

**ADK early exit:** `agents/pipeline/exit_agent.py` — escalate when `validation_result.valid`.

**Approval:** `APPROVAL_MODE=require` + decision files under `APPROVAL_DIR`.

**Observability:** `tools.observability.ObservabilitySession` + HTML dashboard.

---

## Benchmarking paths

| Track | Path |
|-------|------|
| MADE 1.0 | `benchmarking/made/` |
| MedMentions ST21pv | `benchmarking/medmentions/` |
| Ablations | `benchmarking/ablation/` |
| Grounding | `benchmarking/grounding/` |

---

## Status & limitations

- Prototype / PoC — not clinical decision support  
- Validate extractions before clinical use; protect PHI on external APIs  
- Ontology selection ≠ mention grounding  
- BioPortal live grounding needs `BIOPORTAL_API_KEY`  

---

## References

- OntoGPT / SPIRES — https://github.com/monarch-initiative/ontogpt  
- LinkML — https://linkml.io/  
- BioPortal — https://data.bioontology.org/documentation  
- MedMentions — https://github.com/chanzuckerberg/MedMentions  
- MADE 1.0 — https://pmc.ncbi.nlm.nih.gov/articles/PMC6860017/  
- Google ADK — https://google.github.io/adk-docs/  
