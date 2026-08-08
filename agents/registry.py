"""Agent factory registry — additive; does not modify ``agents.pipeline.agent``.

Register a new agent with one line after implementing ``build_*`` in its package.
Consumers (graph scaffold, demos, future ADK Workflow) resolve nodes by name.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional


def _load_builders() -> Dict[str, Callable[..., Any]]:
    from agents.ontology_selector import build_ontology_selector
    from agents.template_generator import build_template_generator
    from agents.validator import build_validator
    from agents.spires_extractor import build_spires_extractor

    return {
        "ontology_selector": build_ontology_selector,
        "template_generator": build_template_generator,
        "validator": build_validator,
        "spires_extractor": build_spires_extractor,
    }


KNOWN_AGENTS: List[str] = [
    "ontology_selector",
    "template_generator",
    "validator",
    "spires_extractor",
]

AGENT_META: Dict[str, Dict[str, str]] = {
    "ontology_selector": {
        "kind": "llm",
        "output_key": "ontology_map",
        "role": "Map entity types → BioPortal ontologies + policy",
    },
    "template_generator": {
        "kind": "llm",
        "output_key": "generated_schema_yaml",
        "role": "Generate / error-directed repair of LinkML SPIRES YAML",
    },
    "validator": {
        "kind": "llm",
        "output_key": "validation_result",
        "role": "Multi-stage LinkML / OntoGPT validation ladder",
    },
    "spires_extractor": {
        "kind": "llm",
        "output_key": "extraction_result",
        "role": "Gated SPIRES extraction with explicit outcomes",
    },
}


def list_agents() -> List[str]:
    return list(KNOWN_AGENTS)


def build(name: str, model: Optional[str] = None, **kwargs: Any) -> Any:
    """Instantiate a registered agent by name. Requires google-adk for LLM factories."""
    builders = _load_builders()
    if name not in builders:
        raise KeyError(
            f"Unknown agent {name!r}. Known: {sorted(builders)}. "
            "Add build_* to the package and register it in _load_builders()."
        )
    if model is not None:
        return builders[name](model=model, **kwargs)
    return builders[name](**kwargs)


def build_many(names: List[str], model: Optional[str] = None) -> Dict[str, Any]:
    return {n: build(n, model=model) for n in names}
