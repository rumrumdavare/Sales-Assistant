from __future__ import annotations
from typing import Optional, List, Dict, Union
from langchain.tools import StructuredTool
from ai_sales_assistant.rag.retriever import notes_search as _search

USED: set[str] = set()

def reset_used() -> None:
    USED.clear()

def _notes(query: Optional[str] = None, k: int = 3, client_name: Optional[str] = None) -> Union[List[Dict], str]:
    """Semantic notes search. If query is empty, fall back to client_name or a generic query."""
    if "notes_search" in USED:
        return "Already called notes_search; do not call again."
    USED.add("notes_search")
    
    q = (query or client_name or "").strip() or "account review"
    res = _search(query=q, k=k, client_name=client_name)
    return res if res else f"No relevant notes found for '{client_name or q}'."

notes_search_tool = StructuredTool.from_function(
    func=_notes,
    name="notes_search",
    description="Semantic search over meeting notes; returns short snippets with sources.",
)
