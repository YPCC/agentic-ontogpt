# MADE 1.0 — Comparative results

**Run ID:** `made-pilot-20260806T234550Z`  
**Timestamp (UTC):** 2026-08-06T23:45:50.617723+00:00  
**Extraction mode:** `simulation`  
**Template SHA-256:** `914bd9f2b22cfed9…`

## Scores vs public baselines

| System | NER F1 | RI F1 | E2E F1 | Evaluation set |
|--------|--------|-------|--------|----------------|
| MADE best team (2019 challenge) | 0.82 | 0.86 | 0.61 | Official test (213 notes) |
| MADE ensemble (2019 challenge) | 0.85 | 0.87 | 0.66 | Official test (213 notes) |
| **agentic-ontogpt SPIRES (this run)** | **1.0** | **1.0** | **1.0** | Synthetic single note (pilot) |

> **Disclaimer:** This run is a **pipeline pilot** on a synthetic MADE-style note in `simulation` mode.
> Perfect pilot F1 validates schema → extract → score plumbing; it is **not** comparable to official MADE test-set scores.
> Official data and BioC eval script: request via http://bio-nlp.org/dataset/made1

## Entity F1 by type (this run)

| Type | P | R | F1 | tp | fp | fn |
|------|---|---|----|----|----|-----|
| ADE | 1.000 | 1.000 | 1.000 | 2 | 0 | 0 |
| Dosage | 1.000 | 1.000 | 1.000 | 2 | 0 | 0 |
| Drug | 1.000 | 1.000 | 1.000 | 5 | 0 | 0 |
| Frequency | 1.000 | 1.000 | 1.000 | 2 | 0 | 0 |
| Indication | 1.000 | 1.000 | 1.000 | 2 | 0 | 0 |
| Route | 1.000 | 1.000 | 1.000 | 1 | 0 | 0 |
| SSLIF | 1.000 | 1.000 | 1.000 | 4 | 0 | 0 |
| Severity | 1.000 | 1.000 | 1.000 | 2 | 0 | 0 |

## Provenance pointers

| Field | Value |
|-------|--------|
| Repository | https://github.com/YPCC/agentic-ontogpt |
| Branch | main |
| Template | `templates/made_1_0.yaml` |
| Runner | `scripts/run_made_eval.py` |
| Full provenance JSON | [`results/provenance.json`](provenance.json) |
| Raw metrics JSON | [`results/made_eval_results.json`](made_eval_results.json) |

Paper: Jagannatha et al., *Drug Safety* 2019 — [PMC6860017](https://pmc.ncbi.nlm.nih.gov/articles/PMC6860017/)
