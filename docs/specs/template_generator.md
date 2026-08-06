# TemplateGeneratorAgent

## Goal
Produce a complete OntoGPT-compliant LinkML / SPIRES schema YAML for the requested entities and chosen ontologies.

## Inputs
- Entity types + ontology mapping from the selector
- Optional relationship requirements

## Outputs
- Full LinkML YAML (imports `linkml:types` + `core`, NamedEntity classes, optional CompoundExpression relations)

## Tools
| Tool | Purpose |
|------|---------|
| `persist_template` | Save YAML to disk for downstream agents |

## Success criteria
- YAML follows OntoGPT conventions (see few-shot examples in the demo notebook)
- Ready for `linkml validate` and SPIRESEngine

## Non-goals
- Generating Pydantic classes (can be added later via gen-pydantic)
