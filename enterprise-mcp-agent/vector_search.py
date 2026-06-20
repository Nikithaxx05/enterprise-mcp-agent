from __future__ import annotations

import math
import re
from collections import Counter
from pathlib import Path
from typing import Any


TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return [token for token in TOKEN_RE.findall(text.lower()) if len(token) > 2]


class LocalVectorIndex:
    """Small local vector index with optional FAISS/Chroma-style interface.

    This keeps the project runnable without network calls or heavyweight installs. The
    class stores bag-of-words vectors in memory and exposes similarity search; it can be
    swapped for FAISS or Chroma in production without changing the MCP tool contract.
    """

    def __init__(self, documents_dir: Path):
        self.documents_dir = documents_dir
        self.items = self._load_items()
        self.idf = self._build_idf()
        self.vectors = [self._vectorize(item["snippet"]) for item in self.items]

    def _load_items(self) -> list[dict[str, str]]:
        items: list[dict[str, str]] = []
        for path in sorted(self.documents_dir.glob("*.txt")):
            text = path.read_text(encoding="utf-8")
            paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
            for index, paragraph in enumerate(paragraphs, start=1):
                items.append({"document": path.name, "chunk_id": f"{path.stem}-{index}", "snippet": paragraph[:900]})
        return items

    def _build_idf(self) -> dict[str, float]:
        doc_count = max(len(self.items), 1)
        document_frequency: Counter[str] = Counter()
        for item in self.items:
            document_frequency.update(set(tokenize(item["snippet"])))
        return {
            term: math.log((doc_count + 1) / (frequency + 1)) + 1
            for term, frequency in document_frequency.items()
        }

    def _vectorize(self, text: str) -> dict[str, float]:
        counts = Counter(tokenize(text))
        return {term: count * self.idf.get(term, 1.0) for term, count in counts.items()}

    @staticmethod
    def _cosine(left: dict[str, float], right: dict[str, float]) -> float:
        if not left or not right:
            return 0.0
        dot = sum(value * right.get(term, 0.0) for term, value in left.items())
        left_norm = math.sqrt(sum(value * value for value in left.values()))
        right_norm = math.sqrt(sum(value * value for value in right.values()))
        if not left_norm or not right_norm:
            return 0.0
        return dot / (left_norm * right_norm)

    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        query_vector = self._vectorize(query)
        scored = []
        for item, vector in zip(self.items, self.vectors):
            score = self._cosine(query_vector, vector)
            if score > 0:
                scored.append({**item, "score": round(score, 3)})
        return sorted(scored, key=lambda row: row["score"], reverse=True)[:limit]
