# Benchmarking

Benchmark runs for **agentic-ontogpt** pipelines against public shared-task baselines.

| Benchmark | Folder | Description |
|-----------|--------|-------------|
| MADE 1.0 | [`made/`](made/) | Medication & Adverse Drug Events (9 NER + 7 RI types) |
| MedMentions ST21pv | [`medmentions/`](medmentions/) | UMLS semantic-type NER on PubMed abstracts (smoke: 50 docs) |

Each benchmark folder includes a `results/` directory with metrics, comparison tables, and **provenance** (timestamp, template hash, extraction mode, baseline citations).
