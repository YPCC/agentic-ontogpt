# Benchmarking — MedMentions ST21pv

Smoke / pilot results for **agentic-ontogpt** on [MedMentions](https://github.com/chanzuckerberg/MedMentions) ST21pv.

## Layout

```
benchmarking/medmentions/
├── README.md
└── results/
    ├── provenance.json
    ├── medmentions_eval_results_summary.json
    └── comparison_table.md
```

## Latest smoke run (50 test abstracts)

| Mode | Micro F1 | Notes |
|------|----------|-------|
| oracle_gold | 1.000 | Pipeline I/O check (1485 gold mentions) |
| no-LLM | 0.000 | OntoGPT not installed in CI sandbox |

## Reproduce

```bash
python scripts/download_medmentions.py
python scripts/convert_medmentions.py
python scripts/run_medmentions_benchmark.py --limit 50
```

## Entity x ontology config

[`configs/medmentions_st21pv_entities.yaml`](../../configs/medmentions_st21pv_entities.yaml)
