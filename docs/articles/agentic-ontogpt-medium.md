# Agentic OntoGPT: Building a Semantic Control Plane Around OntoGPT SPIRES

*Automating ontology selection, LinkML generation, validation, governance, and provenance—while leaving OntoGPT SPIRES as the semantic extraction engine.*

**Repository:** [github.com/YPCC/agentic-ontogpt](https://github.com/YPCC/agentic-ontogpt)

---

## Semantic extraction is only half the problem

Most discussions of biomedical information extraction focus on the extraction model itself.

Can a large language model identify diseases? Can it recognize medications? Can it extract relationships?

Those are important questions.

But in practice, many production failures occur **before** the first entity is ever extracted.

A researcher beginning a new extraction project must first answer questions such as:

- Which ontology should represent each entity type?
- Which LinkML schema should OntoGPT use?
- Is the generated schema actually valid?
- What happens if validation fails?
- Should extraction proceed?
- How can another researcher reproduce the same run months later?

These activities are rarely discussed, yet they often consume more engineering effort than the extraction itself.

OntoGPT’s SPIRES framework already provides an elegant solution for schema-guided semantic extraction.

The challenge explored in this work is different.

**Can the surrounding semantic engineering workflow become executable, governed, and observable?**

That question led to Agentic OntoGPT.

Rather than replacing SPIRES, it builds a **semantic control plane** around it.

### Why now?

Reliable tool use, structured outputs, and agent orchestration frameworks have only recently made it practical to automate parts of semantic engineering that previously required manual iteration. Rather than replacing OntoGPT, these capabilities allow the surrounding workflow—ontology choice, schema validation, repair, approval, and provenance—to become observable, testable, and policy-governed.

---

## The missing layer in semantic extraction

Traditional OntoGPT workflows generally look like this:

```text
Research question
        │
        ▼
Human chooses ontologies
        │
        ▼
Human writes LinkML schema
        │
        ▼
Human debugs schema
        │
        ▼
SPIRES extraction
        │
        ▼
Structured output
```

SPIRES performs exactly the task it was designed for.

However, everything surrounding SPIRES remains largely manual:

- ontology selection
- schema authoring
- validation
- repair
- governance
- provenance
- operational controls

Agentic OntoGPT focuses on those surrounding activities.

It treats semantic engineering itself as a workflow that can be executed, validated, measured, and audited.

---

## A semantic control plane

The architecture is best understood not as “multiple agents,” but as a **semantic control plane**.

![Semantic Control Plane architecture — six panels: high-level pipeline, bounded repair loop, validation ladder, selection vs grounding, execution state machine, and provenance flow](figures/semantic-control-plane-architecture.jpg)

*Figure 1. Agentic OntoGPT as a semantic control plane: (1) high-level architecture with shared pipeline state, (2) bounded repair loop with early exit, (3) validation ladder, (4) ontology selection vs grounding, (5) execution state machine with explicit outcomes, (6) provenance and observability flow.*

SPIRES remains the semantic extraction engine.

Everything above it governs whether and how extraction occurs.

Everything below it governs how extraction is interpreted, audited, and reused.

---

## What “agentic” means in this project

The word *agentic* is often used loosely.

In this project it has a specific meaning.

Specialized components:

- perform well-defined responsibilities,
- operate under explicit contracts,
- exchange structured state,
- invoke deterministic tools,
- evaluate intermediate artifacts,
- revise artifacts when appropriate,
- terminate according to bounded control logic.

The workflow is intentionally constrained.

It is not an open-ended autonomous planning system.

Instead, it is a governed semantic pipeline that combines LLM reasoning with deterministic validation.

---

## A complete example

Suppose a researcher wants to extract adverse drug events from biomedical literature.

The request might specify:

```text
Entity Types
- Medication
- AdverseEvent
- Severity

Relations
- medication_causes_adverse_event
- adverse_event_has_severity
```

### Step 1 – Ontology recommendation

The system recommends candidate ontologies for each entity category.

| Entity Type   | Candidate |
|---------------|-----------|
| Medication    | RxNorm    |
| AdverseEvent  | MedDRA    |
| Severity      | NCIt      |

These recommendations are then passed through a deterministic policy engine.

The policy may enforce:

- organizational allowlists,
- denylists,
- preferred ontologies,
- minimum recommendation scores,
- user preferences.

Ontology recommendation and ontology policy are separate concerns.

### Step 2 – Template generation

The template generator creates a LinkML schema compatible with OntoGPT SPIRES, including imports, entity classes, relationships, tree root, NamedEntity inheritance, and OntoGPT conventions.

### Step 3 – Validation

Generated YAML is never trusted blindly.

It passes through a validation ladder:

1. YAML syntax
2. Required keys
3. LinkML validation (when available)
4. OntoGPT conventions
5. Optional template loading

Each stage produces structured output. Validation reports are first-class artifacts.

### Step 4 – Repair

If validation fails, the repair controller does not simply restart generation.

The validation report becomes structured input to the next generation attempt. Only reported defects should be corrected while preserving valid portions of the schema.

Repair proceeds within a bounded iteration budget. If validation succeeds early, the workflow exits immediately. If it never succeeds, extraction is blocked.

### Step 5 – Explicit execution states

> **Engineering principle:** Explicit failure is preferable to implicit success.

| Outcome | Meaning |
|---------|---------|
| `REAL_SUCCESS` | SPIRES completed successfully |
| `SIMULATION_REQUESTED` | Explicit simulation mode |
| `REAL_EXTRACTION_FAILED` | Validation or execution failure |

Simulation is never used silently to hide production failures.

---

## Ontology selection is not ontology grounding

These concepts answer different questions.

| Decision | Question |
|----------|----------|
| **Ontology selection** | Which vocabulary should represent this entity *type*? |
| **Ontology grounding** | Which *concept* does this specific mention refer to? |

Selecting RxNorm for medications does not determine which RxNorm concept corresponds to the text “carboplatin.”

**Selection chooses the vocabulary. Grounding resolves the mention.**

Separating these responsibilities simplifies both evaluation and governance.

---

## Clinical semantics require more than entities

Entity extraction alone is insufficient for clinical text.

Consider:

> “The patient denies rash, but her mother previously developed a rash after penicillin.”

Simply extracting *penicillin* and *rash* loses essential meaning.

Clinical interpretation depends on additional dimensions such as:

- assertion
- temporality
- experiencer
- certainty

The project includes schemas capable of representing these modifiers alongside extracted entities.

This is not a complete clinical reasoning system. It is recognition that semantic correctness extends beyond entity recognition.

---

## Measuring the right things

End-to-end F1 tells only part of the story.

A governed extraction pipeline introduces intermediate components that deserve independent evaluation.

| Component | Example metrics |
|-----------|-----------------|
| Ontology recommendation | Coverage, policy compliance |
| Template generation | First-pass validity |
| Repair | Success rate, iterations |
| Validation | Failure distribution |
| Grounding | Precision, Recall, F1 |
| Operations | Latency, cost, API calls |

The repository also includes deterministic control-flow ablations comparing progressively richer pipeline configurations. These evaluate the workflow itself rather than claiming state-of-the-art extraction performance.

---

## Provenance matters

Reproducing an LLM workflow requires more than saving prompts.

Each execution records contextual information such as:

- pipeline version,
- git revision,
- execution mode,
- selected ontologies,
- schema fingerprint,
- validation status,
- repair iterations,
- extraction outcome,
- model configuration.

This does not guarantee identical future outputs. Language models evolve. Ontologies evolve. Prompts evolve.

Provenance makes those changes **visible and reconstructable**.

---

## From structured extraction toward knowledge graphs

Extraction results can be serialized toward RDF.

When configured, structural validation and SHACL checking can be applied before downstream knowledge graph ingestion.

The project aims to produce semantic artifacts that can participate in broader knowledge graph workflows rather than remaining isolated JSON outputs.

---

## Design principles

| Principle | Implementation |
|-----------|----------------|
| Explicit states | `REAL_SUCCESS` / `SIMULATION_REQUESTED` / `REAL_EXTRACTION_FAILED` |
| Deterministic governance | Ontology policy engine |
| Validation before execution | Extraction gate |
| Human oversight | Optional approval checkpoints |
| Auditability | Provenance manifests |
| Separation of concerns | Selection distinct from grounding |

Together these principles shift semantic extraction from an isolated inference task toward an observable engineering workflow.

---

## Current scope

The repository should be viewed as an architectural prototype.

**It demonstrates:**

- ontology recommendation and policy,
- bounded template repair,
- validation gating,
- explicit execution outcomes,
- shared pipeline state,
- provenance,
- grounding workflows,
- RDF export,
- operational instrumentation.

**It does not yet claim:**

- state-of-the-art biomedical extraction,
- autonomous semantic engineering,
- production-scale clinical deployment,
- complete reproducibility across evolving LLMs.

Those remain future research directions.

---

## Looking ahead

Near-term priorities include:

- broader empirical evaluation,
- richer grounding strategies,
- ontology version pinning,
- expanded SHACL libraries,
- confidence estimation,
- cost-aware routing,
- larger corpus benchmarks.

The broader research question remains unchanged:

**Can semantic engineering itself become executable?**

---

## Conclusion

The interesting question is no longer only whether a language model can populate a hand-written schema.

The more consequential question is whether the entire semantic engineering workflow can become governed, observable, and reproducible.

OntoGPT SPIRES already provides a powerful semantic extraction engine.

Agentic OntoGPT explores the layer around it:

- selecting ontologies,
- generating schemas,
- validating artifacts,
- repairing failures,
- governing execution,
- recording provenance,
- producing auditable semantic outputs.

The contribution is not another extraction model.

It is a **semantic control plane** for schema-guided biomedical extraction.

As semantic AI systems continue moving toward production environments, that control plane may ultimately prove just as important as the extraction engine itself.

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
