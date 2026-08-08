<img width="1536" height="1024" alt="agentic-ontogpt semantic control plane" src="https://github.com/user-attachments/assets/9192d92a-95ce-453e-9d4a-c4ca3a496510" />

# agentic-ontogpt

**A semantic control plane around OntoGPT / SPIRES** — not a replacement for SPIRES, but the governed workflow that selects ontologies, generates and repairs LinkML templates, gates extraction, and records provenance.

Repository: [github.com/YPCC/agentic-ontogpt](https://github.com/YPCC/agentic-ontogpt)

---

## What this is (and what it showcases)

[OntoGPT](https://github.com/monarch-initiative/ontogpt) + **SPIRES** already perform schema-guided extraction from text. **agentic-ontogpt does not replace that engine.** It automates and governs the work *around* it:

1. **Ontology selection** (and policy filters) per entity type  
2. **LinkML template generation** compatible with OntoGPT  
3. **Multi-stage validation** and **bounded repair** on error  
4. **Deterministic extraction gate** — SPIRES only runs on a valid schema  
5. Optional **grounding** (concept IDs / CURIEs), **RDF** export, and **provenance**

**What we showcase**

- Controlled autonomy (agents + tools) under **fail-closed** programmatic gates  
- Three parallel runtimes (**Path A / B / C**) over the **same** control-plane stages  
- Honest execution outcomes: `REAL_SUCCESS` | `SIMULATION_REQUESTED` | `REAL_EXTRACTION_FAILED`  
- Open literature Track-2 benchmarks: **BC5CDR**, **BC2GM**, **MedMentions** (plus MADE pilot schema)

This is a research / architecture **proof of concept**, not clinical decision support.

---

## Quick start

```bash
git clone https://github.com/YPCC/agentic-ontogpt.git
cd agentic-ontogpt
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
python -m pytest tests/ -q
```

| Variable | Purpose |
|----------|---------|
| `GOOGLE_API_KEY` | ADK / Gemini agents (Path A) |
| `BIOPORTAL_API_KEY` | Ontology recommend / search / annotator |
| `OPENAI_API_KEY` | Real OntoGPT SPIRES (default model `gpt-4o`) |
| `AGENTIC_ONTOGPT_MODE` | `real` (default) or `simulation` (opt-in fixture) |
| `APPROVAL_MODE` | Path C: `auto` / `require` / `reject` |

**Enterprise (no Google API key):** Vertex AI + Application Default Credentials — see [`docs/AUTH_ADC.md`](docs/AUTH_ADC.md) and [`.env.adc.example`](.env.adc.example).

### 30-second headless demo (Path C, no ADK)

```bash
export AGENTIC_ONTOGPT_MODE=simulation
python - <<'PY'
from tools.pipeline_runner import run_pipeline
state = run_pipeline(
    "Patient developed severe neutropenia after carboplatin.",
    ["Medication", "AdverseEvent"],
    ontology_preferences={"Medication": "RXNORM", "AdverseEvent": "MEDDRA"},
)
print(state.selected_ontologies)
print(state.extraction_result.get("outcome"))
PY
```

### Track-2 benchmark smokes (no API key)

```bash
AGENTIC_ONTOGPT_MODE=simulation python scripts/run_medmentions_track2.py --limit 20

python scripts/download_bc5cdr.py && python scripts/convert_bc5cdr.py --split test
AGENTIC_ONTOGPT_MODE=simulation python scripts/run_bc5cdr_track2.py --limit 20
python scripts/run_bc5cdr_track2.py --limit 10 --oracle

python scripts/download_bc2gm.py && python scripts/convert_bc2gm.py --split test
AGENTIC_ONTOGPT_MODE=simulation python scripts/run_bc2gm_track2.py --limit 20
```

---

## Parallel execution paths (same control plane)

```text
Ontology selection → policy → bounded repair (gen ↔ val)×N → gated SPIRES extract
         │                                                      │
         └──────── optional grounding / RDF (Path C) ───────────┘
```

```text
                    ┌──────────────────────────────────────────┐
   same topology    │ Ontology → Repair(gen↔val)×N → Extract  │
                    └──────────────────────────────────────────┘
                         │              │              │
            ┌────────────┘              │              └────────────┐
            ▼                           ▼                           ▼
   Path A — Product            Path B — Graph showcase     Path C — Headless
   ADK Sequential / Loop       registry + graph_*          pipeline_runner /
   agents/pipeline/agent.py    (experimental)              modular_compose
   (canonical — do not break)
```

| Path | Style | Entry | When to use |
|------|--------|-------|-------------|
| **A** | ADK Sequential + Loop (`agents/pipeline/`) | `adk run agents/pipeline` | **Canonical** ADK prototype |
| **B** | Experimental graph / `build_*` registry | `python demos/run_adk_graph_demo.py` | Showcase — **not** equivalent to A/C |
| **C** | Pure Python, no ADK | `tools.pipeline_runner.run_pipeline` | CI, tests, strongest deterministic gates |

```bash
pip install google-adk && adk run agents/pipeline
python demos/run_adk_graph_demo.py
python demos/run_adk_repair_graph_demo.py --max-iterations 3
python demos/run_modular_agents_demo.py --compare --made-template
```

More: [`agents/README.md`](agents/README.md) · [`demos/README.md`](demos/README.md) · [`CHANGELOG.md`](CHANGELOG.md)

---

## Architecture highlights

| Concern | Behavior |
|---------|----------|
| **Validation** | Multi-stage LinkML / OntoGPT ladder; errors feed repair |
| **Repair** | Bounded iterations; stop on valid or budget exhausted |
| **Extract gate** | `tools.schema_gate` revalidates YAML; invalid → block SPIRES (fail closed) |
| **Outcomes** | Explicit `REAL_SUCCESS` / `SIMULATION_REQUESTED` / `REAL_EXTRACTION_FAILED` |
| **Simulation** | Opt-in only; never a silent fallback for real failures |
| **Selection vs grounding** | Selection picks vocabularies; grounding links text to concept IDs/CURIEs |
| **Path C downstream** | Grounding/RDF only after successful extraction; default `grounding_mode=none` |
| **Observability** | Lightweight stage timing and *estimated* tokens/cost |

```text
                 SEMANTIC CONTROL PLANE
Extraction intent → Ontology + policy → Template gen
      → Validation ↔ bounded repair → DETERMINISTIC GATE
      → OntoGPT / SPIRES → optional grounding / RDF → State + provenance
```

---

## Benchmarking

| Track | Guide | Smoke |
|-------|--------|-------|
| **BC5CDR** | [`benchmarking/bc5cdr/`](benchmarking/bc5cdr/) | `run_bc5cdr_track2.py` |
| **BC2GM** | [`benchmarking/bc2gm/`](benchmarking/bc2gm/) | `run_bc2gm_track2.py` |
| **MedMentions** | [`benchmarking/medmentions/`](benchmarking/medmentions/) | `run_medmentions_track2.py` |
| MADE (pilot; full data request-based) | `demos/made/` | `run_made_eval.py` |
| PII/PHI synthetic | [`benchmarking/pii/`](benchmarking/pii/) | `run_pii_smoke.py` |

Track-2 reports schema-gate validity, outcome distribution, failure visibility, and pilot micro-F1. Simulation is not quality evidence.

---

## FAQ

### Does agentic-ontogpt replace OntoGPT or SPIRES?

**No.** OntoGPT and SPIRES already perform schema-guided extraction. agentic-ontogpt does not replace SPIRES; it automates and **governs** the work around it — ontology selection, LinkML template generation, validation, bounded repair, and deterministic extraction gating. SPIRES remains the core semantic extraction engine.

### What exactly is “agentic” about this architecture?

Ontology and schema decisions can be handled by specialized tool-using agents that share state, inspect validation feedback, and revise artifacts. That agency is deliberately **bounded** by deterministic policy, validation, execution gates, and explicit state transitions. The goal is **controlled autonomy**, not maximum autonomy.

### What happens if an agent generates an invalid LinkML schema?

Generated YAML is never trusted merely because an LLM produced it. It must pass a multi-stage validation ladder. On failure, the workflow enters a **bounded repair loop**: validation errors become feedback for regeneration, only within a predefined iteration budget.

### Can SPIRES execute if the schema remains invalid?

**No.** Immediately before SPIRES runs, a deterministic extraction gate independently revalidates the schema. If it is invalid, extraction is blocked (**fail closed**). This is programmatic control, not only prompt-level instruction.

### What are the differences between Paths A, B, and C?

Three parallel ways to run the **same conceptual stages**:

- **Path A** — Canonical Google ADK prototype (`SequentialAgent` + `LoopAgent`).
- **Path B** — Experimental graph / registry showcase (not production-equivalent to A/C).
- **Path C** — Headless pure-Python (`pipeline_runner`) for CI, tests, and ADK-free environments.

### How does simulation mode work?

Simulation is **opt-in** via `AGENTIC_ONTOGPT_MODE=simulation`. It is a first-class outcome (`SIMULATION_REQUESTED`), never silently substituted for a failed real call. Core SPIRES distinguishes `REAL_SUCCESS`, `SIMULATION_REQUESTED`, and `REAL_EXTRACTION_FAILED`. Benchmark harnesses use the same contract.

### Ontology selection vs grounding?

- **Ontology selection** — which vocabulary represents an entity *type* (e.g. RxNorm for medications).
- **Grounding** — which concept ID / CURIE within a vocabulary represents extracted *text* (e.g. “carboplatin” → a specific identifier).

### Is this ready for production clinical use?

The repository is an architectural proof of concept, not an out-of-the-box claim of clinical accuracy or decision support. Production fitness depends on your templates, data agreements, and evaluation on **your** domain. Use the Track-2 harnesses to measure schema validity, failure visibility, and extraction quality under **real** SPIRES.

### How do I evaluate accuracy for my use case?

Use the Track-2 scripts (BC5CDR, BC2GM, MedMentions) and Path C `run_pipeline`:

1. Define or refine a LinkML template for your entity types.
2. Run **oracle** (plumbing), **simulation** (CI / no keys), then **real** (API keys + ontogpt).
3. Inspect outcomes and pilot F1; refine the template and policy.

MADE full official test data remains **request-based**; the repo ships a MADE-faithful schema and synthetic pilot only.

---

## Status & limitations

- Prototype / PoC — **not** clinical decision support
- Validate extractions before any clinical use; protect PHI on external APIs
- Path B is experimental; demos degrade gracefully without `google-adk`
- RDF declares known prefixes, parses before SHACL; `structural_skip` does not claim conformance
- PII smoke uses **synthetic** data only

---

## References

- OntoGPT / SPIRES — https://github.com/monarch-initiative/ontogpt
- LinkML — https://linkml.io/
- BioPortal — https://data.bioontology.org/documentation
- MedMentions — https://github.com/chanzuckerberg/MedMentions
- BC5CDR — e.g. [JHnlp/BioCreative-V-CDR-Corpus](https://github.com/JHnlp/BioCreative-V-CDR-Corpus)
- BC2GM — BioCreative II Gene Mention (IOBES redistribution for Track 2)
- MADE 1.0 — https://pmc.ncbi.nlm.nih.gov/articles/PMC6860017/
- Google ADK workflows — https://google.github.io/adk-docs/workflows/

Changelog: [`CHANGELOG.md`](CHANGELOG.md)
