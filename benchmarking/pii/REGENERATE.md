# Regenerating PII smoke subsets

Committed **samples** are small. For the full 50-row smoke used in reported F1:

## PIIMB

```python
from datasets import load_dataset
import json
ds = load_dataset("piimb/pii-masking-benchmark", split="test")
rows = []
for r in ds:
    if r.get("language") == "en" or r.get("task_name") == "ai4privacy-en":
        rows.append({
            "uid": r["uid"],
            "task_name": r["task_name"],
            "text": r["text"],
            "entities": list(r["entities"]),
            "language": r.get("language"),
        })
        if len(rows) >= 50:
            break
with open("benchmarking/pii/piimb/smoke_50.jsonl", "w") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
```

## ASQ-PHI

```bash
curl -sL -o benchmarking/pii/asq_phi/synthetic_clinical_queries.txt \
  https://raw.githubusercontent.com/JamesWeatherhead/asq-phi/main/data/synthetic_clinical_queries.txt
```

Then parse `===QUERY===` / `===PHI_TAGS===` blocks into `smoke_50.jsonl` (first 50 records).

```bash
python scripts/run_pii_smoke.py --limit 50
```
