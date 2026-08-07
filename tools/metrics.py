"""Component-level metrics for agentic-ontogpt (P2)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass
class ComponentMetrics:
    ontology_selection: Dict[str, Any] = field(default_factory=dict)
    template: Dict[str, Any] = field(default_factory=dict)
    extraction: Dict[str, Any] = field(default_factory=dict)
    grounding: Dict[str, Any] = field(default_factory=dict)
    operational: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def score_ontology_selection(selected, gold=None, *, policy_rejected=None):
    n = len(selected)
    out = {"n_entity_types": n, "n_selected": sum(1 for v in selected.values() if v),
           "coverage": (sum(1 for v in selected.values() if v) / n) if n else 0.0,
           "n_policy_rejected": len(policy_rejected or [])}
    if gold:
        keys = set(selected) | set(gold)
        correct = sum(1 for k in keys
                      if (selected.get(k) or "").upper() == (gold.get(k) or "").upper()
                      and (selected.get(k) or gold.get(k)))
        out["top1_accuracy"] = correct / len(keys) if keys else 0.0
        out["correct"] = correct
    return out


def score_template_stage(validation_report, *, repair_iterations=0, first_pass_valid=None, schema_version=0):
    stages = validation_report.get("stages") or []
    return {"valid": bool(validation_report.get("valid")),
            "n_errors": len(validation_report.get("errors") or []),
            "stages_ok": [s.get("stage") for s in stages if s.get("ok")],
            "stages_failed": [s.get("stage") for s in stages if not s.get("ok")],
            "repair_iterations": repair_iterations, "first_pass_valid": first_pass_valid,
            "repair_success": bool(validation_report.get("valid")) and repair_iterations > 0,
            "schema_version": schema_version}


def score_extraction_outcome(extraction_result):
    outcome = extraction_result.get("outcome")
    obj = extraction_result.get("extracted_object")
    n_fields = sum(1 for v in obj.values() if v) if isinstance(obj, dict) else 0
    return {"outcome": outcome, "status": extraction_result.get("status"),
            "is_success": outcome in ("REAL_SUCCESS", "SIMULATION_REQUESTED"),
            "is_real_success": outcome == "REAL_SUCCESS",
            "is_fixture": bool(extraction_result.get("fixture")),
            "error_type": extraction_result.get("error_type"), "n_extracted_fields": n_fields,
            "blocked": extraction_result.get("error_type") == "invalid_schema"}


def score_grounding(grounding_report):
    return {"n_grounded": grounding_report.get("n_grounded", 0),
            "n_ungrounded": grounding_report.get("n_ungrounded", 0),
            "grounding_rate": grounding_report.get("grounding_rate", 0.0)}


class Timer:
    def __init__(self):
        self.marks = {}
        self._t0 = time.perf_counter()
        self._last = self._t0

    def mark(self, name):
        now = time.perf_counter()
        self.marks[name] = now - self._last
        self._last = now
        return self.marks[name]

    def total(self):
        return time.perf_counter() - self._t0

    def as_dict(self):
        return {"stages_sec": dict(self.marks), "total_sec": self.total()}


def build_component_metrics(*, selected_ontologies=None, gold_ontologies=None, policy_rejected=None,
                            validation_report=None, repair_iterations=0, first_pass_valid=None,
                            schema_version=0, extraction_result=None, grounding_report=None, timer=None):
    m = ComponentMetrics()
    if selected_ontologies is not None:
        m.ontology_selection = score_ontology_selection(selected_ontologies, gold_ontologies,
                                                        policy_rejected=policy_rejected)
    if validation_report is not None:
        m.template = score_template_stage(validation_report, repair_iterations=repair_iterations,
                                          first_pass_valid=first_pass_valid, schema_version=schema_version)
    if extraction_result is not None:
        m.extraction = score_extraction_outcome(extraction_result)
    if grounding_report is not None:
        m.grounding = score_grounding(grounding_report)
    if timer is not None:
        m.operational = timer.as_dict()
    return m
