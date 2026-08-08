# PII / PHI smoke benchmarks

Two public **synthetic** resources (no real patient PHI required):

| Corpus | Role | Local smoke |
|--------|------|-------------|
| **PIIMB** | General PII masking (AI4Privacy EN slice) | `piimb/smoke_50.jsonl` |
| **ASQ-PHI** | Clinical query-style **HIPAA Safe Harbor** tags | `asq_phi/smoke_50.jsonl` |

Schemas: [`schemas/`](schemas/)  
Results: [`results/`](results/)

## Quick start

From repo root:

```bash
# Offline heuristic baseline (no API key)
python scripts/run_pii_smoke.py --limit 50

# Optional GPT extraction (requires OPENAI_API_KEY)
export OPENAI_API_KEY=sk-...
python scripts/run_pii_smoke.py --backend gpt --limit 50
```

Outputs:

- `benchmarking/pii/results/smoke_pii_f1.json` — precision / recall / F1  
- `benchmarking/pii/results/SMOKE_REPORT.md` — human summary  

## Data provenance

**PIIMB**

```text
Hugging Face: piimb/pii-masking-benchmark  (split: test)
Smoke: first 50 English ai4privacy-en rows → piimb/smoke_50.jsonl
```

**ASQ-PHI**

```text
Source: https://github.com/JamesWeatherhead/asq-phi
File:   data/synthetic_clinical_queries.txt  (MIT; fully synthetic)
Smoke:  asq_phi/smoke_50.jsonl
```

If the full ASQ-PHI text is missing:

```bash
curl -sL -o benchmarking/pii/asq_phi/synthetic_clinical_queries.txt \
  https://raw.githubusercontent.com/JamesWeatherhead/asq-phi/main/data/synthetic_clinical_queries.txt
```

## Metrics

Value-level exact and soft (substring) match of gold spans vs predictions.

**Heuristic results are a plumbing floor**, not comparable to GLiNER / PIIMB leaderboard numbers.

## Entity schemas

- `schemas/piimb_entities.yaml` — PIIMB-style labels  
- `schemas/asq_phi_entities.yaml` — ASQ-PHI HIPAA identifier types  

## Safety

- Synthetic data only in this folder.  
- Do not send real clinical PHI to external LLM APIs without institutional controls.  
- i2b2 / n2c2 real clinical de-id requires a separate DUA and is **not** included here.
