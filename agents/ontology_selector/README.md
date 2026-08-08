# OntologySelector

**Role:** Map clinical entity types → BioPortal ontology acronyms, then apply deterministic policy.

| Item | Location |
|------|----------|
| Factory | `build_ontology_selector()` in `agent.py` |
| Tools | BioPortal recommend/search, `apply_ontology_policy` |
| Output key | `ontology_map` |
| Pipeline wiring | Still composed in `agents/pipeline/agent.py` |

```python
from agents.ontology_selector import build_ontology_selector
agent = build_ontology_selector()  # requires google-adk
```
