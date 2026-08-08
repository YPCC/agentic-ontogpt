# Agentic OntoGPT, Part 2: The Headless Control Plane, ADK Graphs, and Honest Benchmarks

*Same control plane. Three ways to run it. No silent failures.*

---

In [Part 1](https://github.com/YPCC/agentic-ontogpt/blob/main/docs/articles/agentic-ontogpt-medium.md) we argued for a **semantic control plane** around OntoGPT/SPIRES: select ontologies, generate LinkML, validate, repair in a bounded loop, then extract—only if the schema is valid.

Part 1 lived mainly on **Path A** (Google ADK Sequential + Loop). This short follow-up is about everything that makes the story *operational*: **Path C** (headless, deterministic), **Path B** (experimental ADK graphs), and **Track-2 benchmarks** that refuse to lie about simulation.

> **SPIRES is still the engine.** We still do not replace it. We govern the work around it.

---

## Context at a glance

![C4 context diagram — Agentic OntoGPT semantic control plane](https://raw.githubusercontent.com/YPCC/agentic-ontogpt/main/docs/articles/figures/c4-context-agentic-ontogpt.jpg)

*C4 context view: the researcher supplies text and preferences; Agentic OntoGPT sits as the semantic control plane between clinical inputs, ontology policy, BioPortal, LLM services, and the OntoGPT/SPIRES engine—emitting schemas, extraction outputs, provenance, and optional RDF/SHACL artifacts.*

---

## One plane, three runtimes

```text
Ontology → policy → repair (gen ↔ val)×N → gated SPIRES
```

| Path | What it is | Use it when |
|------|------------|-------------|
| **A** | ADK Sequential + Loop | Product agent demo (Part 1) |
| **B** | Experimental graph / registry | Exploring ADK 2.0-style composition |
| **C** | Pure Python, no ADK | CI, notebooks, strongest gates |

**Enforcement is not identical.** Path C is the reference for fail-closed extraction. Path B is a *showcase*, not a claim of parity.

---

## Path C: governance you can run in CI

Headless entrypoint:

```python
from tools.pipeline_runner import run_pipeline

state = run_pipeline(
    "Neutropenia after carboplatin.",
    ["Medication", "AdverseEvent"],
    ontology_preferences={"Medication": "RXNORM", "AdverseEvent": "MEDDRA"},
)
print(state.extraction_result["outcome"])
# REAL_SUCCESS | SIMULATION_REQUESTED | REAL_EXTRACTION_FAILED
```

What Path C insists on:

- **Schema gate** — YAML is re-validated in code before SPIRES; invalid ⇒ no extract
- **Explicit outcomes** — simulation is opt-in (`AGENTIC_ONTOGPT_MODE=simulation`), never a silent fallback
- **Downstream only on success** — grounding/RDF run after success (or explicit simulation), not after `REAL_EXTRACTION_FAILED`
- **Default grounding off** — `grounding_mode="none"` until you ask for lexicon or BioPortal

That is controlled autonomy: agents may propose; the gate decides.

---

## Path B: ADK graphs (experimental)

Path B exists so we can compose the *same* stages with a **factory registry** and optional ADK Workflow edges—without rewriting Path A.

```bash
python demos/run_adk_graph_demo.py
python demos/run_adk_repair_graph_demo.py --max-iterations 3
```

**Figures (drop your ADK screen grabs here):**

- *[Fig. 1 — ADK run trace: ontology → template → validate → extract]*
- *[Fig. 2 — Repair loop / REFINE vs DONE gate in the console]*

Treat these as evidence of *orchestration*, not of clinical accuracy. Path B degrades gracefully without `google-adk`; it is not the production graph runtime yet.

---

## Benchmarking without theatre

Open literature Track-2 harnesses (BC5CDR, BC2GM, MedMentions) all share one contract:

| Mode | Meaning |
|------|---------|
| **Oracle** | Gold spans as predictions — plumbing only (F1 ≈ 1) |
| **Simulation** | Fixture path — CI / no API keys; **not quality** |
| **Real** | SPIRES + keys — report F1 only here |

```bash
AGENTIC_ONTOGPT_MODE=simulation python scripts/run_bc5cdr_track2.py --limit 20
python scripts/run_bc5cdr_track2.py --limit 10 --oracle
# Real: ontogpt + OPENAI_API_KEY
AGENTIC_ONTOGPT_MODE=real python scripts/run_bc5cdr_track2.py --limit 20
```

We publish **schema-gate validity**, **outcome counts**, and **failure visibility** first. Pilot micro-F1 second—and only with the mode labeled.

---

## What we still will not claim

- Clinical decision support
- Path B ≡ Path A or C
- Simulation F1 as model quality
- Official MADE leaderboard scores without request-based data access

---

## Try it

```bash
git clone https://github.com/YPCC/agentic-ontogpt.git
cd agentic-ontogpt && pip install -e ".[dev]"
export AGENTIC_ONTOGPT_MODE=simulation
python demos/run_modular_agents_demo.py --compare --made-template
python scripts/run_bc5cdr_track2.py --limit 10 --oracle
```

**Repo:** [YPCC/agentic-ontogpt](https://github.com/YPCC/agentic-ontogpt) · **FAQ & paths:** root README · **Part 1:** [control-plane thesis on Path A](https://github.com/YPCC/agentic-ontogpt/blob/main/docs/articles/agentic-ontogpt-medium.md)

*Part 2 is the operator’s note: same plane, stricter gates, honest benchmarks—and ADK graphs only where they belong.*
