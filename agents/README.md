# Agents

## Design

| Path | Status |
|------|--------|
| `pipeline/agent.py` | **Canonical** ADK SequentialAgent composition (do not break) |
| `pipeline/exit_agent.py` | Validation early-exit for repair loop |
| `ontology_selector/` | Modular factory `build_ontology_selector()` + `get_tools()` |
| `template_generator/` | Modular factory `build_template_generator()` + `get_tools()` |
| `validator/` | Modular factory `build_validator()` + `get_tools()` |
| `spires_extractor/` | Modular factory `build_spires_extractor()` + `get_tools()` |
| `modular_compose.py` | Headless composition using modular `get_tools()` (not ADK graph) |

Pipeline still owns the live ADK graph. Modular packages mirror agent definitions for gradual extraction and unit testing without changing runtime behavior of `pipeline/agent.py`.

## Usage (modular, optional)

```python
from agents.ontology_selector import build_ontology_selector
from agents.template_generator import build_template_generator
from agents.validator import build_validator
from agents.spires_extractor import build_spires_extractor
# Compose your own SequentialAgent / LoopAgent when ready (requires google-adk)
```

For the full product path, keep using:

```bash
adk run agents/pipeline
```

## Headless modular composition

Without ADK, use the same tool surfaces from each package:

```bash
export AGENTIC_ONTOGPT_MODE=simulation
python demos/run_modular_agents_demo.py --compare --made-template
```

```python
from agents.modular_compose import run_modular_pipeline
state = run_modular_pipeline(
    "Patient developed neutropenia after carboplatin.",
    ["Medication", "AdverseEvent"],
    ontology_preferences={"Medication": "RXNORM", "AdverseEvent": "MEDDRA"},
    execution_mode="simulation",
)
assert state.component_metrics["composer"] == "modular"
```

Parity with `tools.pipeline_runner.run_pipeline` is covered by `tests/test_modular_agents.py`.
The ADK graph in `pipeline/agent.py` is **not** modified by this path.
