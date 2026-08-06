# ValidatorAgent

## Goal
Validate a LinkML / SPIRES schema and surface actionable errors for the repair loop.

## Inputs
- Full schema YAML string

## Outputs
- `VALID` or `INVALID` + error messages

## Tools
| Tool | Purpose |
|------|---------|
| `validate_linkml_schema` | Metamodel + OntoGPT convention checks |

## Success criteria
- Clear pass/fail signal for the LoopAgent
