from __future__ import annotations
from pathlib import Path
import os
from typing import List, Dict, Optional

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from chromadb.config import Settings

VECTOR_DIR = "data/vectorstore"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Extra safeguard to silence telemetry on some Chroma versions
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

def load_vectorstore() -> Chroma:
    # Use embedding_function for langchain_community==0.2.x compatibility
    return Chroma(
        persist_directory=VECTOR_DIR,
        embedding_function=HuggingFaceEmbeddings(model_name=EMBED_MODEL),
        client_settings=Settings(anonymized_telemetry=False),
    )

def notes_search(query: str, k: int = 3, client_name: Optional[str] = None) -> List[Dict]:
    """Return top-k snippets with source; if client_name provided, bias by filename match."""
    vs = load_vectorstore()
    docs = vs.similarity_search(query, k=k*2)  # fetch extra to filter
    out = []
    seen_texts = set()
    for d in docs:
        src = d.metadata.get("source", "")
        if client_name:
            slug = client_name.lower().replace(" ", "_")
            if slug not in src.lower():
                continue
        excerpt = d.page_content.strip()
        if len(excerpt) > 350:
            excerpt = excerpt[:347] + "..."
        if excerpt in seen_texts:
            continue
        seen_texts.add(excerpt)
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
