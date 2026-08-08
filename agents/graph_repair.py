"""Multi-iteration schema repair on an ADK 2.0-style graph — **not** pipeline.agent.

Two showcase patterns (both use ``agents.registry.build`` only):

1. **Dynamic orchestrator**: Python loop + ``ctx.run_node(generator/validator)``
   until valid or ``max_iterations``.
2. **Static Workflow + gate**: REFINE → generator, DONE → extractor.

``agents/pipeline/agent.py`` is never used for construction.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional, Tuple

from agents.registry import build, list_agents


def adk_available() -> bool:
    try:
        import google.adk  # noqa: F401
        return True
    except ImportError:
        return False


def _try_import_workflow():
    try:
        from google.adk import Workflow  # type: ignore
        return Workflow
    except ImportError:
        try:
            from google.adk.agents import Workflow  # type: ignore
            return Workflow
        except ImportError:
            return None


def _try_import_event():
    for path in ("google.adk.events.Event", "google.adk.Event", "google.adk.agents.Event"):
        mod, _, name = path.rpartition(".")
        try:
            m = __import__(mod, fromlist=[name])
            return getattr(m, name)
        except (ImportError, AttributeError):
            continue
    return None


def _try_import_node_decorator():
    for path in (
        "google.adk.workflows.node",
        "google.adk.workflow.node",
        "google.adk.nodes.node",
        "google.adk.node",
    ):
        try:
            parent, _, attr = path.rpartition(".")
            m = __import__(parent, fromlist=[attr])
            n = getattr(m, attr, None)
            if n is not None:
                return n
        except (ImportError, AttributeError):
            continue
    try:
        from google.adk import node  # type: ignore
        return node
    except ImportError:
        return None


def make_repair_gate(max_iterations: int = 3):
    """Deterministic gate: REFINE vs DONE from validation payload + iteration."""

    def repair_gate(node_input: Any = None) -> Dict[str, Any]:
        if isinstance(node_input, dict):
            data = node_input
        elif isinstance(node_input, str):
            try:
                data = json.loads(node_input) if node_input.strip().startswith("{") else {}
            except Exception:
                data = {"raw": node_input}
        else:
            data = {}

        valid = bool(data.get("valid") is True or str(data.get("valid", "")).lower() == "true")
        iteration = int(data.get("iteration") or data.get("repair_iterations") or 0)

        if valid:
            route, reason = "DONE", "schema_valid"
        elif iteration >= max_iterations:
            route, reason = "DONE", "max_iterations_reached"
        else:
            route, reason = "REFINE", "schema_invalid"

        payload = {
            "route": route,
            "reason": reason,
            "iteration": iteration,
            "max_iterations": max_iterations,
            "valid": valid,
        }
        Event = _try_import_event()
        if Event is not None:
            try:
                return Event(route=route, message=json.dumps(payload))
            except TypeError:
                try:
                    return Event(route=[route])
                except TypeError:
                    pass
        return payload

    repair_gate.__name__ = "repair_gate"
    return repair_gate


def build_dynamic_repair_orchestrator(
    model: Optional[str] = None, *, max_iterations: int = 3
) -> Tuple[Any, Dict[str, Any]]:
    info: Dict[str, Any] = {
        "pattern": "dynamic_repair",
        "pipeline_module_touched": False,
        "max_iterations": max_iterations,
        "agents": ["template_generator", "validator"],
    }
    if not adk_available():
        info["mode"] = "unavailable"
        info["note"] = "Install google-adk to materialize dynamic repair orchestrator."
        return None, info

    generator = build("template_generator", model=model)
    validator = build("validator", model=model)
    node_deco = _try_import_node_decorator()

    async def repair_orchestrator(ctx: Any, node_input: Any = None) -> Any:
        last_validation = None
        schema_yaml = node_input
        i = 0
        for i in range(1, max_iterations + 1):
            schema_yaml = await ctx.run_node(generator, node_input=schema_yaml)
            last_validation = await ctx.run_node(validator, node_input=schema_yaml)
            text = str(last_validation or "")
            if isinstance(last_validation, dict) and last_validation.get("valid") is True:
                break
            if "valid" in text.lower() and "true" in text.lower():
                if "false" not in text.lower().split("valid")[-1][:24]:
                    break
        return {"schema": schema_yaml, "validation": last_validation, "iterations": i}

    if node_deco is not None:
        try:
            orchestrator = node_deco(rerun_on_resume=True)(repair_orchestrator)
        except TypeError:
            orchestrator = node_deco(repair_orchestrator)
        info["mode"] = "dynamic_node"
        info["note"] = f"Dynamic repair: up to {max_iterations} generate→validate cycles."
        return orchestrator, info

    info["mode"] = "callable_only"
    info["note"] = "@node decorator not found; coroutine defined for when dynamic APIs exist."
    info["orchestrator_fn"] = repair_orchestrator
    return repair_orchestrator, info


def build_workflow_with_repair_gate(
    model: Optional[str] = None, *, max_iterations: int = 3
) -> Tuple[Any, Dict[str, Any]]:
    info: Dict[str, Any] = {
        "pattern": "workflow_repair_gate",
        "pipeline_module_touched": False,
        "max_iterations": max_iterations,
        "agents": list_agents(),
    }
    Workflow = _try_import_workflow()
    if Workflow is None or not adk_available():
        info["mode"] = "unavailable"
        info["note"] = "Workflow API / google-adk missing; gate factory still usable."
        info["gate"] = make_repair_gate(max_iterations)
        return None, info

    ontology = build("ontology_selector", model=model)
    generator = build("template_generator", model=model)
    validator = build("validator", model=model)
    extractor = build("spires_extractor", model=model)
    gate = make_repair_gate(max_iterations)

    try:
        root = Workflow(
            name="ontogpt_repair_graph",
            edges=[
                ("START", ontology, generator, validator, gate),
                (gate, {"REFINE": generator, "DONE": extractor}),
            ],
        )
        info["mode"] = "workflow_with_backedge"
        info["note"] = (
            f"Workflow gate REFINE→generator (max_iterations={max_iterations}). "
            "Prefer dynamic orchestrator if cycles are unreliable in your ADK build."
        )
        return root, info
    except Exception as e:
        root = Workflow(
            name="ontogpt_repair_graph_linear",
            edges=[("START", ontology, generator, validator, gate, extractor)],
        )
        info["mode"] = "workflow_linear_fallback"
        info["note"] = f"Back-edge failed ({e!r}); linear path with gate."
        return root, info


def describe_patterns() -> Dict[str, str]:
    return {
        "dynamic_repair": (
            "ADK dynamic workflow: while/for + ctx.run_node(generator/validator) "
            "until valid or max_iterations. Best multi-iter semantics."
        ),
        "workflow_repair_gate": (
            "Static Workflow: generator→validator→gate; REFINE routes back to "
            "generator, DONE to extractor. Needs cycle support in graph engine."
        ),
        "pipeline_loopagent": (
            "Unchanged product path: agents.pipeline LoopAgent(max_iterations=N). "
            "Not modified by this module."
        ),
    }
