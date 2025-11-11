from __future__ import annotations
from typing import Optional, List, Dict
from langchain.tools import StructuredTool
from ai_sales_assistant.rag.retriever import notes_search as _search

def _notes(query: str, k: int = 3, client_name: Optional[str] = None) -> List[Dict]:
    return _search(query=query, k=k, client_name=client_name)

notes_search_tool = StructuredTool.from_function(
    func=_notes,
    name="notes_search",
    description="Semantic search over meeting notes; returns short snippets with sources.",
)
