# Architecture

```
                  User / Notebook / adk run
                             |
                  OntoGPT_Full_Pipeline (SequentialAgent)
         +-------------------+-------------------+
         |                   |                   |
  OntologySelector    TemplateRepairLoop   SPIRESExtraction
                      (LoopAgent max 3)
```

Specs under `docs/specs/` define the contract.
Tools under `tools/` are pure functions shared by all agents.
