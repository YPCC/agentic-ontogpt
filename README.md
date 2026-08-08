<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/9192d92a-95ce-453e-9d4a-c4ca3a496510" />

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
| `OPENAI_API_KEY` | Optional real OntoGPT SPIRES / GPT PII smoke |
| `AGENTIC_ONTOGPT_MODE` | `real` (default) or `simulation` |
| `APPROVAL_MODE` | `auto` / `require` / `reject` |

---

## How to run

```bash
python -m pytest tests/ -q
python scripts/run_ablation.py --mode simulation
python scripts/run_grounding_benchmark.py --limit 50 --mode lexicon
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
```

ADK: `adk run agents/pipeline`  
Failure modes: `demos/failure_modes_repair_loop.ipynb`

### Modular agents demo (not the ADK pipeline graph)

```bash
export AGENTIC_ONTOGPT_MODE=simulation
python demos/run_modular_agents_demo.py --compare --made-template
```

Uses `agents.modular_compose` + each package’s `get_tools()`. Checks parity with `tools.pipeline_runner`. **Does not modify** `agents/pipeline/agent.py`.

### PII / PHI smoke (PIIMB + ASQ-PHI)

```bash
python scripts/run_pii_smoke.py --limit 50
```

Guide: [`benchmarking/pii/README.md`](benchmarking/pii/README.md)

---

## Capability layers

| Layer | Features |
|-------|----------|
| **P0** | Explicit outcomes, validation ladder, error-directed repair, extract gate |
| **P1** | Ontology policy, PipelineState, provenance manifest |
| **P2** | Grounding ≠ selection, metrics, ablations A–D, clinical modifiers, RDF+SHACL |
| **P3** | Gold-CUI grounding benchmark, ADK ValidationExitAgent, human approval, cost/latency dashboard |

---

## Agents layout

| Path | Role |
|------|------|
| `agents/pipeline/agent.py` | **Canonical** ADK SequentialAgent (keep stable) |
| `agents/pipeline/exit_agent.py` | Validation early-exit for repair loop |
| `agents/ontology_selector/` | Modular `build_*` + `get_tools()` |
| `agents/template_generator/` | Modular `build_*` + `get_tools()` |
| `agents/validator/` | Modular `build_*` + `get_tools()` |
| `agents/spires_extractor/` | Modular `build_*` + `get_tools()` |
| `agents/modular_compose.py` | Headless composition via modular tools |

See [`agents/README.md`](agents/README.md).

---

## Benchmarking paths

| Track | Path | Smoke |
|-------|------|-------|
| MADE 1.0 | `benchmarking/made/` | `python scripts/run_made_eval.py` |
| MedMentions ST21pv | `benchmarking/medmentions/` | `python scripts/run_medmentions_benchmark.py --limit 50` |
| **PII / PHI** | `benchmarking/pii/` | `python scripts/run_pii_smoke.py --limit 50` |
| Ablations | `benchmarking/ablation/` | `python scripts/run_ablation.py --mode simulation` |
| Grounding | `benchmarking/grounding/` | `python scripts/run_grounding_benchmark.py --limit 50` |

---

## Status & limitations

- Prototype / PoC — not clinical decision support  
- Validate extractions before clinical use; protect PHI on external APIs  
- Ontology selection ≠ mention grounding  
- PII smoke uses **synthetic** data only  

---

## References

- OntoGPT / SPIRES — https://github.com/monarch-initiative/ontogpt  
- LinkML — https://linkml.io/  
- BioPortal — https://data.bioontology.org/documentation  
- MedMentions — https://github.com/chanzuckerberg/MedMentions  
- MADE 1.0 — https://pmc.ncbi.nlm.nih.gov/articles/PMC6860017/  
- PIIMB — https://huggingface.co/datasets/piimb/pii-masking-benchmark  
- ASQ-PHI — https://github.com/JamesWeatherhead/asq-phi  
- Google ADK — https://google.github.io/adk-docs/  
