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
 Ontology policy   → allow/deny + preferred-by-type  (configs/ontology_policy.yaml)
        │
        ▼
┌─ TemplateRepairLoop (≤ 3) ─────────────────────┐
│  TemplateGenerator  (error-directed on failure) │
│           ↕                                     │
│  Validator  (YAML → LinkML → OntoGPT conventions│
│              → optional template load)          │
└─────────────────────────────────────────────────┘
        │  only if valid
        ▼
 SPIRES extraction  → REAL_SUCCESS | SIMULATION_REQUESTED | REAL_EXTRACTION_FAILED
        │
        ▼
 PipelineState + provenance manifest
```

| Layer | Mechanism |
|-------|-----------|
| ADK agents | `agents/pipeline` — `LlmAgent` / `LoopAgent` / `SequentialAgent` |
| Headless runner | `tools.pipeline_runner.run_pipeline` — no Google ADK required |
| State | `tools.pipeline_state.PipelineState` |
| Policy | `tools.ontology_policy` + `configs/ontology_policy.yaml` |
| Outcomes | `tools.modes.ExtractionOutcome` |

---

## Quick start

```bash
git clone https://github.com/YPCC/agentic-ontogpt.git
cd agentic-ontogpt

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -e ".[dev]"
# or minimal: pip install pyyaml requests linkml pytest

cp .env.example .env
# Edit .env — see Configuration below
```

### Configuration (`.env`)

| Variable | Purpose |
|----------|---------|
| `GOOGLE_API_KEY` | ADK / Gemini agents |
| `BIOPORTAL_API_KEY` | Ontology recommend & search |
| `OPENAI_API_KEY` | Optional real OntoGPT SPIRES |
| `AGENTIC_ONTOGPT_MODE` | `real` (default) or `simulation` (fixture only) |
| `ADK_LLM_MODEL` | Default `gemini-2.0-flash` |
| `SPIRES_LLM_MODEL` | Default `gpt-4o` |

---

## How to run

### 1. Unit tests (no API keys)

```bash
python -m pytest tests/ -q
```

### 2. Headless pipeline (no ADK)

```python
from tools.pipeline_runner import run_pipeline

state = run_pipeline(
    "Patient developed severe neutropenia after carboplatin.",
    ["Medication", "AdverseEvent"],
    ontology_preferences={"Medication": "RXNORM", "AdverseEvent": "MEDDRA"},
)

print(state.selected_ontologies)
print(state.validation_report["valid"])
print(state.extraction_result["outcome"])
print(state.provenance_manifest["schema"]["sha256"])
```

Simulation (CI / demos):

```bash
export AGENTIC_ONTOGPT_MODE=simulation
python -c "from tools.pipeline_runner import run_pipeline; \
  s=run_pipeline('text', ['Disease']); print(s.extraction_result['outcome'])"
# → SIMULATION_REQUESTED
```

### 3. Failure-modes notebook (P0)

```bash
jupyter notebook demos/failure_modes_repair_loop.ipynb
```

Covers invalid YAML, broken conventions, exhausted repair, extract gate, simulation vs real failure.

### 4. ADK multi-agent pipeline

Requires `GOOGLE_API_KEY` and `google-adk`:

```bash
pip install google-adk
adk run agents/pipeline
# or: adk web
```

### 5. MADE 1.0 pilot

```bash
python scripts/run_made_eval.py
# Results + provenance: benchmarking/made/results/
```

Template: `templates/made_1_0.yaml`

### 6. MedMentions ST21pv smoke (50 abstracts)

```bash
python scripts/download_medmentions.py
python scripts/convert_medmentions.py
python scripts/convert_medmentions.py \
  --pmids data/medmentions/corpus_pubtator_pmids_test.txt \
  --out data/medmentions/docs_test.jsonl

python scripts/run_medmentions_benchmark.py --limit 50
```

Entity × ontology map: `configs/medmentions_st21pv_entities.yaml`  
Results: `benchmarking/medmentions/results/`

---

## Extraction outcomes (P0)

| Outcome | When |
|---------|------|
| `REAL_SUCCESS` | OntoGPT ran successfully |
| `SIMULATION_REQUESTED` | `AGENTIC_ONTOGPT_MODE=simulation` only |
| `REAL_EXTRACTION_FAILED` | Real mode error **or** invalid schema gate |

Never treat arbitrary exceptions as successful simulation.

---

## Validation ladder (P0)

1. YAML syntax  
2. Required keys (`id`, `name`, `imports`, `classes`)  
3. LinkML metamodel (`linkml validate` when CLI present)  
4. OntoGPT conventions (`linkml:types`, `core`, `NamedEntity`, `tree_root`) — **hard fail**  
5. OntoGPT template load (if `ontogpt` installed)  

---

## Ontology policy (P1)

File: [`configs/ontology_policy.yaml`](configs/ontology_policy.yaml)

- **Allowlist / denylist** of BioPortal acronyms  
- **Preferred ontology by entity type**  
- User preferences applied only if allowed  
- BioPortal scores filtered by min score  

---

## Provenance (P1)

Each headless run builds a manifest with run_id, models, package versions, schema hash, validation, extraction outcome, and a reproducibility note.

```python
from tools.provenance import write_manifest
write_manifest(state.provenance_manifest, "artifacts/manifest.json")
```

---

## Repository layout

```
agentic-ontogpt/
├── agents/pipeline/          # ADK orchestration
├── tools/                    # BioPortal, LinkML, SPIRES, repair, state, policy, provenance
├── configs/                  # ontology_policy.yaml, medmentions entity map
├── templates/                # made_1_0.yaml, medmentions_st21pv.yaml
├── scripts/                  # download/convert/eval runners
├── demos/                    # notebooks (failure modes, MADE, prototype)
├── benchmarking/             # made/, medmentions/ + provenance
├── docs/                     # specs, architecture, Medium draft
├── tests/                    # P0 + P1 unit tests
└── pyproject.toml
```

---

## Benchmarking

| Track | Path | Notes |
|-------|------|-------|
| MADE 1.0 | [`benchmarking/made/`](benchmarking/made/) | Pilot / plumbing; official data is request-based |
| MedMentions ST21pv | [`benchmarking/medmentions/`](benchmarking/medmentions/) | 50-abstract smoke + lexicon baseline |

Published baselines in comparison tables are **context**, not always head-to-head (different metrics/splits).

---

## Status & limitations

- **Prototype / architectural PoC** — not a clinical decision-support system  
- Extracted entities need human/clinical validation before use  
- PHI must not be sent to external LLM/ontology APIs without proper agreements  
- Ontology selection ≠ mention grounding (CUI linking is a separate step)  
- ADK `LoopAgent` is bounded; pure-Python `repair_until_valid` is the reference early-exit controller  
- Production RDF export / SHACL still on the roadmap  

---

## Development

```bash
python -m pytest tests/ -q
# Specs: docs/specs/
# Architecture: docs/architecture.md
# Article draft: docs/articles/agentic_ontogpt_medium.md
```

---

## References

- OntoGPT / SPIRES — https://github.com/monarch-initiative/ontogpt  
- LinkML — https://linkml.io/  
- BioPortal API — https://data.bioontology.org/documentation  
- MedMentions — https://github.com/chanzuckerberg/MedMentions  
- MADE 1.0 — https://pmc.ncbi.nlm.nih.gov/articles/PMC6860017/  
- Google ADK — https://google.github.io/adk-docs/  

---

## License

See repository license file. MedMentions is CC0; MADE is request-based from the challenge organizers.
