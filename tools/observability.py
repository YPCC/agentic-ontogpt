"""Cost / latency observability and HTML dashboard (P3)."""
from __future__ import annotations
import json, time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_RATES = {
    "gemini-2.0-flash": {"input": 0.0001, "output": 0.0004},
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "default": {"input": 0.001, "output": 0.002},
}

@dataclass
class StageRecord:
    name: str
    duration_sec: float
    model: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    api_calls: int = 0
    meta: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ObservabilitySession:
    run_id: str
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    stages: List[StageRecord] = field(default_factory=list)
    _t0: float = field(default_factory=time.perf_counter, repr=False)
    _last: float = field(default_factory=time.perf_counter, repr=False)

    def mark(self, name, *, model=None, input_tokens=0, output_tokens=0, api_calls=0, meta=None):
        now = time.perf_counter()
        rec = StageRecord(name=name, duration_sec=now - self._last, model=model,
                          input_tokens=input_tokens, output_tokens=output_tokens,
                          api_calls=api_calls, meta=meta or {})
        self.stages.append(rec)
        self._last = now
        return rec

    def total_sec(self):
        return time.perf_counter() - self._t0

    def estimate_cost_usd(self, rates=None):
        rates = rates or DEFAULT_RATES
        total = 0.0
        for s in self.stages:
            r = rates.get(s.model) or rates["default"]
            total += (s.input_tokens / 1000.0) * float(r.get("input", 0))
            total += (s.output_tokens / 1000.0) * float(r.get("output", 0))
        return total

    def summary(self):
        return {"run_id": self.run_id, "started_at": self.started_at, "total_sec": self.total_sec(),
                "n_stages": len(self.stages),
                "total_input_tokens": sum(s.input_tokens for s in self.stages),
                "total_output_tokens": sum(s.output_tokens for s in self.stages),
                "total_api_calls": sum(s.api_calls for s in self.stages),
                "estimated_cost_usd": round(self.estimate_cost_usd(), 6),
                "stages": [asdict(s) for s in self.stages]}

    def write_json(self, path):
        p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.summary(), indent=2)); return str(p)

def estimate_tokens_from_text(text):
    return max(1, len(text or "") // 4)

def render_dashboard_html(sessions, title="agentic-ontogpt observability"):
    rows = []
    for s in sessions:
        rows.append(f"<tr><td>{s.get('run_id','')}</td><td>{s.get('total_sec',0):.3f}</td>"
                    f"<td>{s.get('total_input_tokens',0)}</td><td>{s.get('total_output_tokens',0)}</td>"
                    f"<td>{s.get('total_api_calls',0)}</td><td>${s.get('estimated_cost_usd',0):.6f}</td>"
                    f"<td>{s.get('n_stages',0)}</td></tr>")
    stage_blocks = []
    for s in sessions:
        total = max(float(s.get("total_sec") or 0.001), 0.001)
        bars = []
        for st in s.get("stages") or []:
            pct = 100.0 * float(st.get("duration_sec") or 0) / total
            bars.append(f"<div class='bar' style='width:{pct:.1f}%'>{st.get('name')} {st.get('duration_sec',0):.2f}s</div>")
        stage_blocks.append(f"<h3>{s.get('run_id')}</h3><div class='stack'>{''.join(bars)}</div>")
    return f"""<!DOCTYPE html><html><head><meta charset='utf-8'/><title>{title}</title>
<style>body{{font-family:system-ui,sans-serif;margin:2rem;background:#0b1020;color:#e8eefc}}
table{{border-collapse:collapse;width:100%;margin-bottom:2rem}}th,td{{border:1px solid #2a3555;padding:.5rem}}
th{{background:#151c33}}.stack{{background:#151c33;border-radius:6px;overflow:hidden;margin-bottom:1rem}}
.bar{{background:linear-gradient(90deg,#3b82f6,#06b6d4);padding:.35rem .5rem;margin:2px 0;font-size:12px}}</style></head>
<body><h1>{title}</h1><table><thead><tr><th>Run</th><th>Total s</th><th>In tok</th><th>Out tok</th><th>API</th><th>USD</th><th>Stages</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table><h2>Stage latency</h2>{''.join(stage_blocks)}</body></html>"""

def write_dashboard(sessions, path):
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(render_dashboard_html(sessions)); return str(p)
