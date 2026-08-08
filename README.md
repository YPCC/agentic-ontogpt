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
5. Optionally ground mentions to ontology concept ids/CURIEs; export RDF; record provenance  

Simulation is **opt-in** (`AGENTIC_ONTOGPT_MODE=simulation`). Core SPIRES runtime never converts real failures into success; benchmark scripts report `REAL_EXTRACTION_FAILED` on errors.

---

## Parallel execution paths (same conceptual stages)

```text
Ontology selection → policy → bounded repair (gen ↔ val)×N → gated SPIRES extract
```

**Enforcement differs by path** (Path C strongest deterministic gate; Path A re-validates schema in the extract tool; Path B is experimental).

```text
   Path A — Canonical ADK prototype    Path B — Experimental graph     Path C — Headless
   Sequential + Loop                   registry + graph_*              pipeline_runner /
   agents/pipeline/agent.py            (additive showcase)             modular_compose
```

| Path | Style | Entry | When to use |
|------|--------|-------|-------------|
| **A** | ADK 1.x-style `SequentialAgent` + `LoopAgent` | `adk run agents/pipeline` | **Canonical ADK prototype** |
| **B** | **Experimental** graph / registry showcase | `python demos/run_adk_graph_demo.py` · `run_adk_repair_graph_demo.py` | Factory composition — **not** equivalent to A/C |
| **C** | Pure Python | `tools.pipeline_runner` · `run_modular_agents_demo.py --compare` | CI / tests / no ADK |

Path B does **not** modify `agents/pipeline/agent.py`.

Optional Path C downstream: `run_pipeline(..., enable_grounding=True, enable_rdf=True)`.

Grounding targets **ontology concept identifiers / CURIEs** (UMLS CUIs when available).

Observability is **lightweight** stage timing and estimated tokens/cost — not full provider telemetry.

### Quick commands

```bash
python -m pytest tests/ -q

export AGENTIC_ONTOGPT_MODE=simulation
python demos/run_modular_agents_demo.py --compare --made-template

pip install google-adk
adk run agents/pipeline

python demos/run_adk_graph_demo.py
python demos/run_adk_repair_graph_demo.py --max-iterations 3
```

---

## Quick start

```bash
git clone https://github.com/YPCC/agentic-ontogpt.git
cd agentic-ontogpt
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
# Enterprise ADC: cp .env.adc.example .env  &&  see docs/AUTH_ADC.md
python -m pytest tests/ -q
```

| Variable | Purpose |
|----------|---------|
| `GOOGLE_API_KEY` | Developer AI Studio mode |
| `BIOPORTAL_API_KEY` | Ontology recommend/search/annotator |
| `OPENAI_API_KEY` | Optional SPIRES / GPT PII |
| `AGENTIC_ONTOGPT_MODE` | `real` or `simulation` |
| `APPROVAL_MODE` | `auto` / `require` / `reject` |

**Enterprise ADC:** [`docs/AUTH_ADC.md`](docs/AUTH_ADC.md) · [`.env.adc.example`](.env.adc.example)

---

## Headless (Path C)

```python
from tools.pipeline_runner import run_pipeline
state = run_pipeline(
    "Patient developed severe neutropenia after carboplatin.",
    ["Medication", "AdverseEvent"],
    ontology_preferences={"Medication": "RXNORM", "AdverseEvent": "MEDDRA"},
    enable_rdf=True,  # optional
)
print(state.selected_ontologies, state.extraction_result["outcome"])
```

---

## Capability layers

| Layer | Features |
|-------|----------|
| **P0** | Explicit outcomes, validation ladder, bounded repair, extract gate |
| **P1** | Ontology policy, PipelineState, provenance |
| **P2** | Grounding ≠ selection (tools/benchmarks); RDF export with prefix+parse discipline; ablations |
| **P3** | Approval (headless), estimated cost/latency instrumentation, ValidationExitAgent |

---

## Status & limitations

- Prototype / PoC — not clinical decision support  
- Path B is an experimental showcase  
- RDF: declares known prefixes; parse before SHACL; `structural_skip` does not claim conformance  
- Path C optional `enable_grounding` / `enable_rdf`  
- PII smoke uses synthetic data only  

---

## References

- OntoGPT / SPIRES — https://github.com/monarch-initiative/ontogpt  
- LinkML — https://linkml.io/  
- BioPortal — https://data.bioontology.org/documentation  
- Google ADK — https://google.github.io/adk-docs/  
- Enterprise ADC — [`docs/AUTH_ADC.md`](docs/AUTH_ADC.md)  
