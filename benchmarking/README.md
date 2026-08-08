# Benchmarking

Runs for **agentic-ontogpt** against public / synthetic shared-task style corpora.

| Benchmark | Folder | Task | Smoke command |
|-----------|--------|------|-----------------|
| MADE 1.0 | [`made/`](made/) | Medication + ADE NER/relations | `python scripts/run_made_eval.py` |
| MedMentions ST21pv | [`medmentions/`](medmentions/) | UMLS semantic-type NER | `python scripts/run_medmentions_benchmark.py --limit 50` |
| **PII / PHI** | [`pii/`](pii/) | PIIMB general PII + ASQ-PHI HIPAA labels | `python scripts/run_pii_smoke.py --limit 50` |
| Grounding | [`grounding/`](grounding/) | Linking given gold spans | `python scripts/run_grounding_benchmark.py --limit 50` |
| Ablations | [`ablation/`](ablation/) | Control-flow A–D | `python scripts/run_ablation.py --mode simulation` |

Each folder should contain (or link to):

- input config / entity schema  
- smoke or full subset  
- `results/` with metrics + provenance  
- short README with how to reproduce  

## General pattern

```bash
# 1) Prepare data (download/convert) if needed
# 2) Run smoke
python scripts/run_<benchmark>_….py --limit 50
# 3) Inspect
ls benchmarking/<name>/results/
```

Set `OPENAI_API_KEY` only when you intentionally want LLM-backed extraction.
Offline defaults use heuristics, lexicons, or simulation — **not** leaderboard claims.
