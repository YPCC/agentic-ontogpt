# Agent & Pipeline Specifications

Specifications are the **source of truth**. Code under `agents/` implements these specs.

| Spec | Agent / component | Status |
|------|-------------------|--------|
| [ontology_selector.md](ontology_selector.md) | OntologySelectorAgent | v0.1 |
| [template_generator.md](template_generator.md) | TemplateGeneratorAgent | v0.1 |
| [validator.md](validator.md) | ValidatorAgent | v0.1 |
| [spires_extractor.md](spires_extractor.md) | SPIRESExtractionAgent | v0.1 |
| [pipeline.md](pipeline.md) | OntoGPT_Full_Pipeline | v0.1 |

## Spec template (use for new agents)

```markdown
# <AgentName>

## Goal
One-sentence purpose.

## Inputs
- ...

## Outputs
- ...

## Tools
| Tool | Purpose |
|------|---------|

## Success criteria
- ...

## Non-goals
- ...

## Failure modes & recovery
- ...
```
