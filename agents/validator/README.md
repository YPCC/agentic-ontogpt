# Validator

**Role:** Multi-stage LinkML / OntoGPT validation ladder.

| Item | Location |
|------|----------|
| Factory | `build_validator()` |
| Tool | `tools.linkml_tools.validate_linkml_schema` |
| Output key | `validation_result` |

Hard-fails OntoGPT convention errors. Reports `validation_completeness`.
