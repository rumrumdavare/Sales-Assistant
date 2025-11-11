from __future__ import annotations
import os
from typing import List
from dotenv import load_dotenv

from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq

# Tools
from ai_sales_assistant.agent.tools.sql_tools import (
    client_overview_tool,
    kpi_snapshot_tool,
    recent_interactions_tool,
    open_tickets_tool,
)
from ai_sales_assistant.agent.tools.notes_tool import notes_search_tool

load_dotenv()

SYSTEM_PROMPT = """You are a sales enablement assistant that prepares concise pre-call briefs.
Use tools for facts and do not invent data. If a section has no data, say 'Not available'.
Keep the final brief under 150 words. Output sections in this order:

Overview
KPIs (with ▲/▼/▬ where clear from last 3 months)
Risks
Talking points
References

Tool usage guidance:
1) Always resolve the client with client_overview first (exact or fuzzy match).
2) Retrieve last 3 months KPIs (kpi_snapshot months=3).
3) Pull 3 most recent interactions (recent_interactions limit=3).
4) List tickets (open_tickets) - highlight High priority or Open status.
5) Search notes (notes_search client_name=...) with at most 3 short snippets (~≤300 chars each).
Synthesise clearly; do not dump raw JSON.
"""

REACT_TEMPLATE = """{system}

You have access to the following tools:
{tools}

Use this format:

Question: the input question
Thought: you should always think step by step about what to do
Action: the action to take, must be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (repeat Thought/Action/Action Input/Observation as needed)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: {agent_scratchpad}
"""

prompt = PromptTemplate(
    template=REACT_TEMPLATE,
    input_variables=["input", "agent_scratchpad", "tool_names", "tools"],
    partial_variables={"system": SYSTEM_PROMPT},
)

def _build_llm():
    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    return ChatGroq(model=model, temperature=0.1)

def _tool_list():
    # Order hints the flow; ReAct can still choose any
    return [
        client_overview_tool,
        kpi_snapshot_tool,
        recent_interactions_tool,
        open_tickets_tool,
        notes_search_tool,
    ]

def build_agent() -> AgentExecutor:
    llm = _build_llm()
    tools = _tool_list()

    prompt = PromptTemplate(
    template=REACT_TEMPLATE,
    input_variables=["input", "agent_scratchpad", "tool_names", "tools"],
    partial_variables={"system": SYSTEM_PROMPT},
    )

    agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=False, handle_parsing_errors=True)
    return executor

def run_brief(client_name: str) -> str:
    """Convenience method to get a brief for a single client."""
    executor = build_agent()
    query = f"Prepare a pre-call brief for {client_name}. Include only factual info from tools."
    result = executor.invoke({"input": query})
    # AgentExecutor returns a dict with 'output'
    return result.get("output", "").strip()
