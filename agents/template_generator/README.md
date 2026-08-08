# TemplateGenerator

**Role:** Generate or error-directed repair of OntoGPT-compliant LinkML/SPIRES YAML.

| Item | Location |
|------|----------|
| Factory | `build_template_generator()` |
| Output key | `generated_schema_yaml` |
| Pipeline wiring | `agents/pipeline/agent.py` (unchanged) |

Uses `validation_result` from session state for repair.
