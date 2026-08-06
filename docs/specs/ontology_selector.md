# OntologySelectorAgent

## Goal
Map clinical entity types (or concrete terms) to the most appropriate BioPortal ontology acronym.

## Inputs
- Comma-separated entity types or terms
- Optional user-preferred ontology per entity

## Outputs
- Mapping `EntityType -> OntologyAcronym` with short justification

## Tools
| Tool | Purpose |
|------|---------|
| `bioportal_recommend_ontology` | Rank ontologies for a keyword list |
| `bioportal_search_term` | Lookup a term in one or more ontologies |

## Success criteria
- Prefer high-quality biomedical ontologies (MONDO, HP, GO, CHEBI, HGNC, NCIT, DRON, ...)
- Respect user preferences when supplied

## Non-goals
- Full ontology alignment / mapping between ontologies
