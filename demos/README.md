# Demos

| Demo | Description |
|------|-------------|
| `OntoGPT_LinkML_Agent_Prototype.ipynb` | Early ADK prototype |
| `failure_modes_repair_loop.ipynb` | P0 repair / gate failure modes |
| `made/` | MADE 1.0 notebook |
| **`run_modular_agents_demo.py`** | Modular packages only (not pipeline ADK graph) |

## Modular agents demo (not pipeline)

```bash
export AGENTIC_ONTOGPT_MODE=simulation
python demos/run_modular_agents_demo.py --compare --made-template
```

Uses `agents.modular_compose.run_modular_pipeline` — packages under
`agents/ontology_selector`, `validator`, `spires_extractor` — and checks parity
against `tools.pipeline_runner`.
