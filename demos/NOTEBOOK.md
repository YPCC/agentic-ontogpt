# Demo notebook

The full interactive demo notebook `OntoGPT_LinkML_Agent_Prototype.ipynb` lives in this `demos/` folder in the project workspace.

It walks through:
1. BioPortal ontology selection
2. LLM-driven LinkML / SPIRES template generation (few-shot)
3. Validation + repair loop
4. SPIRES extraction on a melanoma / BRAF / vemurafenib sample

Run locally with:

```bash
pip install -e ".[dev]"
cp .env.example .env   # set GOOGLE_API_KEY + BIOPORTAL_API_KEY
jupyter notebook demos/OntoGPT_LinkML_Agent_Prototype.ipynb
```

Or exercise the same pipeline without the notebook:

```bash
adk run agents/pipeline
```
