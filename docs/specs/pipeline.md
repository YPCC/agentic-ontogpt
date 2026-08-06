# OntoGPT_Full_Pipeline

## Goal
Orchestrate ontology selection -> SPIRES template generation (with repair) -> grounded extraction from clinical text.

## Inputs
- List of clinical entity types (and optional preferred ontology per type)
- Free-text clinical document / abstract

## Outputs
- Ontology mapping (EntityType -> BioPortal acronym)
- Validated LinkML / SPIRES template (YAML)
- Structured ExtractionResult (entities + relationships + grounded CURIEs)
- Mode indicator (`real_ontogpt` | `simulation`)

## Sub-agents
1. `OntologySelectorAgent`
2. `TemplateRepairLoop` (`LoopAgent`: TemplateGenerator <-> Validator, max 3)
3. `SPIRESExtractionAgent`

## Success criteria
- Template validates against LinkML metamodel and OntoGPT conventions
- Extraction returns at least the requested entity types when present in text
- Grounding attempted via `bioportal:` / OAK annotators when real OntoGPT is available

## Non-goals
- Full knowledge-graph materialization / SPARQL endpoint
- Multi-document batch processing (future agent)

## Failure modes & recovery
| Failure | Recovery |
|---------|----------|
| BioPortal unreachable | Fall back to user-supplied ontology preferences |
| Template invalid after 3 loops | Surface validation errors; do not call extractor |
| OntoGPT not installed | Use simulation mode and clearly label output |
