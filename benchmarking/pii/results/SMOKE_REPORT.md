# PII/PHI Smoke Benchmark Results

## Data
- **PIIMB:** HuggingFace `piimb/pii-masking-benchmark` — 50 English (`ai4privacy-en`) sentences
- **ASQ-PHI:** GitHub `JamesWeatherhead/asq-phi` — 50 synthetic clinical queries (HIPAA Safe Harbor tags)

## Extractor
Heuristic regex / name patterns (**default offline**).  
Optional: `--backend gpt` with `OPENAI_API_KEY`.

This is a **plumbing baseline**, not a leaderboard claim.

## Results (limit=50, heuristic)

### PIIMB (value match)

| Metric | Exact | Soft |
|--------|------:|-----:|
| Precision | ~0.41 | ~0.45 |
| Recall | ~0.12 | ~0.14 |
| F1 | ~0.19 | ~0.21 |

### ASQ-PHI (value match)

| Metric | Exact | Soft |
|--------|------:|-----:|
| Precision | ~0.72 | ~0.88 |
| Recall | ~0.49 | ~0.60 |
| F1 | ~0.58 | ~0.71 |

Exact numbers: `smoke_pii_f1.json`.

## How to run

```bash
python scripts/run_pii_smoke.py --limit 50
python scripts/run_pii_smoke.py --backend gpt --limit 50   # needs API key
```

See [`../README.md`](../README.md).
