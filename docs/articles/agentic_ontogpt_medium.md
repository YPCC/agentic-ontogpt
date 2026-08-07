---
title: "Agentic OntoGPT: Multi-Agent Pipelines for Ontology-Grounded Knowledge Extraction"
author: "YPCC / agentic-ontogpt contributors"
date: 2026-08-06
tags: [OntoGPT, LinkML, SPIRES, agents, BioPortal, knowledge graphs, biomedical NLP, Google ADK]
---

# Agentic OntoGPT: Multi-Agent Pipelines for Ontology-Grounded Knowledge Extraction

**Turning unstructured clinical and biomedical text into grounded, ontology-linked knowledge—with agents that choose ontologies, write LinkML templates, validate them, and run SPIRES extraction.**

Repository: [github.com/YPCC/agentic-ontogpt](https://github.com/YPCC/agentic-ontogpt)

---

## The problem

[OntoGPT](https://github.com/monarch-initiative/ontogpt) and its **SPIRES** method (Structured Prompt Interrogation and Recursive Extraction of Semantics) already show that large language models can extract structured knowledge when guided by a **LinkML schema**. In practice, though, a large share of the work is still manual:

1. **Which ontology** should ground each entity type (disease, gene, drug, adverse event, …)?
2. **How** do you author a valid, OntoGPT-compliant LinkML template for those entities and relations?
3. **How** do you validate the template before spending tokens on extraction?
4. **How** do you repeat this reliably across datasets (MADE, MedMentions, custom clinical notes)?

*Agentic OntoGPT* treats that workflow as a **multi-agent system** rather than a one-off script.

---

## The idea in one diagram

```
Clinical / PubMed text
        │
        ▼
┌───────────────────────┐
│ OntologySelectorAgent │  ← BioPortal Recommender / Search
└───────────┬───────────┘
            ▼
┌───────────────────────┐
│ TemplateGenerator     │  ← LLM + few-shot SPIRES patterns
│        ↕              │
│ ValidatorAgent        │  ← linkml validate + OntoGPT conventions
│   (repair loop ≤ 3)   │
└───────────┬───────────┘
            ▼
┌───────────────────────┐
│ SPIRESExtractionAgent │  ← OntoGPT SPIRESEngine → grounded structure
└───────────┬───────────┘
            ▼
   Entities + relations (+ CURIEs) → eval / RDF-ready output
```

Agents are implemented with **Google ADK** (`LlmAgent`, `SequentialAgent`, `LoopAgent`) so the same graph can be run from a notebook, the CLI (`adk run`), or CI.

---

## What we built

The open repository [**agentic-ontogpt**](https://github.com/YPCC/agentic-ontogpt) packages:

| Piece | Role |
|-------|------|
| **Spec-driven agents** | Contracts under `docs/specs/` for selector, generator, validator, extractor, and the full pipeline |
| **Shared tools** | BioPortal recommend/search, LinkML validate/save, SPIRES extract (real engine or simulation) |
| **ADK pipeline** | `agents/pipeline` — sequential flow with a template **repair loop** |
| **Dataset tracks** | MADE 1.0 (medication & ADE) and MedMentions ST21pv (UMLS semantic types) |
| **Benchmarking + provenance** | `benchmarking/` with metrics, comparison tables, timestamps, template hashes |

Design principles we stuck to:

- **Spec-driven** — code implements written agent contracts  
- **ADK-native** — first-class agent packages, not ad-hoc prompts  
- **Demo-first** — Jupyter demos under `demos/`  
- **Provenance** — every benchmark run records *when*, *what template*, *what mode*

---

## Track 1: MADE 1.0 (Medication & Adverse Drug Events)

[MADE 1.0](https://pmc.ncbi.nlm.nih.gov/articles/PMC6860017/) annotates EHR notes with **nine entity types** and **seven relation types** (drug attributes, indication–drug, ADE–drug, severity).

We published an OntoGPT-compliant LinkML template (`templates/made_1_0.yaml`) aligned to that schema, plus a headless eval runner. Because the official MADE release is **request-based**, the public pilot uses a synthetic MADE-style note to validate schema → extract → score plumbing. Published challenge baselines remain the reference for full-corpus comparison:

| System | NER F1 | RI F1 | E2E F1 |
|--------|--------|-------|--------|
| MADE best team (official test) | 0.82 | 0.86 | 0.61 |
| MADE ensemble | 0.85 | 0.87 | 0.66 |

Artifacts: [`benchmarking/made/`](https://github.com/YPCC/agentic-ontogpt/tree/main/benchmarking/made), [`templates/made_1_0.yaml`](https://github.com/YPCC/agentic-ontogpt/blob/main/templates/made_1_0.yaml).

---

## Track 2: MedMentions ST21pv

[MedMentions](https://github.com/chanzuckerberg/MedMentions) links PubMed title/abstract mentions to **UMLS** concepts, with the ST21pv subset focusing on **21 semantic types** useful for indexing.

We:

1. Defined an **entity × ontology map** (`configs/medmentions_st21pv_entities.yaml`) — e.g. Chemical → CHEBI, Finding → HP, Biologic Function → GO, Virus/Bacterium → NCBITAXON  
2. Shipped download / convert / benchmark scripts  
3. Ran a **50-abstract smoke test** from the official test split  

A **train-lexicon baseline** (word-boundary exact match) produced:

| Mode | P | R | F1 |
|------|---|---|-----|
| Train lexicon (text + semantic type) | 0.32 | 0.38 | **0.35** |
| Train lexicon (text only) | 0.35 | 0.41 | **0.38** |
| Published exact-match CUI (literature) | — | — | ~0.38 |
| Published TaggerOne CUI | — | — | ~0.45 |
| Published BioBERT STY | — | — | ~0.64 |

Live SPIRES scores need `ontogpt` + an API key.

---

## How the agents cooperate

**OntologySelectorAgent** calls BioPortal’s recommender (and search when needed) and returns `EntityType → OntologyAcronym`, respecting user preferences when provided.

**TemplateGeneratorAgent** emits full LinkML YAML following SPIRES conventions: `imports: linkml:types` + `core`, `NamedEntity` subclasses with optional `bioportal:` annotators, `CompoundExpression` for relations, and a `tree_root` container.

**ValidatorAgent** runs structural / `linkml validate` checks. Failures feed a **LoopAgent** (max three iterations) so the generator can repair the schema before extraction.

**SPIRESExtractionAgent** invokes OntoGPT’s `SPIRESEngine` when installed, otherwise a clearly labeled simulation so demos and CI stay runnable offline.

---

## Why this matters

Ontology-grounded extraction is only as good as the **schema and grounding choices** behind it. By making those choices explicit agents—with tools, specs, and repair loops—we get reproducible templates, clear failure modes, a path from notebooks to ADK CLI and CI, and benchmark folders that record **provenance**, not just a single F1 number.

---

## Try it

```bash
git clone https://github.com/YPCC/agentic-ontogpt.git
cd agentic-ontogpt
pip install -e ".[dev]"
cp .env.example .env
adk run agents/pipeline
python scripts/run_made_eval.py
python scripts/download_medmentions.py && python scripts/convert_medmentions.py
python scripts/run_medmentions_benchmark.py --limit 50
```

---

## References

- Mohan & Li. *MedMentions.* AKBC 2019. [GitHub](https://github.com/chanzuckerberg/MedMentions)
- Jagannatha et al. *Overview of MADE 1.0.* Drug Safety 2019. [PMC6860017](https://pmc.ncbi.nlm.nih.gov/articles/PMC6860017/)
- OntoGPT / SPIRES. [github.com/monarch-initiative/ontogpt](https://github.com/monarch-initiative/ontogpt)
- LinkML. [linkml.io](https://linkml.io/)
- BioPortal API. [data.bioontology.org](https://data.bioontology.org/documentation)
- Google ADK. [google.github.io/adk-docs](https://google.github.io/adk-docs/)

---

*Code, templates, and benchmark provenance: [github.com/YPCC/agentic-ontogpt](https://github.com/YPCC/agentic-ontogpt).*
