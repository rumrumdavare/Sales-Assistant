from __future__ import annotations
from typing import Optional, List, Dict, Any
from langchain.tools import StructuredTool
from ai_sales_assistant.db import repositories as repo

def _ov(client_name: str) -> Dict[str, Any] | str:
    r = repo.client_overview(client_name)
    return r if r else "Not found"

def _kpi(client_name: str, months: int = 3) -> List[Dict[str, Any]]:
    return repo.kpi_snapshot(client_name, months)

def _interactions(client_name: str, limit: int = 5) -> List[Dict[str, Any]]:
    return repo.recent_interactions(client_name, limit)

def _tickets(client_name: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
    return repo.open_tickets(client_name, status)

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
