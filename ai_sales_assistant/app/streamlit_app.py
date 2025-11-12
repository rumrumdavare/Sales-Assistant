from __future__ import annotations
import os
from dotenv import load_dotenv
import streamlit as st

os.environ["CHROMA_TELEMETRY_DISABLED"] = "1"
os.environ["LANGCHAIN_TELEMETRY"] = "false"

# --- path fix: ensure project root is importable ---
import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2]  # project root
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ai_sales_assistant.app.components import (
    list_clients,
    init_session,
    can_call,
    bump_calls,
    client_picker,
    render_brief,
    footer,
)

# Load env (works locally). On Streamlit Cloud, prefer st.secrets.
load_dotenv()
if "GROQ_API_KEY" not in os.environ and "GROQ_API_KEY" in st.secrets:
    os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
if "GROQ_MODEL" not in os.environ and "GROQ_MODEL" in st.secrets:
    os.environ["GROQ_MODEL"] = st.secrets["GROQ_MODEL"]
if not os.getenv("GROQ_API_KEY"):
    raise ValueError("❌ GROQ_API_KEY not found. Please set it in .env or Streamlit Secrets.")

MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

st.set_page_config(page_title="AI Sales Assistant", page_icon="📇", layout="centered")
st.title("📇 AI Sales Assistant — Pre-Call Briefs")
st.caption(f"CWD: {os.getcwd()}")

# One-time init
init_session(limit=20)

from ai_sales_assistant.agent.agent import run_brief

# UI flow
clients = list_clients(200)
target, run = client_picker(clients)

placeholder = st.empty()
if run:
    if not can_call():
        st.warning("Daily demo limit reached. Please try again later.")
    else:
        with st.spinner("Preparing your brief…"):
            try:
                brief = run_brief(target)
                bump_calls()
                with placeholder:
                    render_brief(brief)
            except Exception as e:
                st.error(f"Error: {e}")

footer(MODEL)
