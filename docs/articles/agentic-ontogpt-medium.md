# Agentic OntoGPT: Automating Ontology Selection, LinkML Generation, and SPIRES Extraction

*A semantic control plane around OntoGPT/SPIRES — policy-governed ontology choice, iterative schema engineering, explicit failure modes, and auditable runs.*

**Code:** [github.com/YPCC/agentic-ontogpt](https://github.com/YPCC/agentic-ontogpt)

---

## The problem starts before extraction

A researcher wants drugs, adverse events, and relations from a new corpus. [OntoGPT](https://github.com/monarch-initiative/ontogpt)’s **SPIRES** engine can extract them — once someone has chosen ontologies, authored a valid LinkML template, debugged load failures, and preserved enough configuration to audit the job later.

SPIRES already solves **schema-guided semantic extraction**. What remains expensive is the **semantic-engineering workflow around it**.

**Agentic OntoGPT** makes that workflow executable: ontology choice becomes policy-governed, schema creation becomes iterative, validation becomes a gate, failures become explicit states, and every run becomes auditable.

> OntoGPT provides the extraction engine. Agentic OntoGPT is a **semantic control plane** around schema design, ontology selection, validation, repair, execution, and provenance.

---

## Conventional OntoGPT vs Agentic OntoGPT

| Concern | Conventional workflow | Agentic OntoGPT |
|---------|----------------------|-----------------|
| Entity model | Human-defined | Agent-assisted from the extraction brief |
| Ontology selection | Manual | BioPortal-assisted + **policy filter** |
| Template authoring | Manual LinkML | LLM-generated under OntoGPT conventions |
| Validation | Developer-driven | Multi-stage ladder |
| Repair | Manual edits | Bounded, error-directed regeneration |
| Extraction | SPIRES | SPIRES (unchanged) |
| Failures | Ad hoc | Explicit outcomes; no silent simulation |
| Provenance | Ad hoc | Per-run manifest |
| Human control | External | Optional approval checkpoints |

### What is actually new here?

The novelty is not another extraction model. SPIRES remains the engine. The experiment is whether **semantic engineering itself** can become a governed, executable pipeline: from “extract from this text” to “construct and operate a trustworthy extraction pipeline for this semantic task.”

---

## A complete worked trace

**Request**

```yaml
text: >
  The patient developed severe neutropenia after receiving carboplatin.
entity_types: [Medication, AdverseEvent, Severity]
relations:
  - medication_causes_adverse_event
  - adverse_event_has_severity
```

**Ontology selection (after policy)**

```text
Medication   → RXNORM
AdverseEvent → MEDDRA
Severity     → NCIT
```

Denylisted sources (e.g. `STY`) are rejected even if a recommender ranks them highly. User preferences apply only when policy allows them.

**Validation failure (illustrative)**

```json
{
  "valid": false,
  "validation_completeness": "invalid",
  "errors": [
    "OntoGPT convention: missing import 'core'",
    "No class with tree_root: true"
  ]
}
```

**Repair**  
The control loop validates, then regenerates with the **validation report** as input, and stops as soon as the schema is valid (or when the iteration budget is exhausted). Each revision is recorded (iteration, content hash, validity). The ADK path uses a `ValidationExitAgent` that escalates when `validation_result.valid` is true; the headless path uses the same early-exit controller in pure Python.

**Gate**  
Invalid final schema → extraction blocked (`REAL_EXTRACTION_FAILED`), not replaced by a success fixture.

**Outcomes**

| Outcome | Meaning |
|---------|---------|
| `REAL_SUCCESS` | Real SPIRES path completed |
| `SIMULATION_REQUESTED` | Explicit `AGENTIC_ONTOGPT_MODE=simulation` |
| `REAL_EXTRACTION_FAILED` | Real error or schema gate |

Simulation is for CI and demos. It is not an extraction-quality metric.

**Grounding (separate step)**  
Selection chose RXNORM for the *type* Medication. Grounding resolves the *span* `"carboplatin"` to a concept identifier. Those are different decisions.

---

## What “agentic” means here

Specialized components operate under **separate contracts**, call **purpose-specific tools**, share **structured state**, evaluate intermediate artifacts, and **revise** them before downstream execution.

The pipeline is **bounded and mostly sequential**. It does not claim open-ended autonomous planning. “Agentic” here means tool-using, stateful revision under policy — a control plane, not unconstrained agency.

---

## Semantic control plane

```text
            SEMANTIC CONTROL PLANE
┌──────────────────────────────────────────┐
│ Ontology policy                          │
│ Schema generation + error-directed repair│
│ Validation ladder + completeness         │
│ Human approval (headless; ADK pattern)   │
│ Provenance + observability               │
└──────────────────┬───────────────────────┘
                   │ governed template
                   ▼
             SPIRES execution
                   │
                   ▼
        grounded semantic artifacts
        (RDF-exportable when configured)
```

**Two runtimes, one contract:** Google ADK agents for interactive workflows; `run_pipeline()` for tests and CI without ADK.

ADK orchestration models and SPIRES models are separately configurable (`ADK_LLM_MODEL`, `SPIRES_LLM_MODEL`).

### Shared state

```yaml
pipeline_state:
  source_text: string
  selected_ontologies: {type: acronym}
  generated_schema_yaml: string
  schema_version: integer
  schema_history: [{iteration, sha256, valid, ...}]  # full repair chain
  validation_report: object  # includes validation_completeness
  extraction_result: object  # outcome enum
  grounding_report: object
  provenance_manifest: object
  execution_mode: real | simulation
```

Optional **human approval** checkpoints run in the headless pipeline after ontology selection and after schema validation (`APPROVAL_MODE=auto|require|reject`). That is the control pattern for equivalent interactive ADK deployment.

---

## Validation ladder

1. YAML syntax  
2. Required keys (`id`, `name`, `imports`, `classes`)  
3. LinkML metamodel (`linkml validate` when the CLI is available)  
4. OntoGPT conventions (`linkml:types`, `core`, `NamedEntity`, `tree_root`) — **hard fail**  
5. Optional OntoGPT template load when installed  

When the LinkML CLI is unavailable, the metamodel stage is recorded as **skipped** (with a warning), not as a silent pass. OntoGPT convention checks still gate validity. Results distinguish:

| `validation_completeness` | Meaning |
|---------------------------|---------|
| `full` | All stages ran and passed |
| `partial` | Valid, but some optional stages skipped |
| `invalid` | Hard errors present |

---

## Ontology selection is not ontology grounding

| Decision | Question |
|----------|----------|
| **Selection** | Which vocabulary fits this entity *type*? |
| **Grounding** | Which *concept* does this span denote? |

Policy enforces allowlists, denylists, preferred-by-type maps, and minimum recommender scores. BioPortal helps source fitness; it does not by itself resolve every ambiguous mention.

---

## Clinical context beyond entity lists

Binary edges alone are unsafe for:

> “The patient denies rash, but her mother previously developed a rash after penicillin.”

A clinical-modifiers schema carries **assertion**, **temporality**, **experiencer**, **certainty**, and span fields. That does not solve clinical NLP; it refuses to pretend entity lists alone are sufficient.

---

## Evaluation

### Control-flow ablation harness

| Config | Meaning |
|--------|---------|
| **A** | Hand-authored template |
| **B** | One-shot generate |
| **C** | Generate + validate once |
| **D** | Policy + validate + repair + gate |

The offline A–D suite tests **validation, gating, repair, and policy behavior** with deterministic fixtures. It is a **control-flow ablation**, not yet a model-quality study. A real-model ablation (identical prompts and data across one-shot, validate-once, and repair-loop) is the natural next empirical step.

Deterministic smoke tests verify the repair controller, validation gate, and state transitions — including the full schema revision history. Separately, the ADK generator is instructed to perform error-directed LLM repair from the validation report.

### Grounding smoke (MedMentions-style)

**Protocol:** linking given gold spans; exact CUI match after normalization.

On a **50-abstract** subset, the offline train-lexicon baseline achieved:

| Metric | Value |
|--------|------:|
| Precision | 0.786 |
| Recall | 0.449 |
| F1 | 0.571 |

High precision with lower recall is expected for a majority-CUI surface lexicon. This is a **plumbing baseline**, not a state-of-the-art entity-linking claim. Literature systems (different tasks, splits, and matching rules) provide context, not a controlled head-to-head.

### Component metrics

Selection coverage, first-pass vs repaired validity, repair iterations, extraction outcome mix, grounding rate, and stage latency/cost estimates are first-class — not only end-to-end F1.

---

## Provenance

Runs record pipeline version, git commit when available, model ids, package versions, source and schema hashes, **schema revision history**, validation completeness, extraction outcome, and environment flags.

**Reproducibility** means reconstructable execution context and measurable repeatability — not byte-identical LLM output across providers and temperatures.

Structured results are **RDF-exportable** (Turtle; SHACL via `pyshacl` or a documented structural fallback). Export paths exist; production knowledge-graph governance is not claimed as finished.

---

## Limitations and safety

- Not a clinical decision-support system; outputs need independent validation.  
- Do not send PHI to external LLM or ontology APIs without institutional controls.  
- Ontology grounding is not clinical truth.  
- Simulation fixtures are not quality measurements.  
- Smoke subsets and synthetic notes are not real-world performance evidence.

---

## Try it

```bash
git clone https://github.com/YPCC/agentic-ontogpt.git
cd agentic-ontogpt
python -m venv .venv && source .venv/bin/activate
pip install pyyaml requests linkml pytest
cp .env.example .env
python -m pytest tests/ -q

export AGENTIC_ONTOGPT_MODE=simulation
python -c "
from tools.pipeline_runner import run_pipeline
s = run_pipeline(
  'Patient developed severe neutropenia after carboplatin.',
  ['Medication', 'AdverseEvent'],
  ontology_preferences={'Medication': 'RXNORM', 'AdverseEvent': 'MEDDRA'})
print(s.selected_ontologies)
print(s.validation_report.get('validation_completeness'))
print(len(s.schema_history), 'schema revisions')
print(s.extraction_result.get('outcome'))
"

python scripts/run_ablation.py --mode simulation
python scripts/run_grounding_benchmark.py --limit 50 --mode lexicon
```

---

## Roadmap

Entity-type-scoped recommender lists; real-model ablations; stronger grounding than first-hit Annotator; ontology release pinning in manifests; fuller SHACL libraries; cost-aware routing between deterministic NLP and SPIRES.

**Design principle:** human-readable failure modes over silent success.

---

## Conclusion

The unit of automation moves from filling slots in a hand-written template to **operating a governed semantic pipeline**: policy, iteration, gates, outcomes, and audit trails around an extraction engine that already works.

That is the contribution of Agentic OntoGPT — a semantic control plane around SPIRES, demonstrated as a prototype you can run, inspect, and extend.

---

## References

- OntoGPT / SPIRES — https://github.com/monarch-initiative/ontogpt  
- LinkML — https://linkml.io/  
- BioPortal — https://data.bioontology.org/documentation  
- MedMentions — https://github.com/chanzuckerberg/MedMentions  
- MADE 1.0 — https://pmc.ncbi.nlm.nih.gov/articles/PMC6860017/  
- Google ADK — https://google.github.io/adk-docs/  
- Implementation — https://github.com/YPCC/agentic-ontogpt  

*Architectural prototype — not medical advice; not for clinical decisions without independent validation.*
