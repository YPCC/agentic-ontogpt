"""Human approval checkpoints (P3)."""
from __future__ import annotations
import json, os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional

ENV_MODE, ENV_DIR = "APPROVAL_MODE", "APPROVAL_DIR"

@dataclass
class ApprovalRequest:
    checkpoint: str
    run_id: str
    summary: str
    payload: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    def to_dict(self):
        return asdict(self)

@dataclass
class ApprovalDecision:
    checkpoint: str
    approved: bool
    reviewer: str = "system"
    comment: str = ""
    decided_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    def to_dict(self):
        return asdict(self)

def get_approval_mode(override=None):
    raw = (override or os.environ.get(ENV_MODE) or "auto").strip().lower()
    if raw in ("require", "manual", "human"): return "require"
    if raw in ("reject", "deny"): return "reject"
    return "auto"

def _approval_dir():
    d = Path(os.environ.get(ENV_DIR) or "/tmp/agentic_ontogpt_approvals")
    d.mkdir(parents=True, exist_ok=True)
    return d

def request_approval(checkpoint, run_id, summary, payload=None, *, callback=None, mode=None):
    m = get_approval_mode(mode)
    req = ApprovalRequest(checkpoint=checkpoint, run_id=run_id, summary=summary, payload=payload or {})
    if m == "auto":
        return ApprovalDecision(checkpoint=checkpoint, approved=True, reviewer="auto")
    if m == "reject":
        return ApprovalDecision(checkpoint=checkpoint, approved=False, reviewer="reject_mode",
                                comment="APPROVAL_MODE=reject")
    if callback is not None:
        return callback(req)
    req_path = _approval_dir() / f"{run_id}_{checkpoint}.request.json"
    dec_path = _approval_dir() / f"{run_id}_{checkpoint}.decision.json"
    req_path.write_text(json.dumps(req.to_dict(), indent=2))
    if dec_path.exists():
        data = json.loads(dec_path.read_text())
        return ApprovalDecision(checkpoint=checkpoint, approved=bool(data.get("approved")),
                                reviewer=str(data.get("reviewer") or "file"),
                                comment=str(data.get("comment") or ""))
    return ApprovalDecision(checkpoint=checkpoint, approved=False, reviewer="pending",
                            comment=f"Awaiting decision file: {dec_path}")

def write_decision(run_id, checkpoint, approved, *, reviewer="human", comment=""):
    path = _approval_dir() / f"{run_id}_{checkpoint}.decision.json"
    path.write_text(json.dumps({"checkpoint": checkpoint, "approved": approved,
        "reviewer": reviewer, "comment": comment,
        "decided_at": datetime.now(timezone.utc).isoformat()}, indent=2))
    return path

def gate_or_raise(checkpoint, run_id, summary, payload=None, **kwargs):
    dec = request_approval(checkpoint, run_id, summary, payload, **kwargs)
    if not dec.approved:
        raise PermissionError(f"Approval denied at checkpoint={checkpoint}: {dec.comment or dec.reviewer}")
    return dec
