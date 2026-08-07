"""Run provenance manifests for agentic-ontogpt."""

from __future__ import annotations

import hashlib
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from .modes import get_adk_model, get_execution_mode, get_spires_model
from .pipeline_state import PipelineState


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_text(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def _git_commit(repo_root: Optional[Path] = None) -> str:
    root = repo_root or Path(__file__).resolve().parents[1]
    try:
        r = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                           capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            return r.stdout.strip()
    except Exception:
        pass
    return "unknown"


def _pkg_version(name: str) -> str:
    try:
        from importlib.metadata import version
        return version(name)
    except Exception:
        return "not-installed"


def build_run_manifest(
    state: Optional[PipelineState] = None,
    *,
    extra: Optional[Dict[str, Any]] = None,
    repo_root: Optional[Path] = None,
) -> Dict[str, Any]:
    mode = get_execution_mode(state.execution_mode if state else None).value
    schema_yaml = state.generated_schema_yaml if state else ""
    validation = (state.validation_report if state else {}) or {}
    extraction = (state.extraction_result if state else {}) or {}
    manifest: Dict[str, Any] = {
        "run_id": (state.run_id if state else None) or f"run-{_utc_now()}",
        "timestamp_utc": _utc_now(),
        "pipeline_version": (state.pipeline_version if state else "0.2.0"),
        "git_commit": _git_commit(repo_root),
        "execution_mode": mode,
        "models": {
            "adk_llm": (state.adk_model if state else None) or get_adk_model(),
            "spires_llm": (state.spires_model if state else None) or get_spires_model(),
        },
        "versions": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "ontogpt": _pkg_version("ontogpt"),
            "linkml": _pkg_version("linkml"),
            "google-adk": _pkg_version("google-adk"),
        },
        "source": {
            "text_sha256": _sha256_text(state.source_text if state else ""),
            "text_length": len(state.source_text) if state else 0,
            "entity_types": list(state.entity_types) if state else [],
        },
        "ontology": {
            "selected": dict(state.selected_ontologies) if state else {},
            "policy_report": dict(state.ontology_policy_report) if state else {},
        },
        "schema": {
            "version": state.schema_version if state else 0,
            "sha256": _sha256_text(schema_yaml) if schema_yaml else None,
            "repair_iterations": state.repair_iterations if state else 0,
            "repair_stopped_reason": state.repair_stopped_reason if state else "",
        },
        "validation": {
            "valid": validation.get("valid"),
            "errors": validation.get("errors") or [],
        },
        "extraction": {
            "outcome": extraction.get("outcome"),
            "status": extraction.get("status"),
            "blocked": state.extraction_blocked if state else False,
        },
        "reproducibility_note": (
            "Manifest captures execution context. LLM outputs may still vary."
        ),
        "env_flags": {
            "AGENTIC_ONTOGPT_MODE": os.environ.get("AGENTIC_ONTOGPT_MODE", "real"),
            "BIOPORTAL_API_KEY_set": bool(os.environ.get("BIOPORTAL_API_KEY")),
            "OPENAI_API_KEY_set": bool(os.environ.get("OPENAI_API_KEY")),
            "GOOGLE_API_KEY_set": bool(os.environ.get("GOOGLE_API_KEY")),
        },
    }
    if extra:
        manifest["extra"] = extra
    if state is not None:
        state.provenance_manifest = manifest
        state.touch()
    return manifest


def write_manifest(manifest: Dict[str, Any], path: str | Path) -> str:
    import json
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(manifest, indent=2))
    return str(p)
