# MedMentions ST21pv — Smoke benchmark results

**Docs:** 50 (head of official test split, 879 total)  
**Gold mentions in sample:** 1,485

## Micro scores

| Mode | Precision | Recall | F1 | TP/FP/FN |
|------|-----------|--------|-----|----------|
| oracle_gold (`--simulate-oracle`) | 1.000 | 1.000 | **1.000** | 1485/0/0 |
| no-LLM / empty extract | 0.000 | 0.000 | **0.000** | 0/0/1485 |

## vs published baselines (indicative; metric definitions differ)

| System | Reported F1 | Metric notes |
|--------|-------------|--------------|
| TaggerOne (CUI linking) | ~0.45 | Official ST21pv concept linking |
| BioBERT (STY) | ~0.64 | Semantic type |
| README SOTA note (mention-level) | ~0.57 | Recognition + linking lower bound |
| **agentic-ontogpt oracle smoke** | **1.000** | text+ST; plumbing only |
| **agentic-ontogpt no-LLM** | **0.000** | OntoGPT not installed |

> Install `ontogpt` + API key and re-run without `--simulate-oracle` for real SPIRES scores on these 50 abstracts.

Dataset: Mohan & Li, AKBC 2019 — https://github.com/chanzuckerberg/MedMentions
