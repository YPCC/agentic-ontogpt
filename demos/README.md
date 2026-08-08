# Demos

## Parallel paths (same control plane)

| Path | Demo | Notes |
|------|------|-------|
| **A — product** | `adk run agents/pipeline` | Sequential/Loop in `agents/pipeline/agent.py` |
| **B — ADK 2.0 graph** | `run_adk_graph_demo.py`, `run_adk_repair_graph_demo.py` | Registry + Workflow / repair gate |
| **C — headless** | `run_modular_agents_demo.py` | No ADK; parity with `pipeline_runner` |

```bash
export AGENTIC_ONTOGPT_MODE=simulation
python demos/run_modular_agents_demo.py --compare --made-template
python demos/run_adk_graph_demo.py
python demos/run_adk_repair_graph_demo.py --max-iterations 3
```

## Notebooks

| Demo | Description |
|------|-------------|
| `OntoGPT_LinkML_Agent_Prototype.ipynb` | Early ADK prototype |
| `failure_modes_repair_loop.ipynb` | P0 repair / gate failure modes |
| `made/` | MADE 1.0 notebook |

## Modular agents demo (Path C)

```bash
export AGENTIC_ONTOGPT_MODE=simulation
python demos/run_modular_agents_demo.py --compare --made-template
```

Uses `agents.modular_compose.run_modular_pipeline` — packages under
`agents/ontology_selector`, `validator`, `spires_extractor` — and checks parity
against `tools.pipeline_runner`.

## ADK graph showcase (Path B, not pipeline)

```bash
python demos/run_adk_graph_demo.py
python demos/run_adk_repair_graph_demo.py --max-iterations 3
```

Assembles a root from `agents.registry` factories. Original workflow remains `adk run agents/pipeline`.
