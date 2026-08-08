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
| **Track 2** | Evidence harnesses on open literature NER corpora (outcomes + pilot F1) |

---

## [Unreleased]

### Added

#### Track 2 — open literature evaluation foundation

- **Shared** `tools/track2_eval.py` — schema gate, shared SPIRES outcomes, oracle mode, micro P/R/F1, provenance helpers
- **MedMentions ST21pv** — `scripts/run_medmentions_track2.py`; control-plane metrics (schema validity, outcome distribution, failure visibility) + text+ST micro-F1; results under `benchmarking/medmentions/results_track2_*`
- **BC5CDR** (Chemical + Disease)
  - `scripts/download_bc5cdr.py` / `convert_bc5cdr.py`
  - `templates/bc5cdr.yaml`
  - `scripts/run_bc5cdr_track2.py` (simulation / oracle / real)
  - `benchmarking/bc5cdr/README.md`
- **BC2GM** (Gene/Protein — genomics/proteomics literature NER)
  - `scripts/download_bc2gm.py` / `convert_bc2gm.py`
  - `templates/bc2gm.yaml`
  - `scripts/run_bc2gm_track2.py` (simulation / oracle / real)
  - `benchmarking/bc2gm/README.md`
- Tests: `tests/test_medmentions_track2.py`, `tests/test_track2_bc5cdr_bc2gm.py`

#### Documentation

- **README** restructured: hero image → what this is / showcases → quick start → Paths A/B/C → architecture → benchmarking → **FAQ** → status & references
- FAQ covers: SPIRES not replaced, controlled agency, invalid schema / fail-closed gate, paths, simulation outcomes, selection vs grounding, production readiness, evaluation workflow

### Fixed (Track 1 — control-plane honesty)

- **Benchmarks:** MADE (`scripts/run_made_eval.py`) and MedMentions harnesses use shared `tools.spires` outcomes — no silent gold simulation on real failure
- **Path C:** grounding/RDF run only after extraction outcome ∈ `{REAL_SUCCESS, SIMULATION_REQUESTED}`; skipped with explicit reason otherwise
- **Path C:** default `grounding_mode="none"` — callers must pass `lexicon` or `bioportal` to resolve concepts
- **Path C / SPIRES:** `REAL_EXTRACTION_FAILED` marks extraction as blocked for downstream gating
- **CI:** Ruff is a **failing** quality gate (`ruff check tools agents tests`; removed `|| true`); intentional broad `except` rules ignored via `pyproject.toml`

### Planned (not yet claimed as shipped)

- Per-entity-type BioPortal ranking before policy (selection quality)
- `concept_id` / optional `umls_cui` rename in grounding public API
- Path C `profile="full"` (grounding + RDF convenience preset)
- Real SPIRES quality runs on BC5CDR / BC2GM with published comparison tables (requires API keys + pinned ontogpt)
- Path B pinned ADK graph API in CI (until then Path B stays experimental)

---

## [0.1.0] — Path A foundation + Path B additive showcase

First tagged narrative baseline of the repository as a **semantic control plane PoC**.

### Path A (canonical)

- ADK Sequential + Loop pipeline in `agents/pipeline/agent.py`
- Ontology selection tools, template generation, validation ladder, SPIRES extract tool
- Bounded repair via `LoopAgent` + validation-oriented exit agent
- Explicit runtime outcomes in core SPIRES integration

### Path B (experimental, additive)

- `agents/registry.py` — `build_*` factory registry
- `agents/graph_workflow.py` / `agents/graph_repair.py` — graph / sequential-from-factories demos
- Demos under `demos/run_adk_graph_demo.py`, `run_adk_repair_graph_demo.py`
- **Does not** modify or replace Path A product entrypoints; **not** claimed equivalent to A/C

### Path C (headless)

- `tools/pipeline_runner.py` — policy → repair → gated extract → provenance
- `agents/modular_compose.py` — modular tool composition without ADK
- Strongest deterministic extract enforcement for CI

### Shared governance (cross-path)

- **`tools/schema_gate.py`** — single deterministic extract gate (re-validate YAML; honor prior `valid=False`)
  - Wired into SPIRES core, Path A tool, modular SPIRES, Path C runner
- Optional Path C downstream: `enable_grounding`, `enable_rdf`
- RDF export: declare known ontology prefixes; parse-before-SHACL; no false conformance without `pyshacl`/`rdflib`
- Enterprise auth docs: `docs/AUTH_ADC.md`, `.env.adc.example` (Vertex + ADC vs API keys)

### Benchmarks & demos (supporting)

- MADE 1.0 template + eval harness (request-based full data still external)
- MedMentions ST21pv smoke / Track 2 scripts
- PII/PHI synthetic smoke (PIIMB / ASQ-PHI) — separate from SPIRES pipeline
- Ablation harness (control-flow / gating behavior in simulation)
- Failure-modes / repair-loop notebook under `demos/`

### Documentation

- Root `README.md` — parallel paths A/B/C, real vs simulation (later expanded with FAQ)
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

Suggested next release candidate after Unreleased lands: **0.2.0** (Track 2 foundation + Track 1 honesty fixes + README/FAQ).

---

## How maintainers should update this file

1. Under **[Unreleased]**, add bullets as PRs land (Added / Changed / Fixed / Deprecated / Security).
2. On release, move Unreleased → a dated `## [x.y.z]` section and bump `pyproject.toml`.
3. Tag Path A / B / C / Track 2 in the bullet when the change is scoped.
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
- Path overview + FAQ: root `README.md`
- Auth: `docs/AUTH_ADC.md`
- Track 2 guides: `benchmarking/bc5cdr/`, `benchmarking/bc2gm/`, `benchmarking/medmentions/`
