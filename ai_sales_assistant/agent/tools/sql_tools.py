from __future__ import annotations
from typing import Optional, List, Dict, Any
import json
from langchain.tools import StructuredTool
from ai_sales_assistant.db import repositories as repo

USED: set[str] = set()

def reset_used() -> None:
    USED.clear()

def _normalize_name(arg: Any) -> str:
    """Accept plain name, or JSON string with client_name/company_name, or dict.
    Returns best-effort extracted company name.
    """
    if isinstance(arg, str):
        s = arg.strip()
        if s.startswith("{") and s.endswith("}"):
            try:
                data = json.loads(s)
                return (
                    data.get("client_name")
                    or data.get("company_name")
                    or s
                )
            except Exception:
                return arg
        return arg
    if isinstance(arg, dict):
        return arg.get("client_name") or arg.get("company_name") or ""
    return str(arg)


def _ov(client_name: str):
    name = _normalize_name(client_name)
    if "client_overview" in USED:
        return "Already called client_overview; do not call again."
    USED.add("client_overview")
    r = repo.client_overview(name)
    return r if r else {"not_found": True}

def _kpi(client_name: str, months: int = 3) -> List[Dict[str, Any]]:
    name = _normalize_name(client_name)
    # Allow months to come via JSON string
    if isinstance(client_name, str) and client_name.strip().startswith("{"):
        try:
            data = json.loads(client_name)
            months = int(data.get("months", months))
        except Exception:
            pass
    return repo.kpi_snapshot(name, months)

def _interactions(client_name: str, limit: int = 5) -> List[Dict[str, Any]]:
    name = _normalize_name(client_name)
    if isinstance(client_name, str) and client_name.strip().startswith("{"):
        try:
            data = json.loads(client_name)
            limit = int(data.get("limit", limit))
        except Exception:
            pass
    return repo.recent_interactions(name, limit)

def _tickets(client_name: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
    name = _normalize_name(client_name)
    if isinstance(client_name, str) and client_name.strip().startswith("{"):
        try:
            data = json.loads(client_name)
            status = data.get("status", status)
        except Exception:
            pass
    return repo.open_tickets(name, status)

client_overview_tool = StructuredTool.from_function(
    func=_ov,
    name="client_overview",
    description="Get a client's profile fields by company name.",
)

kpi_snapshot_tool = StructuredTool.from_function(
    func=_kpi,
    name="kpi_snapshot",
    description="Get last N months of KPIs (spend, satisfaction, churn, open_tickets).",
)

recent_interactions_tool = StructuredTool.from_function(
    func=_interactions,
    name="recent_interactions",
    description="Get the latest interactions for a client.",
)

open_tickets_tool = StructuredTool.from_function(
    func=_tickets,
    name="open_tickets",
    description="List tickets for a client; optional exact status filter (Open/Pending/Resolved).",
)
