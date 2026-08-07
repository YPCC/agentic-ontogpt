"""LinkML schema validation ladder and persistence helpers.

Validation stages (ladder):
  1. YAML syntax
  2. Required top-level keys
  3. LinkML metamodel (CLI when available)
  4. OntoGPT / SPIRES conventions
  5. OntoGPT template load (when ontogpt is installed)

Convention failures set valid=False (they are not soft-passed).
Skipped optional stages (no CLI / no ontogpt) are recorded as skipped,
not as ok=True. validation_completeness is full | partial | invalid.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


def save_template_yaml(
    schema_yaml: str,
    schema_name: str = "clinical_extraction",
    out_dir: str = "/tmp/ontogpt_templates",
) -> Dict[str, Any]:
    """Persist a generated LinkML YAML to disk."""
    path = Path(out_dir)
    path.mkdir(parents=True, exist_ok=True)
    target = path / f"{schema_name}.yaml"
    target.write_text(schema_yaml)
    return {"status": "success", "path": str(target), "schema_name": schema_name}


def _stage(
    name: str,
    ok: Optional[bool],
    messages: Optional[List[str]] = None,
    *,
    skipped: bool = False,
) -> Dict[str, Any]:
    """ok=True pass, ok=False fail, ok=None + skipped=True for unavailable tools."""
    return {
        "stage": name,
        "ok": ok,
        "skipped": skipped,
        "messages": messages or [],
    }


def validate_linkml_schema(schema_yaml: str) -> Dict[str, Any]:
    """Run the multi-stage validation ladder on a schema YAML string.

    Returns:
      valid: bool — True if no hard errors (skipped optional stages allowed)
      validation_completeness: full | partial | invalid
      skipped_stages: stages not run (tool unavailable)
      stages: list of per-stage results (ok True/False/None; skipped flag)
      errors / warnings / status / message
    """
    stages: List[Dict[str, Any]] = []
    errors: List[str] = []
    warnings: List[str] = []
    data: Any = None

    try:
        data = yaml.safe_load(schema_yaml)
        if not isinstance(data, dict):
            stages.append(_stage("yaml_syntax", False, ["Root must be a mapping"]))
            errors.append("YAML root must be a mapping/object")
            return _finalize(False, stages, errors, warnings)
        stages.append(_stage("yaml_syntax", True))
    except Exception as e:
        stages.append(_stage("yaml_syntax", False, [str(e)]))
        errors.append(f"YAML parse error: {e}")
        return _finalize(False, stages, errors, warnings)

    required = ["id", "name", "imports", "classes"]
    missing = [k for k in required if k not in data]
    if missing:
        msg = f"Missing required keys: {missing}"
        stages.append(_stage("required_keys", False, [msg]))
        errors.append(msg)
        return _finalize(False, stages, errors, warnings)
    stages.append(_stage("required_keys", True))

    cli_ok, cli_msgs = _linkml_cli_validate(schema_yaml)
    if cli_ok is True:
        stages.append(_stage("linkml_metamodel", True))
    elif cli_ok is False:
        stages.append(_stage("linkml_metamodel", False, cli_msgs))
        errors.extend(cli_msgs)
    else:
        stages.append(
            _stage(
                "linkml_metamodel",
                None,
                ["linkml CLI not available; skipped metamodel check"],
                skipped=True,
            )
        )
        warnings.append("linkml CLI not available; metamodel stage skipped")

    conv_errs, conv_warns = _check_ontogpt_conventions(data)
    if conv_errs:
        stages.append(_stage("ontogpt_conventions", False, conv_errs))
        errors.extend(conv_errs)
    else:
        stages.append(_stage("ontogpt_conventions", True, conv_warns or None))
    warnings.extend(conv_warns)

    load_ok, load_msgs = _try_ontogpt_template_load(schema_yaml)
    if load_ok is True:
        stages.append(_stage("ontogpt_template_load", True))
    elif load_ok is False:
        stages.append(_stage("ontogpt_template_load", False, load_msgs))
        errors.extend(load_msgs)
    else:
        stages.append(
            _stage(
                "ontogpt_template_load",
                None,
                ["ontogpt not installed; template-load stage skipped"],
                skipped=True,
            )
        )
        warnings.append("ontogpt not installed; template-load stage skipped")

    valid = len(errors) == 0
    return _finalize(valid, stages, errors, warnings)


def _finalize(
    valid: bool,
    stages: List[Dict[str, Any]],
    errors: List[str],
    warnings: List[str],
) -> Dict[str, Any]:
    skipped = [s["stage"] for s in stages if s.get("skipped")]
    failed = [s["stage"] for s in stages if s.get("ok") is False]
    if not valid or failed:
        completeness = "invalid"
    elif skipped:
        completeness = "partial"
    else:
        completeness = "full"
    return {
        "status": "success" if valid else "error",
        "valid": valid,
        "validation_completeness": completeness,
        "skipped_stages": skipped,
        "message": (
            (
                "Schema passed validation ladder"
                + (f" (partial; skipped: {skipped})" if completeness == "partial" else ".")
            )
            if valid
            else "; ".join(errors) or "Validation failed"
        ),
        "errors": errors,
        "warnings": warnings,
        "stages": stages,
    }


def _linkml_cli_validate(schema_yaml: str) -> tuple:
    """Returns (True|False|None, messages). None = CLI unavailable."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(schema_yaml)
        tmp = f.name
    try:
        result = subprocess.run(
            ["linkml", "validate", tmp],
            capture_output=True,
            text=True,
            timeout=25,
        )
        if result.returncode == 0:
            return True, []
        msg = (result.stderr or result.stdout or "linkml validate failed").strip()
        return False, [msg]
    except FileNotFoundError:
        return None, []
    except Exception as e:
        return False, [str(e)]
    finally:
        Path(tmp).unlink(missing_ok=True)


def _check_ontogpt_conventions(data: dict) -> tuple:
    errors: List[str] = []
    warnings: List[str] = []
    imports = data.get("imports") or []
    import_str = " ".join(str(i) for i in imports)
    if "linkml:types" not in import_str and "types" not in import_str:
        errors.append("Missing import: linkml:types")
    if "core" not in imports and "core" not in import_str:
        errors.append("Missing import: core (OntoGPT NamedEntity / CompoundExpression)")
    classes = data.get("classes") or {}
    if not isinstance(classes, dict) or not classes:
        errors.append("classes must be a non-empty mapping")
        return errors, warnings
    has_named = any(
        isinstance(c, dict) and c.get("is_a") == "NamedEntity" for c in classes.values()
    )
    if not has_named:
        errors.append("No class with is_a: NamedEntity (required for grounding)")
    roots = [
        name
        for name, c in classes.items()
        if isinstance(c, dict) and c.get("tree_root") is True
    ]
    if not roots:
        errors.append("No class with tree_root: true")
    elif len(roots) > 1:
        warnings.append(f"Multiple tree_root classes: {roots}")
    return errors, warnings


def _try_ontogpt_template_load(schema_yaml: str) -> tuple:
    try:
        from ontogpt.io.template_loader import get_template_details  # type: ignore
    except Exception:
        return None, []
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(schema_yaml)
        tmp = f.name
    try:
        get_template_details(template=tmp)
        return True, []
    except Exception as e:
        return False, [f"OntoGPT template load failed: {e}"]
    finally:
        Path(tmp).unlink(missing_ok=True)
