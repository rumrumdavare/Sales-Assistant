from __future__ import annotations
import os
from typing import List
from dotenv import load_dotenv

from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq # type: ignore

from .tools import sql_tools, notes_tool
# Tools
from ai_sales_assistant.agent.tools.sql_tools import (
    client_overview_tool,
    kpi_snapshot_tool,
    recent_interactions_tool,
    open_tickets_tool,
)
from ai_sales_assistant.agent.tools.notes_tool import notes_search_tool

load_dotenv()

SYSTEM_PROMPT = """
You are a sales enablement assistant that prepares concise pre-call briefs for account representatives.

Core Rules
- Use tools for all factual data — never invent information.
- If a section has no data, write “Not available”.
- Keep the entire brief under 150 words.
- Output sections in this exact order:

1. Overview
2. Talking points
3. KPIs (last 3 months)
4. Risks
5. References

Tool Usage Workflow
1. Always begin with `client_overview` (exact or fuzzy match).
   - If `client_overview` returns **not_found**, immediately call `notes_search`
     (`query` = requested client name) and then produce the **Final Answer**.  
     Do **not** call any other SQL tools in this case.
2. After a valid client is found:
   - Call `kpi_snapshot` (`months` = 3) to retrieve KPIs.
   - Call `recent_interactions` (`limit` = 3) for latest client interactions.
   - Call `open_tickets` to list support issues (highlight *High priority* or *Open* status).
   - Call `notes_search` (`client_name` = client, `k` ≤ 3) for up to three short note snippets (~300 chars each).
3. If `notes_search` is called without a query, set `query` = client name (never null).

Synthesis Guidance
- Combine tool outputs into clear prose — do **not** dump raw JSON.
- If any tool yields “No relevant notes…” or similar empty data, use that as
  confirmation to end the workflow and produce the **Final Answer**.

Stop Conditions
- Call each tool at most once.
- Never call `client_overview` more than once.
- Once you have the Overview and at least two of these — KPIs, Interactions,
  Tickets, or Notes — immediately produce the **Final Answer**.
- If you reach `notes_search` (including the `not_found` fallback), always
  produce the **Final Answer** right after it.

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
     # reset once-per-executor
    sql_tools.reset_used()
    notes_tool.reset_used()

    llm = _build_llm()
    tools: List = _tool_list()

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
        early_stopping_method="force"
    )
    return executor

def run_brief(client_name: str) -> str:
    """Convenience method to get a brief for a single client."""
    executor = build_agent()
    query = f"Prepare a pre-call brief for {client_name}. Include only factual info from tools."
    result = executor.invoke({"input": query})
    output = (result.get("output", "") or "").strip()
    if output:
        return output

    # Deterministic fallback: synthesize a brief directly from repositories and notes
    try:
        from ai_sales_assistant.db import repositories as repo
        from ai_sales_assistant.rag.retriever import notes_search

        ov = repo.client_overview(client_name)
        kpis = repo.kpi_snapshot(client_name, 3)
        interactions = repo.recent_interactions(client_name, 3)
        tickets = repo.open_tickets(client_name)
        notes = notes_search(query=client_name, k=3, client_name=client_name)

        if ov:
            overview = f"{ov.get('company_name','')} | {ov.get('industry','')} | {ov.get('region','')} (Owner: {ov.get('owner_name','')})"
        else:
            overview = "Not available"

        if kpis:
            last = kpis[-1]
            spend = last.get("spend")
            spend_part = f"Spend: {spend:.0f}; " if isinstance(spend, (int, float)) else ""
            kpi_str = (
                f"{spend_part}Sat: {last.get('satisfaction_score','?')}; Churn risk: {last.get('churn_risk','?')}%"
            )
        else:
            kpi_str = "Not available"

        risks = []
        if kpis:
            try:
                if float(kpis[-1].get('churn_risk') or 0) >= 15:
                    risks.append("Elevated churn risk")
            except Exception:
                pass
            try:
                if int(kpis[-1].get('open_tickets') or 0) >= 2:
                    risks.append("Multiple open tickets")
            except Exception:
                pass
        if any((t.get('priority') == 'High') and (t.get('status') in {'Open','Pending'}) for t in tickets):
            risks.append("High-priority ticket pending")
        risks_str = ", ".join(risks) if risks else "Not available"

        tp = []
        for it in interactions[:2]:
            note = (it or {}).get('notes')
            if note:
                tp.append(note)
        talking_points = "; ".join(tp)[:200] if tp else "Not available"

        refs = ", ".join((n or {}).get('source','') for n in notes) if notes else "Not available"

        brief = (
            f"Overview: {overview}\n"
            f"KPIs (last 3 months): {kpi_str}\n"
            f"Risks: {risks_str}\n"
            f"Talking points: {talking_points}\n"
            f"References: {refs}"
        )
        words = brief.split()
        return " ".join(words[:150]) if len(words) > 150 else brief
    except Exception:
        return "Agent stopped due to iteration limit or time limit."
