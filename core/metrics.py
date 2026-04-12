"""
InfiniteClaw — Metrics & Analytics
Usage tracking and cost estimation.
"""
import json
import os
from datetime import datetime
from core.config import METRICS_DIR
from core.local_db import get_usage_summary, get_current_workspace_id


def get_metrics() -> dict:
    ws_id = get_current_workspace_id()
    if not ws_id:
        return {"total_calls": 0, "total_tokens": 0, "total_cost": 0.0, "avg_response_ms": 0}
    return get_usage_summary(ws_id)


def log_event_metric(bot_id: str, event_type: str, details: dict = None):
    """Log a pictorial event for the performance tracker."""
    metric_file = METRICS_DIR / f"{bot_id}_events.json"
    events = []
    if metric_file.exists():
        try:
            events = json.loads(metric_file.read_text())
        except Exception:
            events = []
    events.append({
        "type": event_type,
        "details": details or {},
        "timestamp": datetime.now().isoformat(),
    })
    # Keep last 500 events
    events = events[-500:]
    metric_file.write_text(json.dumps(events, indent=2))
