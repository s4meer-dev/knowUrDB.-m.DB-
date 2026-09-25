import logging
import re
from typing import Any

from app.services.gemini_provider import GeminiProvider
from app.services.mongo_validator import MongoQueryValidator
from app.services.schema_service import MongoSchemaService
from app.services.source_manager import SourceManager

logger = logging.getLogger("knowurdb.router")


class QueryRouter:
    """
    Intelligently routes a natural language question across MongoDB collections and RAG documents:
      - SINGLE_SOURCE
      - MULTI_SOURCE
      - DOCUMENT_RAG
      - META
      - CLARIFICATION
      - UNRELATED
    """

    def __init__(self, ai_provider: GeminiProvider, source_manager: SourceManager):
        self.ai = ai_provider
        self.source_manager = source_manager
        self.schema_service = MongoSchemaService()

    def route_query(
        self, question: str, explicit_source_ids: list[str] | None = None
    ) -> dict[str, Any]:
        # Validate safety first so malicious injections are caught immediately
        MongoQueryValidator.validate_question_safety(question)

        all_sources = self.source_manager.list_sources()
        sources = all_sources
        if explicit_source_ids:
            sources = [s for s in all_sources if s.source_id in explicit_source_ids]

        q = question.strip()
        q_lower = q.lower()
        q_words = set(re.sub(r"[^\w\s]", " ", q_lower).split())

        # 1. Check for META questions ("What files have I uploaded?", "What sources are available?")
        if re.search(
            r"\b(what|which|list|show)\b.*\b(files|sources|uploaded|datasets in my collection|available sources)\b",
            q_lower,
        ):
            return {
                "decision": "META",
                "sources": [],
                "candidates": [],
                "confidence": 0.98,
                "reasoning": "User asked about available uploaded sources/collections.",
            }

        # 2. Check for explicit off-topic / UNRELATED questions
        unrelated_patterns = (
            "weather",
            "write a poem",
            "tell me a joke",
            "capital of france",
            "who is the president",
            "recipe for",
            "2+2",
            "2 + 2",
        )
        if any(p in q_lower for p in unrelated_patterns) or not sources:
            return {
                "decision": "UNRELATED",
                "sources": [],
                "candidates": [],
                "confidence": 0.95,
                "reasoning": "Question is unrelated to any uploaded MongoDB collection or document.",
                "friendly_message": (
                    "There are no datasets in the collection right now, please upload a dataset."
                    if not sources
                    else "I couldn't find relevant data for your question in the connected MongoDB collections or documents."
                ),
            }

        # If user explicitly restricted to specific source(s), honor that directly
        if explicit_source_ids and len(sources) == 1:
            s = sources[0]
            decision_type = (
                "DOCUMENT_RAG"
                if s.detected_format in ("pdf", "txt", "markdown")
                else "SINGLE_SOURCE"
            )
            return {
                "decision": decision_type,
                "sources": [
                    {
                        "source_id": s.source_id,
                        "name": s.name,
                        "type": s.detected_format,
                        "file_type": s.file_type,
                    }
                ],
                "candidates": [],
                "confidence": 1.0,
                "reasoning": "User explicitly selected source.",
            }

        # 3. Check for DOCUMENT_RAG intent (PDF / TXT / Markdown sources)
        doc_sources = [s for s in sources if s.detected_format in ("pdf", "txt", "markdown")]
        tabular_sources = [s for s in sources if s.detected_format not in ("pdf", "txt", "markdown")]

        if doc_sources:
            doc_keywords = {"document", "pdf", "policy", "refund", "clause", "article", "page", "paragraph", "handbook", "manual", "terms"}
            matched_doc_sources = []
            for ds in doc_sources:
                stem = re.sub(r"[^\w\s]", " ", ds.name.lower()).split()
                if any(w in q_lower for w in stem if len(w) > 2) or q_words.intersection(doc_keywords):
                    matched_doc_sources.append(ds)

            if matched_doc_sources:
                chosen = matched_doc_sources[0]
                return {
                    "decision": "DOCUMENT_RAG",
                    "sources": [
                        {
                            "source_id": chosen.source_id,
                            "name": chosen.name,
                            "type": chosen.detected_format,
                            "file_type": chosen.file_type,
                        }
                    ],
                    "candidates": [],
                    "confidence": 0.95,
                    "reasoning": "Question targets unstructured document / policy content via MongoDB Vector RAG.",
                }

        # 4. Check for MULTI_SOURCE comparison ("compare ... across all", "from two uploaded datasets", "between 2024 and 2025")
        if len(tabular_sources) > 1 and re.search(
            r"\b(compare\s+.*(?:datasets|sources|collections|2024|2025|q1|q2)|across\s+all|all\s+sources|describe\s+all)\b",
            q_lower,
        ):
            return {
                "decision": "MULTI_SOURCE",
                "sources": [
                    {
                        "source_id": s.source_id,
                        "name": s.name,
                        "type": s.detected_format,
                        "file_type": s.file_type,
                    }
                    for s in tabular_sources
                ],
                "candidates": [],
                "confidence": 0.92,
                "reasoning": "Question compares or aggregates across multiple MongoDB sources.",
            }

        # 5. Check for Ambiguity / CLARIFICATION across multiple user-uploaded sources with overlapping domain names
        # (e.g., 'sales_2024.csv' and 'sales_2025.csv' when asking 'What are the total sales?')
        non_demo_tabular = [s for s in tabular_sources if s.source_id != "demo-source-id"]
        candidate_Pool = non_demo_tabular if len(non_demo_tabular) > 1 else tabular_sources

        if len(candidate_Pool) > 1:
            explicitly_named = []
            overlapping_domain = []
            for s in candidate_Pool:
                s_clean = re.sub(r"\.[a-z0-9]+$", "", s.name.lower())
                tokens = [t for t in re.split(r"[_\-\s]+", s_clean) if len(t) > 1]
                # Did the user mention the exact distinguishing token (e.g. '2024' vs '2025' or full filename)?
                if s_clean in q_lower or all(t in q_lower for t in tokens):
                    explicitly_named.append(s)
                elif any(t in q_lower for t in tokens if len(t) > 2):
                    overlapping_domain.append(s)

            if len(explicitly_named) == 1:
                chosen = explicitly_named[0]
                return {
                    "decision": "SINGLE_SOURCE",
                    "sources": [
                        {
                            "source_id": chosen.source_id,
                            "name": chosen.name,
                            "type": chosen.detected_format,
                            "file_type": chosen.file_type,
                        }
                    ],
                    "candidates": [],
                    "confidence": 0.95,
                    "reasoning": f"Matched specific source '{chosen.name}'.",
                }

            if len(overlapping_domain) > 1 and not explicitly_named:
                return {
                    "decision": "CLARIFICATION",
                    "sources": [],
                    "candidates": [
                        {"source_id": s.source_id, "name": s.name}
                        for s in overlapping_domain
                    ],
                    "confidence": 0.85,
                    "reasoning": "Multiple sources match the domain term without disambiguation.",
                }

        # 6. Match Single Source by collection/field schema relevance, honoring active_source_id
        from app.core.mongodb import MongoDBManager

        active_sid = MongoDBManager.get_active_source_id()
        best_source = None
        best_score = -1
        for s in tabular_sources:
            score = 0
            s_clean = s.name.lower()
            if any(w in s_clean for w in q_words if len(w) > 3):
                score += 5
            for col_name in s.collections or []:
                base_col = col_name.split("_")[-1].lower()
                if base_col in q_lower or base_col.rstrip("s") in q_lower:
                    score += 10
            if s.schema_summary and any(w in str(s.schema_summary).lower() for w in q_words if len(w) > 3):
                score += 3
            if s.source_id == active_sid:
                score += 8
            elif s.source_id != "demo-source-id" and score > 0:
                score += 2
            if score > best_score:
                best_score = score
                best_source = s

        if best_source is None and tabular_sources:
            best_source = next(
                (s for s in tabular_sources if s.source_id == active_sid),
                tabular_sources[0],
            )


        if best_source is None and doc_sources:
            best_source = doc_sources[0]
            return {
                "decision": "DOCUMENT_RAG",
                "sources": [
                    {
                        "source_id": best_source.source_id,
                        "name": best_source.name,
                        "type": best_source.detected_format,
                        "file_type": best_source.file_type,
                    }
                ],
                "candidates": [],
                "confidence": 0.8,
                "reasoning": "Routed to document source.",
            }

        return {
            "decision": "SINGLE_SOURCE",
            "sources": [
                {
                    "source_id": best_source.source_id,
                    "name": best_source.name,
                    "type": best_source.detected_format,
                    "file_type": best_source.file_type,
                }
            ],
            "candidates": [],
            "confidence": 0.9,
            "reasoning": f"Selected optimal MongoDB source '{best_source.name}'.",
        }
