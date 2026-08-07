# MedMentions ST21pv — Smoke benchmark (50 test abstracts)

**UTC:** 2026-08-07T00:18:15Z  
**Method:** train-lexicon exact match (word-boundary, min freq 3, min len 4)

## Results

| System / mode | P | R | **F1** | Notes |
|---------------|---|---|--------|-------|
| TaggerOne (published) | — | — | ~0.45 | CUI linking, full test |
| BioBERT STY (published) | — | — | ~0.64 | Semantic type |
| Exact match CUI (literature) | — | — | ~0.38 | MedLinker paper |
| **Train lexicon (text+ST)** | **0.320** | **0.376** | **0.346** | This run, 50 test docs |
| Train lexicon (text only) | 0.351 | 0.414 | 0.380 | Ignore type |
| oracle_gold | 1.000 | 1.000 | 1.000 | Plumbing only |
| no-LLM empty | 0.000 | 0.000 | 0.000 | No OntoGPT |

Lexicon size: **8,301** train surface forms.

## Real SPIRES (requires API key)

```bash
pip install ontogpt oaklib
export OPENAI_API_KEY=...
python scripts/run_medmentions_benchmark.py --limit 50
```
