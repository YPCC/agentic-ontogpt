# MADE 1.0 — Agentic OntoGPT demo

LinkML / SPIRES template and notebook for the **MADE 1.0** (Medication and Adverse Drug Events) shared task.

## Files

| Path | Description |
|------|-------------|
| `MADE_1_0_OntoGPT_Demo.ipynb` | Two-phase notebook (inventory + extract/eval) |
| `../../templates/made_1_0.yaml` | OntoGPT-compliant LinkML schema |

## Entities (9)

Drug, Dosage, Route, Duration, Frequency, Indication, ADE, Severity, SSLIF

## Relations (7)

Drug–Dosage, Drug–Route, Drug–Frequency, Drug–Duration, Indication–Drug (Reason), ADE–Drug (Adverse), Severity–SSD

## Run

```bash
cd demos/made
jupyter notebook MADE_1_0_OntoGPT_Demo.ipynb
```

Data access: http://bio-nlp.org/dataset/made1  
Paper: https://pmc.ncbi.nlm.nih.gov/articles/PMC6860017/
