# agentic-ontogpt

**Agentic SPIRES / OntoGPT pipeline built with Google ADK**

Turn unstructured clinical text into **grounded, ontology-linked knowledge** (entities + relationships → RDF-ready) using a multi-agent system on top of [OntoGPT](https://github.com/monarch-initiative/ontogpt), [LinkML](https://linkml.io/), and the [BioPortal API](https://data.bioontology.org/documentation).

---

## What problem does this solve?

OntoGPT's SPIRES method already extracts structured knowledge from text given a **LinkML template**. In practice, building a good template is still manual:

- Which ontology should ground each clinical entity type?
- How do you author a valid OntoGPT-compliant LinkML schema?
- How do you validate it before extraction?
- How do you wire this into a repeatable, agentic workflow?

**agentic-ontogpt** automates that pipeline with specialized agents:

| Step | Agent | Role |
|------|--------|------|
| 1 | **OntologySelectorAgent** | Uses BioPortal Recommender / Search to pick the best ontology per entity (or honor user preference) |
| 2 | **TemplateGeneratorAgent** | LLM-generates an OntoGPT-compliant LinkML / SPIRES schema (few-shot from real OntoGPT templates) |
| 3 | **ValidatorAgent** + repair loop | Validates with LinkML; loops back to the generator on failure (max 3 attempts) |
| 4 | **SPIRESExtractionAgent** | Runs OntoGPT SPIRES on the clinical text → structured + grounded output (RDF-ready) |

```
User query (entities ± preferred ontologies + clinical text)
        │
        ▼
 OntologySelectorAgent  ──► BioPortal Recommender / Search
        │
        ▼
┌─ TemplateRepairLoop (LoopAgent ≤ 3) ─┐
│  TemplateGeneratorAgent (few-shot)   │
│           ↕                          │
│  ValidatorAgent (linkml validate)    │
└─────────────────────────────────────┘
        │
        ▼
 SPIRESExtractionAgent  ──► OntoGPT SPIRESEngine (or simulation)
        │
        ▼
 Grounded structured output (entities, relations, CURIEs)
```

---

## Key design principles

| Principle | How we follow it |
|-----------|------------------|
| **Spec-driven** | Every agent has a contract under [`docs/specs/`](docs/specs/) (goal, I/O, tools, success criteria). Code implements the spec. |
| **ADK-native** | Agents are Google [ADK](https://google.github.io/adk-docs/) packages so you can run them with `adk run` / `adk web` and plug into CI. |
| **Composable** | New agents = new folder under `agents/` + new spec + register in the pipeline. |
| **Demo-first** | The Jupyter notebook in [`demos/`](demos/) is the living end-to-end demonstration. |

---

## Repository layout

```
agentic-ontogpt/
├── agents/                     # ADK agent packages
│   ├── pipeline/               # Sequential + Loop orchestration (runnable today)
│   ├── ontology_selector/      # reserved for standalone promotion
│   ├── template_generator/
│   ├── validator/
│   └── spires_extractor/
├── tools/                      # Pure Python tools (BioPortal, LinkML, SPIRES)
├── demos/                      # Jupyter demonstration notebooks
├── docs/
│   ├── architecture.md
│   ├── specs/                  # Agent & pipeline specifications
│   └── cookbook/               # ADK development cookbook
├── tests/
├── .github/workflows/          # CI (lint + pytest; ADK eval placeholder)
├── pyproject.toml
└── README.md
```

---

## Quick start

```bash
git clone https://github.com/YPCC/agentic-ontogpt.git
cd agentic-ontogpt

python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

cp .env.example .env
# Edit .env:
#   GOOGLE_API_KEY=...          # Gemini / Google AI Studio
#   BIOPORTAL_API_KEY=...       # https://bioportal.bioontology.org/account

# Interactive demo
jupyter notebook demos/OntoGPT_LinkML_Agent_Prototype.ipynb

# Or run the pipeline agent via ADK CLI
adk run agents/pipeline
# adk web agents/
```

Optional (real OntoGPT SPIRES engine instead of simulation):

```bash
pip install -e ".[ontogpt]"
# Configure an OpenAI-compatible key for OntoGPT / OAK as needed
```

---

## Sample demo scenario

**Clinical text**

> Melanoma is an aggressive skin cancer. Activating mutations in the BRAF gene, particularly the V600E variant, are found in approximately 50% of cutaneous melanomas. The BRAF inhibitor vemurafenib has demonstrated significant clinical benefit in patients with BRAF-mutant melanoma.

**Entity types:** Disease, Gene, Drug

**Preferred ontologies:** Disease → MONDO, Gene → HGNC, Drug → (agent chooses DRON/CHEBI)

**Expected outcome**

- Ontology mapping confirmed/refined
- Validated LinkML/SPIRES template for entities + Disease–Gene and Drug–Disease relations
- Structured extraction with grounded CURIEs (e.g. `MONDO:0005105`, `HGNC:1097`, `CHEBI:63637`)

Run this flow from the notebook cell **"End-to-end Sample Demo"** or via `adk run agents/pipeline`.

---

## Stack

- **Google ADK** – multi-agent orchestration (`LlmAgent`, `SequentialAgent`, `LoopAgent`)
- **OntoGPT / SPIRES** – schema-guided extraction + ontology grounding
- **LinkML** – schema language + validation
- **BioPortal API** – ontology recommendation and term search
- **Gemini** – LLM for selector / generator / validator / extractor agents

---

## Adding a new agent

1. Write the spec in `docs/specs/<agent_name>.md`
2. Implement tools (if any) under `tools/`
3. Create `agents/<agent_name>/agent.py` following the ADK pattern
4. Wire it into `agents/pipeline`
5. Add tests and (optionally) a CI job

See the [ADK Development Cookbook](docs/cookbook/README.md) for patterns and checklists.

---

## Status

| Area | Status |
|------|--------|
| Four-agent pipeline (selector → generator → validator → extractor) | ✅ |
| Repair loop via `LoopAgent` | ✅ |
| Demo notebook | ✅ |
| Spec stubs + cookbook | ✅ |
| Unit smoke tests + CI workflow | ✅ |
| Full ADK 2.0 graph edges & production RDF export | 🚧 |
| Evaluation harness / richer CI | 🚧 |

---

## References

- [OntoGPT](https://github.com/monarch-initiative/ontogpt) & [SPIRES paper](https://arxiv.org/abs/2304.02711)
- [LinkML](https://linkml.io/) / [Custom OntoGPT schemas](https://monarch-initiative.github.io/ontogpt/custom/)
- [BioPortal API](https://data.bioontology.org/documentation)
- [Google ADK](https://google.github.io/adk-docs/) / [ADK 2.0](https://google.github.io/adk-docs/2.0/)

---

## License

Apache-2.0 (aligned with OntoGPT, LinkML, and ADK ecosystems)
