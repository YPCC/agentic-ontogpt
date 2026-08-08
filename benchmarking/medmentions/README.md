# Benchmarking — MedMentions ST21pv (Track 2)

Accessible **CC0** corpus: [MedMentions](https://github.com/chanzuckerberg/MedMentions) (Mohan & Li, AKBC 2019).

## Metrics

| Metric | Meaning |
|--------|---------|
| Schema gate valid | Template passes `tools.schema_gate` |
| Outcome distribution | REAL_SUCCESS / SIMULATION_REQUESTED / REAL_EXTRACTION_FAILED |
| Failure visibility | Explicit outcome per doc (no silent success) |
| Micro P/R/F1 | Normalized text + primary semantic type (pilot; not official CUI linking) |

## Commands

```bash
python scripts/download_medmentions.py
python scripts/convert_medmentions.py \
  --pmids data/medmentions/corpus_pubtator_pmids_test.txt \
  --out data/medmentions/docs_test.jsonl

AGENTIC_ONTOGPT_MODE=simulation python scripts/run_medmentions_track2.py --limit 50
AGENTIC_ONTOGPT_MODE=real python scripts/run_medmentions_track2.py --limit 20
python scripts/run_medmentions_track2.py --limit 20 --oracle
```

Template: `templates/medmentions_st21pv.yaml`  
Entity map: `configs/medmentions_st21pv_entities.yaml`
