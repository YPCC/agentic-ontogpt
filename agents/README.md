# Agents

## Design

| Path | Status |
|------|--------|
| `pipeline/agent.py` | **Canonical** ADK SequentialAgent composition (do not break) |
| `pipeline/exit_agent.py` | Validation early-exit for repair loop |
| `ontology_selector/` | Modular factory `build_ontology_selector()` |
| `template_generator/` | Modular factory `build_template_generator()` |
| `validator/` | Modular factory `build_validator()` |
| `spires_extractor/` | Modular factory `build_spires_extractor()` |

Pipeline still owns the live graph. Modular packages mirror agent definitions for
gradual extraction and unit testing without changing runtime behavior.

```text
agents/pipeline/agent.py  ──►  OntologySelector → RepairLoop → SPIRESExtraction
                                      ▲                ▲              ▲
                                      │                │              │
              agents/ontology_selector/agent.py        │              │
              agents/template_generator + validator ───┘              │
              agents/spires_extractor/agent.py ───────────────────────┘
```

## Usage (modular, optional)

```python
from agents.ontology_selector import build_ontology_selector
from agents.template_generator import build_template_generator
from agents.validator import build_validator
from agents.spires_extractor import build_spires_extractor

# Compose your own SequentialAgent / LoopAgent when ready
```

For the full product path, keep using:

```bash
adk run agents/pipeline
```
