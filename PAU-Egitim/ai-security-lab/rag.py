"""Tiny keyword-overlap RAG retriever for the lab."""

from __future__ import annotations

import re
from pathlib import Path


def load_documents(data_dir: str = "data") -> list[dict[str, str | int]]:
    """Load .txt documents from the data directory."""
    documents: list[dict[str, str | int]] = []
    for path in sorted(Path(data_dir).glob("*.txt")):
        documents.append({"source": path.name, "content": path.read_text(encoding="utf-8"), "score": 0})
    return documents


def retrieve_context(query: str, top_k: int = 2) -> str:
    """Return the highest-scoring documents using simple keyword overlap."""
    documents = load_documents()
    query_terms = _tokenize(query)
    scored_documents: list[dict[str, str | int]] = []

    for document in documents:
        content = str(document["content"])
        doc_terms = _tokenize(content)
        score = len(query_terms.intersection(doc_terms))
        scored_documents.append({**document, "score": score})

    selected = sorted(scored_documents, key=lambda item: int(item["score"]), reverse=True)[:top_k]
    if not selected:
        return "No context found."

    return "\n\n".join(
        f"[source: {doc['source']} | score: {doc['score']}]\n{doc['content']}" for doc in selected
    )


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"\b[\wçğıöşüÇĞİÖŞÜ]+\b", text.lower()))
