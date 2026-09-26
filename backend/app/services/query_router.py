import logging
import re
from typing import Any

from app.core.mongodb import MongoDBManager
from app.services.gemini_provider import GeminiProvider
from app.services.mongo_validator import MongoQueryValidator
from app.services.registry_service import RegistryService
from app.services.schema_service import MongoSchemaService
from app.services.scope_resolver import QueryScope, ScopeResolver
from app.services.source_manager import SourceManager

logger = logging.getLogger("knowurdb.router")


class QueryRouter:
    """
    Intelligently routes a natural language question across MongoDB collections,
    platform metadata, and RAG documents:
      - PLATFORM (Platform-level scope: dataset count, source catalog, databases)
      - SINGLE_SOURCE (Collection or document query within 1 database)
      - MULTI_SOURCE (Comparison or cross-database aggregation)
      - DOCUMENT_RAG (PDF / TXT / Markdown vector search)
      - META (Legacy source listing)
      - CLARIFICATION (Ambiguity across datasets or fields)
      - UNRELATED (Off-topic question)
    """

    def __init__(self, ai_provider: GeminiProvider, source_manager: SourceManager):
        self.ai = ai_provider
        self.source_manager = source_manager
        self.schema_service = MongoSchemaService()
        self.registry_service = RegistryService()

    def route_query(
        self, question: str, explicit_source_ids: list[str] | None = None
    ) -> dict[str, Any]:
        # Validate safety first so malicious injections are caught immediately
        MongoQueryValidator.validate_question_safety(question)

        q = question.strip()
        q_lower = q.lower()
        q_words = set(re.sub(r"[^\w\s]", " ", q_lower).split())

        all_sources = self.source_manager.list_sources()
        sources = all_sources
        if explicit_source_ids:
            sources = [
                s
                for s in all_sources
                if s.source_id in explicit_source_ids
                or s.dataset_id in explicit_source_ids
                or s.database_name in explicit_source_ids
            ]

        is_all_sources = (
            explicit_source_ids is None
            or len(explicit_source_ids) > 1
            or (len(explicit_source_ids) == 1 and explicit_source_ids[0] in ("all", "all_sources"))
        )
        active_sid = MongoDBManager.get_active_source_id()

        # 1. SCOPE RESOLVER (Strict first-stage classification)
        scope_res = ScopeResolver.resolve_scope(
            q, active_source_id=active_sid, is_all_sources=is_all_sources
        )

        # 1A. PLATFORM SCOPE: Always PLATFORM, regardless of active source dropdown
        if scope_res.scope == QueryScope.PLATFORM:
            return {
                "decision": "PLATFORM",
                "intent": scope_res.intent,
                "sources": [],
                "candidates": [],
                "confidence": scope_res.confidence,
                "reasoning": scope_res.reason,
            }

        # 1B. UNRELATED: Always UNRELATED
        if scope_res.scope == QueryScope.UNRELATED:
            return {
                "decision": "UNRELATED",
                "sources": [],
                "candidates": [],
                "confidence": scope_res.confidence,
                "reasoning": scope_res.reason,
                "friendly_message": "I couldn't find relevant data for your question in the connected MongoDB collections or documents.",
            }

        # If there are no sources at all in the system:
        if not sources and not all_sources:
            return {
                "decision": "UNRELATED",
                "sources": [],
                "candidates": [],
                "confidence": 0.95,
                "reasoning": "No datasets or sources are connected.",
                "friendly_message": "There are no datasets in the collection right now, please upload a dataset or click 'Generate Random MongoDB Demo Dataset'.",
            }

        # 1C. DATASET SCOPE (e.g. "Tell me about this dataset", "how many collections do i have")
        if scope_res.scope == QueryScope.DATASET:
            # If user explicitly selected a source or there is only 1 tabular source:
            tabular_sources = [s for s in sources if s.detected_format not in ("pdf", "txt", "markdown")]
            if not is_all_sources and len(tabular_sources) == 1:
                chosen = tabular_sources[0]
                return {
                    "decision": "SINGLE_SOURCE",
                    "intent": scope_res.intent,
                    "sources": [
                        {
                            "source_id": chosen.source_id,
                            "name": chosen.name,
                            "type": chosen.detected_format,
                            "file_type": chosen.file_type,
                        }
                    ],
                    "candidates": [],
                    "confidence": scope_res.confidence,
                    "reasoning": f"Scope is DATASET targeting active dataset '{chosen.name}'.",
                }

            # If ALL SOURCES is active:
            registered_ds = self.registry_service.list_datasets()
            if len(registered_ds) == 1:
                d = registered_ds[0]
                return {
                    "decision": "SINGLE_SOURCE",
                    "intent": scope_res.intent,
                    "sources": [
                        {
                            "source_id": d["source_id"],
                            "name": d["display_name"],
                            "type": "mongodb",
                            "file_type": "mongodb",
                        }
                    ],
                    "candidates": [],
                    "confidence": 0.95,
                    "reasoning": f"Only one dataset registered ({d['display_name']}).",
                }

            # Multiple datasets exist and ALL SOURCES is active -> Ask dataset clarification!
            return {
                "decision": "CLARIFICATION",
                "clarification_type": "dataset",
                "sources": [],
                "candidates": [
                    {
                        "source_id": d.get("source_id") or d.get("dataset_id"),
                        "name": d.get("display_name") or d.get("name"),
                        "collection": d.get("display_name") or d.get("name"),
                        "document_count": d.get("document_count"),
                        "field_count": len(d.get("collections", [])),
                        "fields_preview": d.get("collections", [])[:5],
                        "description": d.get("description") or f"Domain: {d.get('domain', 'general')}",
                        "clarification_type": "dataset",
                    }
                    for d in registered_ds
                ],
                "confidence": 0.95,
                "reasoning": "Which dataset would you like an overview of?",
            }

        # 2. Check for DOCUMENT_RAG intent (PDF / TXT / Markdown sources)
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

        # 3. Check for MULTI_SOURCE comparison
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

        # 4. If explicit single source was selected by user, honor it
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

        # 4B. Check for Ambiguity across multiple user-uploaded sources with overlapping domain names
        # (e.g., 'sales_2024.csv' and 'sales_2025.csv' when asking 'What are the total sales?')
        non_demo_tabular = [s for s in tabular_sources if s.source_id != "demo-source-id"]
        candidate_pool = non_demo_tabular if len(non_demo_tabular) > 1 else tabular_sources

        if len(candidate_pool) > 1:
            explicitly_named = []
            overlapping_domain = []
            for s in candidate_pool:
                s_clean = re.sub(r"\.[a-z0-9]+$", "", s.name.lower())
                tokens = [t for t in re.split(r"[_\-\s]+", s_clean) if len(t) > 1]
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
                    "clarification_type": "dataset",
                    "sources": [],
                    "candidates": [
                        {"source_id": s.source_id, "name": s.name, "collection": s.name}
                        for s in overlapping_domain
                    ],
                    "confidence": 0.85,
                    "reasoning": "Multiple sources match the domain term without disambiguation.",
                }

        # 5. ALL SOURCES ACTIVE: Resolve Entity to Dataset via RegistryService
        if is_all_sources and len(tabular_sources) > 1:
            # Check if an entity in the query matches a specific dataset
            entity_candidates = []
            clean_tokens = [w for w in re.split(r"[^\w]+", q_lower) if len(w) > 2]
            # Try 2-grams and single tokens
            for i in range(len(clean_tokens) - 1):
                entity_candidates.append(f"{clean_tokens[i]}_{clean_tokens[i+1]}")
                entity_candidates.append(f"{clean_tokens[i]} {clean_tokens[i+1]}")
            entity_candidates.extend(clean_tokens)

            matched_datasets_map: dict[str, dict[str, Any]] = {}
            for cand in entity_candidates:
                if cand in ("how", "many", "what", "which", "show", "list", "total", "average", "highest", "lowest", "the", "are", "there", "has", "have", "with", "from", "for"):
                    continue
                matches = self.registry_service.find_datasets_matching_entity(cand)
                for m in matches:
                    m_id = m.get("source_id") or m.get("dataset_id")
                    if m_id not in matched_datasets_map:
                        matched_datasets_map[m_id] = m

            matched_datasets = list(matched_datasets_map.values())
            if len(matched_datasets) == 1:
                m_ds = matched_datasets[0]
                target_sid = m_ds.get("source_id") or m_ds.get("dataset_id")
                chosen = next((s for s in tabular_sources if s.source_id == target_sid), None)
                if chosen:
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
                        "reasoning": f"Uniquely matched entity to dataset '{chosen.name}'.",
                    }

            if len(matched_datasets) > 1:
                return {
                    "decision": "CLARIFICATION",
                    "clarification_type": "dataset",
                    "sources": [],
                    "candidates": [
                        {
                            "source_id": d.get("source_id") or d.get("dataset_id"),
                            "name": d.get("display_name") or d.get("name"),
                            "collection": d.get("display_name") or d.get("name"),
                            "document_count": d.get("document_count"),
                            "field_count": len(d.get("collections", [])),
                            "fields_preview": d.get("collections", [])[:5],
                            "description": d.get("description") or f"Domain: {d.get('domain', 'general')}",
                            "clarification_type": "dataset",
                        }
                        for d in matched_datasets
                    ],
                    "confidence": 0.90,
                    "reasoning": "Multiple datasets contain matching entities.",
                }

        # 6. Fallback: match by collection/field schema relevance or active_source_id
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

        if best_source is None:
            return {
                "decision": "UNRELATED",
                "sources": [],
                "candidates": [],
                "confidence": 0.90,
                "reasoning": "No relevant source found.",
                "friendly_message": "I couldn't find a matching dataset for your question.",
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
