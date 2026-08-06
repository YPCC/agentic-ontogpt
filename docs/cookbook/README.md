# ADK Development Cookbook for agentic-ontogpt

Practical patterns for extending this repository with Google Agent Development Kit (ADK).

## 1. Mental model

```
docs/specs/<agent>.md     <- what the agent must do (contract)
tools/                    <- pure Python functions (no LLM)
agents/<agent>/agent.py   <- LlmAgent / SequentialAgent / LoopAgent wiring
tests/                    <- unit + light integration
.github/workflows/        <- CI that runs tests + optional adk eval
```

## 2. Adding a new agent (checklist)

1. **Write the spec** in `docs/specs/<name>.md`.
2. **Implement tools** (if needed) under `tools/`.
3. **Create the ADK package** under `agents/<name>/`.
4. **Register** the agent in `agents/pipeline/agent.py`.
5. **Add tests** under `tests/`.
6. **Document** the agent in the root README / cookbook.

## 3. ADK agent skeleton

```python
from google.adk.agents import LlmAgent
from textwrap import dedent

def my_tool(arg: str) -> dict:
    """Docstring becomes the tool description for the LLM."""
    return {"status": "success", "result": arg}

root_agent = LlmAgent(
    name="MyAgent",
    model="gemini-2.0-flash",
    description="One-line purpose",
    instruction=dedent("""..."""),
    tools=[my_tool],
    output_key="my_output",
)
```

## 4. Composition patterns used here

| Pattern | ADK construct | Where |
|---------|---------------|-------|
| Linear pipeline | `SequentialAgent` | `agents/pipeline` |
| Generate -> validate -> repair | `LoopAgent` | TemplateRepairLoop |
| Tool calling | plain Python functions in `tools=` | all agents |
| State hand-off | `output_key` | ontology_map, generated_schema_yaml, ... |

## 5. Running locally

```bash
adk run agents/pipeline
adk web agents/
jupyter notebook demos/OntoGPT_LinkML_Agent_Prototype.ipynb
```

## 6. Evolving to ADK 2.0 graph Workflows

Replace `SequentialAgent` + `LoopAgent` with an explicit `Workflow` graph that uses route edges for the repair cycle. Keep the same tools and LlmAgent nodes. See ADK docs: https://google.github.io/adk-docs/2.0/
