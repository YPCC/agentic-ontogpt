# Changelog

All notable changes to **agentic-ontogpt** are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project aims to follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
once it leaves the prototype stage.

**Current package version:** `0.1.0` (see `pyproject.toml` / `PipelineState.pipeline_version`).

---

## Why this file exists

This repository started as a **Path A–only** ADK Sequential/Loop prototype around OntoGPT/SPIRES.
It is evolving toward a production-grade semantic control plane. Maintaining a changelog helps:

- Record **what shipped when** (features vs experiments vs docs)
- Separate **canonical path** changes from **showcase / experimental** paths
- Support reviewers, CI, and future releases without relying on chat history
- Make breaking changes and honesty about maturity explicit (e.g. Path B ≠ Path A)

**Convention for this project**

| Tag in notes | Meaning |
|--------------|---------|
| **Path A** | Canonical ADK Sequential + Loop (`agents/pipeline/agent.py`) — default product path |
| **Path B** | Experimental graph / registry showcase — additive; must not break Path A |
| **Path C** | Headless pure-Python runner — strongest deterministic gates; CI-friendly |
| **Control plane** | Policy → schema gen/validate → bounded repair → gated extract → optional grounding/RDF |

---

## [Unreleased]

### Planned (not yet claimed as shipped)

- Per-entity-type BioPortal ranking before policy (selection quality)
- `concept_id` / optional `umls_cui` rename in grounding public API
- Path C `profile="full"` (grounding + RDF on by default as a named profile)
- Pin and CI-test ADK 2.x graph API before advertising Path B parity
- Align remaining benchmark scripts on remote with no silent simulation
- Production packaging: deploy samples, durable state, real provider telemetry

---

## [0.1.0] — 2026-08 — Prototype control plane

First coherent open release of the agentic control layer around OntoGPT/SPIRES.

### Path A — initial canonical path (foundation)

Shipped first as the primary ADK workflow:

- `SequentialAgent` + `LoopAgent` orchestration in `agents/pipeline/`
- Roles: ontology selection → template generate ↔ validate (bounded) → SPIRES extract
- Multi-stage LinkML / OntoGPT validation ladder
- Error-directed generator instructions (consume `validation_result`)
- Explicit extraction outcomes (`REAL_SUCCESS` | `SIMULATION_REQUESTED` | `REAL_EXTRACTION_FAILED`)
- Simulation **opt-in only** (`AGENTIC_ONTOGPT_MODE=simulation`); no silent fallback on real failure in core SPIRES

### Path C — headless / CI twin

Added so tests and notebooks do not depend on ADK:

- `tools/pipeline_runner.run_pipeline` — policy → repair → **hard extract gate** → provenance
- Ontology allow/deny / preferred-by-type policy
- `PipelineState` + run manifest (git/provenance fields)
- Human approval checkpoints (headless; `APPROVAL_MODE`)
- Lightweight observability (stage timers, estimated tokens/cost)

### Path B — next version line (experimental, additive)

Introduced **without** rewriting Path A’s `agents/pipeline/agent.py`:

| Addition | Role |
|----------|------|
| `agents/registry.py` | `build_*` factory registry for composable agents |
| Modular packages under `agents/{ontology_selector,template_generator,validator,spires_extractor}/` | Same tools as Path A, importable as factories |
| `agents/graph_workflow.py` | Workflow assembly when ADK exposes it; Sequential-from-factories fallback |
| `agents/graph_repair.py` | `REFINE` / `DONE` gate + experimental multi-iter repair showcase |
| `demos/run_adk_graph_demo.py` | Prove factories compose into an ADK-ready root |
| `demos/run_adk_repair_graph_demo.py` | Gate unit demo + repair graph modes |
| `agents/modular_compose.py` + `demos/run_modular_agents_demo.py` | Headless modular path with parity checks |

**Maturity note (honest):** Path B is a **compatibility / composition showcase**. Multi-iteration repair remains strongest on Path A `LoopAgent` and Path C `repair_until_valid`. Path B is **not** yet an equivalent production graph runtime.

### Shared governance (cross-path)

- **`tools/schema_gate.py`** — single deterministic extract gate (re-validate YAML; honor prior `valid=False`)
  - Wired into SPIRES core, Path A tool, modular SPIRES, Path C runner
- Optional Path C downstream: `enable_grounding`, `enable_rdf`
- RDF export: declare known ontology prefixes; parse-before-SHACL; no false conformance without `pyshacl`/`rdflib`
- Enterprise auth docs: `docs/AUTH_ADC.md`, `.env.adc.example` (Vertex + ADC vs API keys)

### Benchmarks & demos (supporting)

- MADE 1.0 template + eval harness (request-based full data still external)
- MedMentions ST21pv smoke scripts
- PII/PHI synthetic smoke (PIIMB / ASQ-PHI) — separate from SPIRES pipeline
- Ablation harness (control-flow / gating behavior in simulation)
- Failure-modes / repair-loop notebook under `demos/`

### Documentation

- Root `README.md` — parallel paths A/B/C, real vs simulation
- `docs/AUTH_ADC.md` — enterprise Gemini via ADC
- Medium article assets under `docs/articles/` (narrative; code is source of truth)

---

## Versioning policy (toward production)

Until **1.0.0**:

| Version bump | When |
|--------------|------|
| **0.x patch** | Fixes, docs, tests, honesty/claim updates, gate/RDF hardening |
| **0.x minor** | New path capability that does not break Path A public entrypoints |
| **1.0.0** | Only when: Path A has deterministic extract guarantees in CI, real SPIRES smoke on a pinned stack, no overstated Path B claims, and a documented deploy/auth story |

**Do not** bump to 1.0 solely because Path B demos exist.

---

## How maintainers should update this file

1. Under **[Unreleased]**, add bullets as PRs land (Added / Changed / Fixed / Deprecated / Security).
2. On release, move Unreleased → a dated `## [x.y.z]` section and bump `pyproject.toml`.
3. Tag Path A / B / C in the bullet when the change is path-specific.
4. Prefer **under-claiming** experimental graph work over implying parity with Path C gates.

Example:

```markdown
### Added
- **Path C:** `profile="full"` enables grounding + RDF after extract

### Fixed
- **Path A:** extract tool uses `schema_gate` only (no duplicate ladder code)
```

---

## Related

- Package version: `pyproject.toml`
- Runtime version in manifests: `tools/pipeline_state.py` → `_package_version()`
- Path overview: root `README.md`
- Auth: `docs/AUTH_ADC.md`
