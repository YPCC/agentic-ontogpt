"""LinkML schema validation and persistence helpers."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict

import yaml


def save_template_yaml(
    schema_yaml: str, schema_name: str = "clinical_extraction", out_dir: str = "/tmp/ontogpt_templates"
) -> Dict[str, Any]:
    """Persist a generated LinkML YAML to disk."""
    path = Path(out_dir)
    path.mkdir(parents=True, exist_ok=True)
    target = path / f"{schema_name}.yaml"
    target.write_text(schema_yaml)
    return {"status": "success", "path": str(target), "schema_name": schema_name}


def validate_linkml_schema(schema_yaml: str) -> Dict[str, Any]:
    """Validate a LinkML schema against the metamodel and OntoGPT conventions."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(schema_yaml)
        tmp = f.name
    try:
        result = subprocess.run(
            ["linkml", "validate", tmp], capture_output=True, text=True, timeout=25
        )
        if result.returncode == 0:
            data = yaml.safe_load(schema_yaml)
            imports = data.get("imports", [])
            issues = []
            if "core" not in imports and "linkml:types" not in str(imports):
                issues.append("Missing recommended imports: linkml:types and/or core")
            has_named = any(
                c.get("is_a") == "NamedEntity" for c in data.get("classes", {}).values()
            )
            if not has_named:
                issues.append("No class inherits from NamedEntity (required for grounding)")
            if issues:
                return {"status": "warning", "message": "; ".join(issues), "valid": True}
            return {
                "status": "success",
                "message": "Schema is valid and OntoGPT-compatible.",
                "valid": True,
            }
        return {
            "status": "error",
            "message": result.stderr or result.stdout or "Validation failed",
            "valid": False,
        }
    except FileNotFoundError:
        try:
            data = yaml.safe_load(schema_yaml)
            required = ["id", "name", "imports", "classes"]
            missing = [k for k in required if k not in data]
            if missing:
                return {
                    "status": "error",
                    "message": f"Missing keys: {missing}",
                    "valid": False,
                }
            return {
                "status": "success",
                "message": "Basic structural validation passed (linkml CLI not found).",
                "valid": True,
            }
        except Exception as e:
            return {"status": "error", "message": str(e), "valid": False}
    finally:
        Path(tmp).unlink(missing_ok=True)
