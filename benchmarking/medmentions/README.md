# Benchmarking — MedMentions ST21pv

Results for **agentic-ontogpt** on [MedMentions](https://github.com/chanzuckerberg/MedMentions) ST21pv (50 test abstracts smoke).

## Latest scores

| Mode | F1 (text+ST) | F1 (text only) |
|------|--------------|----------------|
| **Train lexicon baseline** | **0.346** | **0.380** |
| oracle_gold | 1.000 | — |
| Published exact-match CUI | ~0.38 | — |
| Published TaggerOne CUI | ~0.45 | — |
| Published BioBERT STY | ~0.64 | — |

See [results/comparison_table.md](results/comparison_table.md).

## Reproduce

```bash
python scripts/download_medmentions.py
python scripts/convert_medmentions.py
python scripts/convert_medmentions.py --pmids data/medmentions/corpus_pubtator_pmids_test.txt --out data/medmentions/docs_test.jsonl
python scripts/run_medmentions_benchmark.py --limit 50
```

Entity config: [`configs/medmentions_st21pv_entities.yaml`](../../configs/medmentions_st21pv_entities.yaml)
