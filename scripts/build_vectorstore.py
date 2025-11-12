from pathlib import Path
import os
import sys

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

NOTES_DIR = Path("data/meeting_notes")
PERSIST_DIR = Path(os.getenv("VECTORSTORE_DIR", "data/vectorstore"))
MODEL_NAME = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

def main():
    if not NOTES_DIR.exists():
        sys.exit(f"❌ Notes folder not found: {NOTES_DIR}")

    txt_files = sorted(NOTES_DIR.glob("*.txt"))
    if not txt_files:
        sys.exit(f"❌ No .txt files found in {NOTES_DIR}. Generate data first.")

    print(f"[vs] Reading {len(txt_files)} note files from {NOTES_DIR} ...")

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120)
    texts, metas = [], []
    for p in txt_files:
        raw = p.read_text(encoding="utf-8").strip()
        chunks = splitter.split_text(raw)
        texts.extend(chunks)
        metas.extend([{"source": str(p)}] * len(chunks))

    print(f"[vs] Total chunks: {len(texts)}")

    PERSIST_DIR.mkdir(parents=True, exist_ok=True)

    # Local, free embeddings
    embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME)
    vs = Chroma.from_texts(
        texts=texts,
        embedding_function=embeddings,
        metadatas=metas,
        persist_directory=str(PERSIST_DIR),
    )
    vs.persist()
    print(f"✅ Vector store built at {PERSIST_DIR.resolve()}")

if __name__ == "__main__":
    main()
