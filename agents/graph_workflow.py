"""Optional ADK graph entry built from ``agents.registry`` (not pipeline.agent).

* Does **not** change ``agents/pipeline/agent.py``.
* Prefer ADK 2.0 Workflow(edges=...) when available; else Sequential+Loop from factories.
* Topology: ontology → (generator↔validator)×N → extract
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from agents.registry import AGENT_META, build, list_agents


def adk_available() -> bool:
    try:
        import google.adk  # noqa: F401
        return True
    except ImportError:
        return False


def workflow_api_available() -> bool:
    try:
        from google.adk import Workflow  # type: ignore  # noqa: F401
        return True
    except ImportError:
        try:
            from google.adk.agents import Workflow  # type: ignore  # noqa: F401
            return True
        except ImportError:
            return False


def build_control_plane_from_registry(
    model: Optional[str] = None,
    *,
    max_repair_iterations: int = 3,
    prefer_workflow_api: bool = True,
) -> Tuple[Any, Dict[str, Any]]:
    info: Dict[str, Any] = {
        "source": "agents.graph_workflow",
        "pipeline_module_touched": False,
        "agents": list_agents(),
        "agent_meta": {k: AGENT_META[k] for k in list_agents() if k in AGENT_META},
    }

    if not adk_available():
        info["mode"] = "unavailable"
        info["note"] = (
            "google-adk not installed. Use agents.modular_compose or "
            "tools.pipeline_runner for headless runs; install google-adk for graphs."
        )
        return None, info

    ontology = build("ontology_selector", model=model)
    generator = build("template_generator", model=model)
    validator = build("validator", model=model)
    extractor = build("spires_extractor", model=model)

    if prefer_workflow_api and workflow_api_available():
        root, mode_note = _build_workflow_v2(
            ontology, generator, validator, extractor, max_repair_iterations
        )
        info["mode"] = "workflow_v2"
        info["note"] = mode_note
        return root, info

    root, mode_note = _build_sequential_loop(
        ontology, generator, validator, extractor, max_repair_iterations
    )
    info["mode"] = "sequential_loop"
    info["note"] = mode_note
    return root, info


def _build_workflow_v2(ontology, generator, validator, extractor, max_repair_iterations):
    try:
        from google.adk import Workflow
    except ImportError:
        from google.adk.agents import Workflow  # type: ignore

    root = Workflow(
        name="ontogpt_control_plane_graph",
        edges=[("START", ontology, generator, validator, extractor)],
    )
    note = (
        "ADK Workflow API: linear edge ontology→generator→validator→extractor. "
        f"Bounded multi-iter repair (max={max_repair_iterations}) remains on "
        "agents.pipeline LoopAgent until cycle/dynamic nodes are used."
    )
    return root, note


def _build_sequential_loop(ontology, generator, validator, extractor, max_repair_iterations):
    from google.adk.agents import LoopAgent, SequentialAgent

    try:
        from agents.pipeline.exit_agent import build_repair_loop, ADK_AVAILABLE
    except ImportError:
        build_repair_loop = None
        ADK_AVAILABLE = False

    if build_repair_loop is not None and ADK_AVAILABLE:
        repair = build_repair_loop(generator, validator, max_iterations=max_repair_iterations)
    else:
        repair = LoopAgent(
            name="TemplateRepairLoop",
            sub_agents=[generator, validator],
            max_iterations=max_repair_iterations,
        )

    root = SequentialAgent(
        name="OntoGPT_Registry_Pipeline",
        sub_agents=[ontology, repair, extractor],
        description=(
            "Registry-built control plane (factories only). "
            "Not agents.pipeline.agent.root_agent — parallel showcase path."
        ),
    )
    note = (
        "Assembled SequentialAgent+LoopAgent from registry build_* factories. "
        "Same topology idea as pipeline, different construction path."
    )
    return root, note


def get_root_agent(model: Optional[str] = None):
    return build_control_plane_from_registry(model=model)
