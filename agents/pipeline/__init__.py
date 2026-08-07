"""ADK pipeline package. Lazy-import root_agent when google-adk is available."""

__all__ = ["root_agent"]

def __getattr__(name: str):
    if name == "root_agent":
        from .agent import root_agent
        return root_agent
    raise AttributeError(name)
