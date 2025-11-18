from __future__ import annotations
import os
from dotenv import load_dotenv
import streamlit as st

hide_loader = """
<style>
#stDecoration, /* the top-right Streamlit spinner */
.stDeployButton, /* "running man" spinner when deploying */
.css-6qob1r, /* older spinner class */
.stSpinner > div > div { 
    display: none !important; 
}
</style>
"""
st.markdown(hide_loader, unsafe_allow_html=True)

os.environ["CHROMA_TELEMETRY_DISABLED"] = "1"
os.environ["LANGCHAIN_TELEMETRY"] = "false"

# --- path fix: ensure project root is importable ---
import sys, pathlib
from pathlib import Path 

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

from ai_sales_assistant.agent.agent import run_brief

# Load env (works locally). On Streamlit Cloud, prefer st.secrets.
load_dotenv()
if "GROQ_API_KEY" not in os.environ and "GROQ_API_KEY" in st.secrets:
    os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
if "GROQ_MODEL" not in os.environ and "GROQ_MODEL" in st.secrets:
    os.environ["GROQ_MODEL"] = st.secrets["GROQ_MODEL"]
if not os.getenv("GROQ_API_KEY"):
    raise ValueError("❌ GROQ_API_KEY not found. Please set it in .env or Streamlit Secrets.")

MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

def load_css(path: str) -> None:
    css_path = Path(path)
    if css_path.is_file():
        with open(css_path, "r", encoding="utf-8") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

st.set_page_config(page_title="AI Sales Assistant", page_icon="📇", layout="centered")
# Load custom CSS
load_css("ai_sales_assistant/app/assets/styles.css")
st.title("📇 AI Sales Assistant — Pre-Call Briefs")
st.markdown("""
**Prepare for your next client call.**  
Generate a full client overview or talking points only — synthesized from recent interactions, KPIs, and tickets.
""")

# One-time init
init_session(limit=20)

# Cache the agent once so "talking points only" can use it
@st.cache_resource(show_spinner=False)
def get_executor():
    from ai_sales_assistant.agent.agent import build_agent
    return build_agent()

# Wrapper for running talking points only
def run_talking_points_only(client_name: str) -> str:
    exec_ = get_executor()
    q = (
        f"Prepare a pre-call brief for {client_name}. Include only factual info from tools. "
        f"Return ONLY the 'Talking points' section as 3-5 concise, professional bullets. "
        f"Do not include Overview, KPIs, Risks, or References. Avoid repeating raw notes; "
        f"synthesize next-step discussion items based on recent interactions, KPIs, and open tickets."
    )
    result = exec_.invoke({"input": q})
    return (result.get("output") or "").strip()

# UI flow
clients = list_clients(200)
target, run, brief_type = client_picker(clients)

placeholder = st.empty()
if run:
    if not can_call():
        st.warning("Daily demo limit reached. Please try again later.")
    else:
        with st.spinner("Preparing your brief…"):
            try:
                if brief_type == "Full brief":
                    md = run_brief(target)
                    render_brief(md)
                elif brief_type == "Talking points only":
                    md = run_talking_points_only(target)
                    render_brief(md)
                else:
                    st.info("Please select a brief type.")
                    st.stop()
                bump_calls()
            except Exception as e:
                st.error(f"Error: {e}")

footer(MODEL)
