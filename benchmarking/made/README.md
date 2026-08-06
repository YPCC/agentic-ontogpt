# Benchmarking — MADE 1.0

Results and provenance for the **agentic-ontogpt** SPIRES pipeline on the MADE 1.0 schema
(Medication and Adverse Drug Events from EHR notes).

## Layout

```
benchmarking/made/
├── README.md
└── results/
    ├── provenance.json          # when/how this run was produced
    ├── made_eval_results.json   # full metrics + predictions + gold
    └── comparison_table.md      # vs public MADE challenge baselines
```

## Latest run

- **Run ID:** `made-pilot-20260806T234550Z`
- **UTC:** 2026-08-06T23:45:50Z
- **Mode:** `simulation`
- **NER micro-F1:** 1.0
- **RI micro-F1:** 1.0

See [results/comparison_table.md](results/comparison_table.md) for the full table and caveats.

## Reproduce

```bash
python scripts/run_made_eval.py
# results land in demos/made/ and are copied to benchmarking/made/results/
```

## Related code

| Artifact | Path |
|----------|------|
| LinkML / SPIRES template | [`templates/made_1_0.yaml`](../../templates/made_1_0.yaml) |
| Eval runner | [`scripts/run_made_eval.py`](../../scripts/run_made_eval.py) |
| Demo notebook | [`demos/made/`](../../demos/made/) |
