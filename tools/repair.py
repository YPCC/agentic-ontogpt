"""Deterministic template repair controller (error-directed, bounded)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List

from .linkml_tools import validate_linkml_schema


@dataclass
class RepairStep:
    iteration: int
    schema_yaml: str
    validation: Dict[str, Any]


@dataclass
class RepairResult:
    valid: bool
    schema_yaml: str
    schema_version: int
    iterations: int
    history: List[RepairStep] = field(default_factory=list)
    final_validation: Dict[str, Any] = field(default_factory=dict)
    stopped_reason: str = ""


def repair_until_valid(
    initial_schema_yaml: str,
    regenerate_fn: Callable[[str, Dict[str, Any], int], str],
    *,
    max_iterations: int = 3,
) -> RepairResult:
    history: List[RepairStep] = []
    schema = initial_schema_yaml
    version = 0

    for i in range(1, max_iterations + 1):
        report = validate_linkml_schema(schema)
        history.append(RepairStep(iteration=i, schema_yaml=schema, validation=report))
        if report.get("valid"):
            return RepairResult(
                valid=True,
                schema_yaml=schema,
                schema_version=version,
                iterations=i,
                history=history,
                final_validation=report,
                stopped_reason="validation_passed",
            )
        schema = regenerate_fn(schema, report, i)
        version += 1

    final = validate_linkml_schema(schema)
    history.append(RepairStep(iteration=max_iterations + 1, schema_yaml=schema, validation=final))
    return RepairResult(
        valid=bool(final.get("valid")),
        schema_yaml=schema,
        schema_version=version,
        iterations=max_iterations,
        history=history,
        final_validation=final,
        stopped_reason="max_iterations" if not final.get("valid") else "validation_passed",
    )


_MINIMAL_VALID_SPIRES = """id: https://w3id.org/ontogpt/demo_clinical
name: demo_clinical
title: Demo clinical SPIRES schema
imports:
  - linkml:types
  - core
prefixes:
  linkml: https://w3id.org/linkml/
  demo: https://w3id.org/ontogpt/demo_clinical/
default_prefix: demo
default_range: string
classes:
  ExtractionResult:
    tree_root: true
    attributes:
      medications:
        range: Medication
        multivalued: true
      adverse_events:
        range: AdverseEvent
        multivalued: true
  Medication:
    is_a: NamedEntity
    attributes:
      id:
        identifier: true
        range: uriorcurie
      label:
        range: string
  AdverseEvent:
    is_a: NamedEntity
    attributes:
      id:
        identifier: true
        range: uriorcurie
      label:
        range: string
"""


def fixture_regenerate(schema_yaml: str, validation: Dict[str, Any], iteration: int) -> str:
    if iteration >= 1:
        return _MINIMAL_VALID_SPIRES
    return schema_yaml


def noop_regenerate(schema_yaml: str, validation: Dict[str, Any], iteration: int) -> str:
    return schema_yaml
