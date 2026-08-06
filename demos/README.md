# Demos

## OntoGPT_LinkML_Agent_Prototype.ipynb

End-to-end Jupyter demonstration of the agentic OntoGPT / SPIRES pipeline:

1. BioPortal ontology selection
2. LLM-driven LinkML template generation (few-shot)
3. Validation + repair loop
4. SPIRES extraction (real OntoGPT or simulation)

### Run

```bash
# from repo root
pip install -e ".[dev]"
cp .env.example .env   # add GOOGLE_API_KEY + BIOPORTAL_API_KEY
jupyter notebook demos/OntoGPT_LinkML_Agent_Prototype.ipynb
```

Open the notebook and run the cells in order. The final demo cell runs the melanoma / BRAF / vemurafenib sample end-to-end.
