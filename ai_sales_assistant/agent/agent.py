from __future__ import annotations
import os
from typing import List
from dotenv import load_dotenv

from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
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
Keep the final brief under 150 words. If client_overview returns not_found, do not call other SQL tools; instead run notes_search (query and client_name = the requested client) and then write a brief. Use 'Not available' for sections without data.
Output sections in this order:

Overview
KPIs (last 3 months)
Risks
Talking points
References

Tool usage guidance:
1) Always resolve the client with client_overview first (exact or fuzzy match).
 1a) If client_overview returns not_found, call notes_search next (query and client_name = requested client) and then produce the Final Answer.
2) Retrieve last 3 months KPIs (kpi_snapshot months=3).
3) Pull 3 most recent interactions (recent_interactions limit=3).
4) List tickets (open_tickets) - highlight High priority or Open status.
5) Search notes (notes_search client_name=...) with at most 3 short snippets (~300 chars each).
Synthesise clearly; do not dump raw JSON.

Stop conditions and limits:
- Call each tool at most once.
- Do not call client_overview more than once.
- After you have Overview and at least two of: KPIs, Interactions, Tickets, or Notes, immediately produce Final Answer.
- If you reach notes_search (including the not_found fallback), produce Final Answer right after it.
"""

REACT_TEMPLATE = """{system}

You have access to the following tools:
{tools}

Use this format:

Question: the input question
Thought: you should always think step by step about what to do
Action: the action to take, must be one of [{tool_names}]
Action Input: a strict JSON object matching the tool schema
Observation: the result of the action
... (repeat Thought/Action/Action Input/Observation as needed)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Important formatting rules:
- Action Input MUST be valid JSON, not plain text. Example: {{"client_name": "Wolfe LLC Ltd", "months": 3}}
- Do NOT include commentary with Action or Action Input lines.
- Only produce Final Answer when you are done with tools.

Begin!

Question: {input}
Thought: {agent_scratchpad}
"""

prompt = ChatPromptTemplate.from_template(REACT_TEMPLATE).partial(system=SYSTEM_PROMPT)

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
    tools: List = _tool_list()

    prompt = ChatPromptTemplate.from_template(REACT_TEMPLATE).partial(system=SYSTEM_PROMPT)

    agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=15,  # default was ~5
        max_execution_time=45,
        return_intermediate_steps=True,
        handle_parsing_errors=(
            "If the previous step failed to parse, and you were calling a tool, "
            "output only a corrected 'Action Input' line with a valid JSON object. "
            "Otherwise, produce 'Final Answer' in the required format."
        ),
    )
    return executor

def run_brief(client_name: str) -> str:
    """Convenience method to get a brief for a single client."""
    executor = build_agent()
    query = f"Prepare a pre-call brief for {client_name}. Include only factual info from tools."
    result = executor.invoke({"input": query})
    # AgentExecutor returns a dict with 'output'
    return result.get("output", "").strip()
