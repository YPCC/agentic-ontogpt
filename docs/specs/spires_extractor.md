# SPIRESExtractionAgent

## Goal
Run OntoGPT SPIRES extraction on clinical text using a validated template and return grounded structured output.

## Inputs
- Validated LinkML template YAML
- Clinical free text

## Outputs
- `extracted_object` (schema-conformant structure)
- `named_entities` with CURIEs when grounding succeeds
- Mode: `real_ontogpt` | `simulation`

## Tools
| Tool | Purpose |
|------|---------|
| `run_spires_extraction` | Real SPIRESEngine or simulation fallback |

## Success criteria
- Returns structured data for the entity types present in the text
- Clearly labels simulation vs real engine
