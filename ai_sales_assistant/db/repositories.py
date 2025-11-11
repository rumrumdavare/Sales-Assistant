from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

DB_PATH = Path("local.db")

def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

def client_overview(client_name: str) -> Dict[str, Any] | None:
    q = """
    SELECT client_id, company_name, industry, region, owner_name,
           lifecycle_stage, deal_stage, lifetime_value, created_at
    FROM clients
    WHERE company_name LIKE ? COLLATE NOCASE
    LIMIT 1;
    """
    with _conn() as c:
        r = c.execute(q, (client_name,)).fetchone()
    return dict(r) if r else None

def kpi_snapshot(client_name: str, months: int = 3) -> List[Dict[str, Any]]:
    q = """
    WITH tgt AS (
      SELECT client_id FROM clients WHERE company_name LIKE ? COLLATE NOCASE LIMIT 1
    )
    SELECT m.month, m.spend, m.satisfaction_score, m.churn_risk, m.open_tickets, m.renewal_due
    FROM metrics m
    JOIN tgt ON tgt.client_id = m.client_id
    ORDER BY m.month DESC
    LIMIT ?
    """
    with _conn() as c:
        rows = c.execute(q, (client_name, months)).fetchall()
    # Return in ascending month order for nicer trend calc
    return [dict(r) for r in rows][::-1]

def recent_interactions(client_name: str, limit: int = 5) -> List[Dict[str, Any]]:
    q = """
    WITH tgt AS (
      SELECT client_id FROM clients WHERE company_name LIKE ? COLLATE NOCASE LIMIT 1
    )
    SELECT i.timestamp, i.channel, i.owner_name, i.sentiment, i.notes
    FROM interactions i
    JOIN tgt ON tgt.client_id = i.client_id
    ORDER BY i.timestamp DESC
    LIMIT ?
    """
    with _conn() as c:
        rows = c.execute(q, (client_name, limit)).fetchall()
    return [dict(r) for r in rows]

def open_tickets(client_name: str, status: str | None = None) -> List[Dict[str, Any]]:
    q = """
    WITH tgt AS (
      SELECT client_id FROM clients WHERE company_name LIKE ? COLLATE NOCASE LIMIT 1
    )
    SELECT t.ticket_id, t.category, t.status, t.opened_at, t.resolved_at, t.resolution_time_days, t.priority
    FROM tickets t
    JOIN tgt ON tgt.client_id = t.client_id
    WHERE (? IS NULL OR t.status = ?)
    ORDER BY
      CASE t.status WHEN 'Open' THEN 0 WHEN 'Pending' THEN 1 ELSE 2 END,
      t.opened_at DESC
    """
    params = (client_name, status, status)
    with _conn() as c:
        rows = c.execute(q, params).fetchall()
    return [dict(r) for r in rows]
