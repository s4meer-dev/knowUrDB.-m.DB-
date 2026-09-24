import datetime
import hashlib
import math
import os
import re
import uuid
from pathlib import Path
from typing import Any

import PyPDF2

from app.core.mongodb import MongoDBManager


def _compute_vector_embedding(text: str, dim: int = 128) -> list[float]:
    """
    Computes a normalized L2 dense vector embedding (dim=128) using token + trigram
    feature hashing so MongoDB cosine vector search works deterministically with zero latency.
    """
    vec = [0.0] * dim
    clean = re.sub(r"[^\w\s]", " ", text.lower())
    tokens = [t for t in clean.split() if len(t) > 1]
    if not tokens:
        return vec

    features: list[tuple[str, float]] = []
    for tok in tokens:
        features.append((tok, 2.0))
        if len(tok) >= 4:
            for i in range(len(tok) - 2):
                features.append((tok[i : i + 3], 0.75))

    for feat, weight in features:
        h = int(hashlib.md5(feat.encode("utf-8")).hexdigest()[:8], 16)
        idx = h % dim
        sign = 1.0 if (h & 1) == 0 else -1.0
        vec[idx] += sign * weight

    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [round(x / norm, 6) for x in vec]
    return vec


def _cosine_similarity(v1: list[float], v2: list[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    return sum(a * b for a, b in zip(v1, v2))


class DocumentProcessor:
    """
    MongoDB-native Document & RAG Pipeline:
    UPLOAD -> TEXT EXTRACTION -> CLEANING -> CHUNKING -> VECTOR EMBEDDING ->
    MONGODB STORAGE (_sys_document_chunks) -> HYBRID VECTOR RETRIEVAL -> LLM SYNTHESIS
    """

    def __init__(self, ai_provider: Any = None):
        self.ai = ai_provider

    def ingest_document(
        self, source_id: str, file_path: str, filename: str
    ) -> dict[str, Any]:
        db = MongoDBManager.get_db()
        db[MongoDBManager.SYS_DOCUMENT_CHUNKS].delete_many({"source_id": source_id})

        pages = self._extract_pages(file_path, filename)
        chunk_docs: list[dict[str, Any]] = []
        now_iso = datetime.datetime.now(datetime.UTC).isoformat()

        for page_num, page_text in pages:
            chunks = self._chunk_text(page_text, chunk_size=550, overlap=80)
            for idx, chunk_str in enumerate(chunks):
                embedding = _compute_vector_embedding(chunk_str)
                chunk_docs.append(
                    {
                        "chunk_id": f"{source_id}_p{page_num}_c{idx}_{uuid.uuid4().hex[:6]}",
                        "source_id": source_id,
                        "filename": filename,
                        "page_number": page_num,
                        "text": chunk_str,
                        "embedding": embedding,
                        "created_at": now_iso,
                    }
                )

        if chunk_docs:
            db[MongoDBManager.SYS_DOCUMENT_CHUNKS].insert_many(chunk_docs)

        return {
            "chunk_count": len(chunk_docs),
            "page_count": len(pages),
        }

    def _extract_pages(self, file_path: str, filename: str) -> list[tuple[int, str]]:
        ext = os.path.splitext(filename)[1].lower()
        pages: list[tuple[int, str]] = []
        path_obj = Path(file_path)
        if not path_obj.exists():
            return pages

        if ext == ".pdf":
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for idx, page in enumerate(reader.pages, start=1):
                    txt = page.extract_text() or ""
                    txt = re.sub(r"\s+", " ", txt).strip()
                    if txt:
                        pages.append((idx, txt))
        else:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            paragraphs = [p.strip() for p in re.split(r"\n\s*\n", content) if p.strip()]
            if not paragraphs and content.strip():
                paragraphs = [content.strip()]
            for idx, para in enumerate(paragraphs, start=1):
                pages.append((idx, para))

        return pages

    def _chunk_text(
        self, text: str, chunk_size: int = 550, overlap: int = 80
    ) -> list[str]:
        text = text.strip()
        if not text:
            return []
        if len(text) <= chunk_size:
            return [text]
        chunks: list[str] = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunks.append(text[start:end].strip())
            if end >= len(text):
                break
            start = max(end - overlap, start + 1)
        return chunks

    def search(
        self, query: str, source_or_path: str, top_k: int = 4
    ) -> list[dict[str, Any]]:
        """
        Retrieves the most relevant document chunks from MongoDB using hybrid
        Vector Similarity + Lexical Relevance scoring.
        """
        db = MongoDBManager.get_db()

        # Resolve source_id
        chunks = list(
            db[MongoDBManager.SYS_DOCUMENT_CHUNKS].find({"source_id": source_or_path})
        )
        if not chunks:
            # Check if source_or_path is a storage_location or file path
            src = db[MongoDBManager.SYS_SOURCES].find_one(
                {
                    "$or": [
                        {"source_id": source_or_path},
                        {"storage_location": source_or_path},
                    ]
                }
            )
            if src:
                chunks = list(
                    db[MongoDBManager.SYS_DOCUMENT_CHUNKS].find(
                        {"source_id": src["source_id"]}
                    )
                )
            if not chunks and Path(source_or_path).exists():
                self.ingest_document(
                    source_id=source_or_path,
                    file_path=source_or_path,
                    filename=Path(source_or_path).name,
                )
                chunks = list(
                    db[MongoDBManager.SYS_DOCUMENT_CHUNKS].find(
                        {"source_id": source_or_path}
                    )
                )

        if not chunks:
            return []

        q_vec = _compute_vector_embedding(query)
        q_words = {
            w
            for w in re.sub(r"[^\w\s]", " ", query.lower()).split()
            if len(w) > 2
            and w
            not in {
                "what",
                "does",
                "the",
                "say",
                "about",
                "from",
                "document",
                "file",
                "which",
                "where",
                "how",
            }
        }

        scored: list[dict[str, Any]] = []
        for ch in chunks:
            c_vec = ch.get("embedding") or _compute_vector_embedding(ch.get("text", ""))
            vec_score = _cosine_similarity(q_vec, c_vec)

            text_lower = ch.get("text", "").lower()
            lexical_hits = sum(1 for w in q_words if w in text_lower)
            lexical_score = (lexical_hits / max(len(q_words), 1)) if q_words else 0.0

            combined_score = (0.55 * vec_score) + (0.45 * lexical_score)
            if combined_score > 0.08 or lexical_hits > 0:
                scored.append(
                    {
                        "chunk_id": ch.get("chunk_id"),
                        "text": ch.get("text", ""),
                        "page_number": ch.get("page_number", 1),
                        "score": round(combined_score, 4),
                    }
                )

        if not scored and chunks:
            # If the user asks a broad question like "Summarize this document", return first top_k chunks
            if any(
                k in query.lower()
                for k in ("summarize", "summary", "overview", "what is", "describe", "about", "content")
            ):
                return [
                    {
                        "chunk_id": ch.get("chunk_id"),
                        "text": ch.get("text", ""),
                        "page_number": ch.get("page_number", 1),
                        "score": 0.5,
                    }
                    for ch in chunks[:top_k]
                ]

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]
