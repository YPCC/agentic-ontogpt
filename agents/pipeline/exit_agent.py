"""Native ADK early-exit agent for the template repair loop (P3).

LoopAgent stops on max_iterations OR EventActions(escalate=True).
ValidationExitAgent escalates when validation_result.valid is true.
"""
from __future__ import annotations
from textwrap import dedent
from typing import Any, AsyncGenerator, Optional

def _parse_valid_from_state(state: Any) -> Optional[bool]:
    if state is None: return None
    raw = state.get("validation_result") if hasattr(state, "get") or isinstance(state, dict) else None
    if raw is None: return None
    if isinstance(raw, dict):
        if "valid" in raw: return bool(raw.get("valid"))
        if "status" in raw: return raw.get("status") == "success" and raw.get("valid", True)
    if isinstance(raw, str):
        low = raw.lower()
        if "invalid" in low or "valid=false" in low or '"valid": false' in low: return False
        if low.strip().startswith("valid") or '"valid": true' in low: return True
    return None

try:
    from google.adk.agents import BaseAgent, LlmAgent, LoopAgent
    from google.adk.events import Event, EventActions

    class ValidationExitAgent(BaseAgent):
        name: str = "ValidationExitAgent"
        description: str = "Exits repair loop when validation_result.valid is true."

        async def _run_async_impl(self, ctx) -> AsyncGenerator[Event, None]:
            state = getattr(ctx, "session", None)
            state = getattr(state, "state", None) if state is not None else None
            if state is None:
                state = getattr(ctx, "state", None)
            valid = _parse_valid_from_state(state)
            if valid is True:
                yield Event(author=self.name,
                    content="VALIDATION_PASSED — escalating to exit TemplateRepairLoop",
                    actions=EventActions(escalate=True))
            else:
                yield Event(author=self.name,
                    content=f"VALIDATION_NOT_PASSED — continue (valid={valid})",
                    actions=EventActions(escalate=False))

    def build_repair_loop(template_generator, validator, *, max_iterations=3):
        return LoopAgent(name="TemplateRepairLoop",
            sub_agents=[template_generator, validator, ValidationExitAgent(name="ValidationExitAgent")],
            max_iterations=max_iterations)

    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False
    ValidationExitAgent = None

    def build_repair_loop(template_generator, validator, *, max_iterations=3):
        return {"name": "TemplateRepairLoop", "max_iterations": max_iterations,
                "sub_agents": [getattr(template_generator, "name", "TemplateGenerator"),
                               getattr(validator, "name", "Validator"), "ValidationExitAgent"],
                "early_exit": "ValidationExitAgent escalates when validation_result.valid",
                "adk_available": False,
                "note": "Install google-adk for native LoopAgent; use tools.repair offline."}
