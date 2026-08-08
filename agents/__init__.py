"""Agent packages for agentic-ontogpt.

Canonical ADK wiring lives in ``agents.pipeline.agent`` (unchanged).
Per-role modules under this package are modular exports for future
composition; they do not replace the pipeline root agent yet.
"""

__all__ = [
    "ontology_selector",
    "template_generator",
    "validator",
    "spires_extractor",
    "pipeline",
]
