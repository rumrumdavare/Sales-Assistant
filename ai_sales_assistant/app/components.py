from __future__ import annotations
from typing import List, Tuple
import sqlite3
from pathlib import Path
import streamlit as st

DB_PATH = Path("local.db")

# ---------- Data helpers ----------
def list_clients(limit: int = 200) -> List[str]:
    if not DB_PATH.exists():
        return []
    with sqlite3.connect(DB_PATH) as c:
        rows = c.execute(
            "SELECT company_name FROM clients ORDER BY company_name LIMIT ?",
            (limit,),
        ).fetchall()
    return [r[0] for r in rows]

# ---------- Session / rate limit ----------
def init_session(limit: int = 20) -> None:
    if "calls_used" not in st.session_state:
        st.session_state.calls_used = 0
    if "call_limit" not in st.session_state:
        st.session_state.call_limit = limit

def can_call() -> bool:
    return st.session_state.calls_used < st.session_state.call_limit

def bump_calls() -> None:
    st.session_state.calls_used += 1

# ---------- Widgets ----------
def client_picker(clients: List[str]) -> Tuple[str, bool]:
    """Returns (target_name, run_clicked)."""
    col1, col2 = st.columns([2, 1])
    with col1:
        idx = 0 if clients else None
        clients_with_placeholder = ["Select a client"] + clients
        
        chosen = st.selectbox(
        "Pick a client",
        clients_with_placeholder,
        index=0
        )
    if chosen == "Select a client":
        chosen = None

    with col2:
        typed = st.text_input("…or type a name", value="")
    target = (typed or chosen or "").strip()
    run = st.button("Generate Brief", type="primary", disabled=not bool(target))
    st.caption("Tip: tweak the name if needed (e.g., 'Acme' vs 'Acme Corp').")
    return target, run

# ---------- Renderers ----------
def render_brief(markdown_text: str) -> None:
    if markdown_text:
        st.markdown(markdown_text)
    else:
        st.info("No data found. Try selecting an exact company name from the list.")

def footer(model_name: str) -> None:
    st.divider()
    st.caption(
        f"Calls used: {st.session_state.calls_used}/{st.session_state.call_limit} · "
        f"Model: {model_name} · Local RAG (MiniLM + Chroma)"
    )
