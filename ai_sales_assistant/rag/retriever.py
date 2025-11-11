from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Optional

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings  # LC 0.2 line

VECTOR_DIR = "data/vectorstore"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

def load_vectorstore() -> Chroma:
    return Chroma(
        persist_directory=VECTOR_DIR,
        embedding_function=HuggingFaceEmbeddings(model_name=EMBED_MODEL),
    )

def notes_search(query: str, k: int = 3, client_name: Optional[str] = None) -> List[Dict]:
    """Return top-k snippets with source; if client_name provided, bias by filename match."""
    vs = load_vectorstore()
    docs = vs.similarity_search(query, k=k*2)  # fetch extra to filter
    out = []
    for d in docs:
        src = d.metadata.get("source", "")
        if client_name:
            slug = client_name.lower().replace(" ", "_")
            if slug not in src.lower():
                continue
        excerpt = d.page_content.strip()
        if len(excerpt) > 350:
            excerpt = excerpt[:347] + "..."
        out.append({"text": excerpt, "source": Path(src).name})
        if len(out) >= k:
            break
    # Fallback: if filter removed all, return top-k unfiltered
    if not out:
        for d in docs[:k]:
            src = Path(d.metadata.get("source", "")).name
            excerpt = d.page_content.strip()
            if len(excerpt) > 350:
                excerpt = excerpt[:347] + "..."
            out.append({"text": excerpt, "source": src})
    return out
