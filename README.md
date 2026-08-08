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

## Parallel execution paths (same control plane)

The **control-plane topology is the same** everywhere:

```text
Ontology selection → policy → bounded repair (gen ↔ val)×N → gated SPIRES extract
```

We keep **three parallel ways** to run it so the product path stays stable while we showcase ADK 2.0 graphs:

```text
                    ┌──────────────────────────────────────────┐
   same topology    │ Ontology → Repair(gen↔val)×N → Extract  │
                    └──────────────────────────────────────────┘
                         │              │              │
            ┌────────────┘              │              └────────────┐
            ▼                           ▼                           ▼
   Path A — Product            Path B — Graph showcase     Path C — Headless
   ADK Sequential / Loop       ADK 2.0 Workflow + gate     No ADK
   agents/pipeline/agent.py    registry + graph_*          pipeline_runner /
   (canonical — do not break)  (additive only)             modular_compose
```

| Path | Style | Entry | When to use |
|------|--------|-------|-------------|
| **A** | ADK **1.x-style** templated agents (`SequentialAgent` + `LoopAgent`) — *non-graph* | `adk run agents/pipeline` | Production / default |
| **B** | ADK **2.0 graph** (`Workflow` edges, `REFINE`/`DONE` gate, dynamic multi-iter repair) | `python demos/run_adk_graph_demo.py` · `python demos/run_adk_repair_graph_demo.py` | Showcase graph routing **without** changing Path A |
| **C** | Pure Python (factories / tools only) | `tools.pipeline_runner` · `python demos/run_modular_agents_demo.py --compare` | CI, tests, no `google-adk` |

Path B builds nodes from `build_*` factories via [`agents/registry.py`](agents/registry.py). It does **not** modify [`agents/pipeline/agent.py`](agents/pipeline/agent.py).

### Quick commands

```bash
# Always
python -m pytest tests/ -q

# Path C — headless (no ADK)
export AGENTIC_ONTOGPT_MODE=simulation
python demos/run_modular_agents_demo.py --compare --made-template

# Path A — product Sequential/Loop (needs google-adk + Vertex/ADC or GOOGLE_API_KEY)
pip install google-adk
adk run agents/pipeline

# Path B — ADK 2.0 graph showcase (registry; does not load pipeline.agent)
python demos/run_adk_graph_demo.py
python demos/run_adk_repair_graph_demo.py --max-iterations 3
```

| Module / demo | Path | Role |
|---------------|------|------|
| `agents/pipeline/agent.py` | A | Canonical Sequential + Loop repair |
| `agents/registry.py` | B | `build(name)` factory registry |
| `agents/graph_workflow.py` | B | Control-plane `Workflow` (or Sequential-from-factories fallback) |
| `agents/graph_repair.py` | B | Multi-iter repair: dynamic loop **or** gate `REFINE`→gen / `DONE`→extract |
| `agents/modular_compose.py` | C | Headless composition via `get_tools()` |
| `demos/run_adk_graph_demo.py` | B | Assemble & report graph mode |
| `demos/run_adk_repair_graph_demo.py` | B | Gate unit demo + repair graph modes |
| `demos/run_modular_agents_demo.py` | C | Parity vs `pipeline_runner` |

More detail: [`agents/README.md`](agents/README.md) · [`demos/README.md`](demos/README.md)

---

## Quick start

```bash
git clone https://github.com/YPCC/agentic-ontogpt.git
cd agentic-ontogpt
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"   # or: pip install pyyaml requests linkml pytest
cp .env.example .env      # developer API-key mode
# Enterprise Vertex + ADC instead:
#   cp .env.adc.example .env
#   see docs/AUTH_ADC.md
python -m pytest tests/ -q
```

| Variable | Purpose |
|----------|---------|
| `GOOGLE_API_KEY` | ADK / Gemini (developer AI Studio mode) |
| `BIOPORTAL_API_KEY` | Recommend, search, annotator grounding |
| `OPENAI_API_KEY` | Optional real OntoGPT SPIRES / GPT PII smoke |
| `AGENTIC_ONTOGPT_MODE` | `real` (default) or `simulation` |
| `APPROVAL_MODE` | `auto` / `require` / `reject` |

**Enterprise (no API key):** Vertex AI + Google ADC — [`docs/AUTH_ADC.md`](docs/AUTH_ADC.md) · [`.env.adc.example`](.env.adc.example)

| Variable | Purpose |
|----------|---------|
| `GOOGLE_GENAI_USE_VERTEXAI` | `TRUE` — use Vertex backend |
| `GOOGLE_CLOUD_PROJECT` | GCP project id |
| `GOOGLE_CLOUD_LOCATION` | e.g. `us-central1` |
| `ADK_LLM_MODEL` | e.g. `gemini-2.0-flash` |

---

## How to run (benchmarks & headless)

```bash
python -m pytest tests/ -q
python scripts/run_ablation.py --mode simulation
python scripts/run_grounding_benchmark.py --limit 50 --mode lexicon
```

Headless pipeline (Path C):

```python
from tools.pipeline_runner import run_pipeline
state = run_pipeline(
    "Patient developed severe neutropenia after carboplatin.",
    ["Medication", "AdverseEvent"],
    ontology_preferences={"Medication": "RXNORM", "AdverseEvent": "MEDDRA"},
)
print(state.selected_ontologies, state.extraction_result["outcome"])
```

Failure modes notebook: `demos/failure_modes_repair_loop.ipynb`

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
| `agents/pipeline/agent.py` | **Path A** — canonical ADK Sequential/Loop (keep stable) |
| `agents/pipeline/exit_agent.py` | Validation early-exit for repair loop |
| `agents/ontology_selector/` | Modular `build_*` + `get_tools()` |
| `agents/template_generator/` | Modular `build_*` + `get_tools()` |
| `agents/validator/` | Modular `build_*` + `get_tools()` |
| `agents/spires_extractor/` | Modular `build_*` + `get_tools()` |
| `agents/registry.py` | **Path B** — factory registry |
| `agents/graph_workflow.py` | **Path B** — ADK 2.0 Workflow assembly |
| `agents/graph_repair.py` | **Path B** — multi-iter repair graph |
| `agents/modular_compose.py` | **Path C** — headless modular composition |

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
- Path B graph materialization needs `google-adk`; demos degrade gracefully without it  

---

## References

- OntoGPT / SPIRES — https://github.com/monarch-initiative/ontogpt  
- LinkML — https://linkml.io/  
- BioPortal — https://data.bioontology.org/documentation  
- MedMentions — https://github.com/chanzuckerberg/MedMentions  
- MADE 1.0 — https://pmc.ncbi.nlm.nih.gov/articles/PMC6860017/  
- PIIMB — https://huggingface.co/datasets/piimb/pii-masking-benchmark  
- ASQ-PHI — https://github.com/JamesWeatherhead/asq-phi  
- Google ADK graphs — https://google.github.io/adk-docs/workflows/  
- Enterprise ADC + Vertex — [`docs/AUTH_ADC.md`](docs/AUTH_ADC.md)  
