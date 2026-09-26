import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.services.intent_classifier import QuestionNormalizer


class QueryScope(str, Enum):
    PLATFORM = "platform"
    DATASET = "dataset"
    COLLECTION = "collection"
    DOCUMENT = "document"
    UNRELATED = "unrelated"


@dataclass
class ScopeResolutionResult:
    scope: QueryScope
    intent: str
    confidence: float
    reason: str
    target_entity: str | None = None
    target_field: str | None = None
    matched_keywords: list[str] = field(default_factory=list)


class ScopeResolver:
    """
    First-Stage Scope & Intent Classifier for KnowUrDB.
    Determines WHAT LEVEL of the data hierarchy the user is querying before
    any collection resolution or MongoDB execution takes place:
      - PLATFORM: KnowUrDB system, dataset count, source catalog, database list
      - DATASET: One complete dataset overview, collection counts in dataset, schema
      - COLLECTION: Entities, collections, record lists, aggregations across collection
      - DOCUMENT: Specific document lookup, field analysis, maximum/minimum record
      - UNRELATED: Off-topic questions (weather, poems, math puzzles)
    """

    UNRELATED_PATTERNS = (
        r"\bweather\b",
        r"\bwrite a poem\b",
        r"\btell me a joke\b",
        r"\bcapital of france\b",
        r"\bwho is the president\b",
        r"\brecipe for\b",
        r"\b2\s*\+\s*2\b",
        r"\btranslate to\b",
        r"\bhow to cook\b",
        r"\bwho won the\b",
    )

    PLATFORM_COUNT_PATTERNS = (
        r"\bhow many\s+(?:total\s+)?(?:datasets?|databases?|sources?|dbs?)\b",
        r"\bhow much\s+(?:datasets?|databases?)\b",
        r"\b(?:count|number of|total)\s+(?:datasets?|databases?|sources?|dbs?)\b",
        r"\bgive\s+(?:me\s+)?(?:total\s+)?(?:datasets?|databases?)\b",
        r"\btell\s+(?:me\s+)?(?:the\s+)?number of\s+(?:datasets?|databases?)\b",
    )

    PLATFORM_LIST_PATTERNS = (
        r"\b(?:show|list|display|view)\s+(?:all\s+)?(?:datasets?|databases?|sources?|dbs?)\b",
        r"\bwhat\s+(?:datasets?|databases?|sources?)\s+(?:are\s+)?(?:available|connected|present|registered)\b",
        r"\bwhich\s+(?:datasets?|databases?|sources?)\s+(?:are\s+)?(?:available|connected|present)\b",
        r"\bwhat\s+(?:datasets?|databases?)\s+do\s+i\s+have\b",
        r"\bavailable\s+(?:datasets?|databases?|sources?)\b",
        r"\ball\s+(?:datasets?|databases?)\b",
        r"\bshow\s+(?:all\s+)?available\s+sources\b",
        r"\bwhat\s+files\s+(?:have\s+i\s+)?uploaded\b",
        r"\bconnected\s+sources\b",
    )

    PLATFORM_ACTIVE_PATTERNS = (
        r"\bwhat\s+is\s+(?:the\s+)?active\s+(?:dataset|database|source)\b",
        r"\bactive\s+(?:dataset|database|source)\b",
        r"\bcurrent\s+(?:dataset|database|source)\b",
    )

    PLATFORM_GENERATION_PATTERNS = (
        r"\bhow many\s+datasets?\s+have\s+i\s+generated\b",
        r"\bgeneration\s+history\b",
        r"\blist\s+generations\b",
    )

    DATASET_OVERVIEW_PATTERNS = (
        r"\b(?:tell\s+me\s+about|give\s+me\s+info(?:rmation)?\s+about|overview\s+of|describe)\s+(?:this|the|selected)?\s*(?:dataset|database)\b",
        r"\bdataset\s+overview\b",
        r"\bdatabase\s+overview\b",
        r"\bwhat\s+type\s+of\s+data\s+does\s+this\s+dataset\s+contain\b",
    )

    DATASET_COLLECTION_COUNT_PATTERNS = (
        r"\bhow many\s+(?:total\s+)?collections?\b",
        r"\bcount\s+collections?\b",
        r"\bnumber of\s+collections?\b",
    )

    DATASET_COLLECTION_LIST_PATTERNS = (
        r"\b(?:what|which|show|list)\s+collections?\b",
        r"\bavailable\s+collections?\b",
    )

    DATASET_SCHEMA_PATTERNS = (
        r"\b(?:show|what\s+is\s+the|give\s+me\s+the)\s+schema\s+(?:of\s+this\s+dataset|of\s+this\s+database)?\b",
        r"\bschema\s+of\s+(?:this\s+)?(?:dataset|database)\b",
    )

    @classmethod
    def resolve_scope(
        cls,
        question: str,
        active_source_id: str | None = None,
        is_all_sources: bool = True,
    ) -> ScopeResolutionResult:
        normalized = QuestionNormalizer.normalize(question)
        q_lower = normalized.lower().strip()

        # 1. Unrelated check
        for pat in cls.UNRELATED_PATTERNS:
            if re.search(pat, q_lower):
                return ScopeResolutionResult(
                    scope=QueryScope.UNRELATED,
                    intent="UNRELATED",
                    confidence=0.98,
                    reason="Question is unrelated to KnowUrDB datasets or database queries.",
                )

        # 2. Check for PLATFORM Scope
        # Check generation history first so 'how many datasets have i generated' matches generations
        for pat in cls.PLATFORM_GENERATION_PATTERNS:
            if re.search(pat, q_lower):
                return ScopeResolutionResult(
                    scope=QueryScope.PLATFORM,
                    intent="META_GENERATIONS",
                    confidence=0.95,
                    reason="Question asks about generated dataset history.",
                )

        # Crucial: Asking for dataset count or listing datasets is PLATFORM scope
        # even if a specific dataset is selected (Section 101, 102).
        for pat in cls.PLATFORM_COUNT_PATTERNS:
            if re.search(pat, q_lower):
                return ScopeResolutionResult(
                    scope=QueryScope.PLATFORM,
                    intent="META_COUNT_DATASETS",
                    confidence=0.99,
                    reason="Question asks for the total count of registered KnowUrDB datasets.",
                )

        for pat in cls.PLATFORM_LIST_PATTERNS:
            if re.search(pat, q_lower):
                return ScopeResolutionResult(
                    scope=QueryScope.PLATFORM,
                    intent="META_LIST_DATASETS",
                    confidence=0.98,
                    reason="Question asks to view/list all registered KnowUrDB datasets or sources.",
                )

        for pat in cls.PLATFORM_ACTIVE_PATTERNS:
            if re.search(pat, q_lower):
                return ScopeResolutionResult(
                    scope=QueryScope.PLATFORM,
                    intent="META_ACTIVE_DATASET",
                    confidence=0.95,
                    reason="Question asks for the currently active dataset/source.",
                )

        if re.search(r"\binfo(?:rmation)?\s+about\s+all\s+datasets\b", q_lower):
            return ScopeResolutionResult(
                scope=QueryScope.PLATFORM,
                intent="META_DATASET_OVERVIEW_ALL",
                confidence=0.97,
                reason="Question asks for an overview of all datasets across KnowUrDB.",
            )

        # 3. Check for DATASET Scope
        for pat in cls.DATASET_OVERVIEW_PATTERNS:
            if re.search(pat, q_lower):
                return ScopeResolutionResult(
                    scope=QueryScope.DATASET,
                    intent="META_DATASET_OVERVIEW",
                    confidence=0.95,
                    reason="Question asks for an overview of the selected dataset.",
                )

        for pat in cls.DATASET_COLLECTION_COUNT_PATTERNS:
            if re.search(pat, q_lower):
                return ScopeResolutionResult(
                    scope=QueryScope.DATASET,
                    intent="META_COUNT_COLLECTIONS",
                    confidence=0.96,
                    reason="Question asks to count collections within the dataset.",
                )

        for pat in cls.DATASET_COLLECTION_LIST_PATTERNS:
            if re.search(pat, q_lower):
                return ScopeResolutionResult(
                    scope=QueryScope.DATASET,
                    intent="META_LIST_COLLECTIONS",
                    confidence=0.96,
                    reason="Question asks to list collections within the dataset.",
                )

        for pat in cls.DATASET_SCHEMA_PATTERNS:
            if re.search(pat, q_lower):
                return ScopeResolutionResult(
                    scope=QueryScope.DATASET,
                    intent="META_SCHEMA",
                    confidence=0.95,
                    reason="Question asks for schema information of the dataset.",
                )

        # 4. Check for DOCUMENT / FIELD Scope (Targeted record lookup or specific metric)
        if re.search(r"\b(?:who\s+has\s+the\s+highest|which\s+.*is\s+(?:the\s+)?(?:highest|most\s+expensive|largest|cheapest|lowest))\b", q_lower):
            return ScopeResolutionResult(
                scope=QueryScope.DOCUMENT,
                intent="MAXIMUM" if not re.search(r"\b(?:cheapest|lowest)\b", q_lower) else "MINIMUM",
                confidence=0.92,
                reason="Question asks for a single winning record by extreme metric value.",
            )

        if re.search(r"\b(?:show|get|find|details\s+of)\s+[A-Za-z]+\s+[A-Z0-9_-]{3,}\b", q_lower):
            return ScopeResolutionResult(
                scope=QueryScope.DOCUMENT,
                intent="DETAIL",
                confidence=0.90,
                reason="Question asks to lookup a specific record by identifier.",
            )

        # 5. Default to COLLECTION Scope (standard analytical or data querying)
        # Determine likely intent from action verbs
        if re.search(r"\b(how many|count|number of)\b", q_lower):
            inferred_intent = "COUNT"
        elif re.search(r"\b(total|sum|combined)\b", q_lower):
            inferred_intent = "SUM"
        elif re.search(r"\b(average|mean|avg)\b", q_lower):
            inferred_intent = "AVERAGE"
        elif re.search(r"\b(top\s+\d+|bottom\s+\d+|highest\s+\d+)\b", q_lower):
            inferred_intent = "TOP_N"
        elif re.search(r"\b(compare|versus|difference\s+between)\b", q_lower):
            inferred_intent = "COMPARE"
        elif re.search(r"\b(by|per|for\s+each)\s+[a-z_]+\b", q_lower) and not q_lower.startswith("show"):
            inferred_intent = "GROUP_BY"
        elif re.search(r"\b(show|list|display|find|get)\b", q_lower):
            inferred_intent = "FILTER"
        else:
            inferred_intent = "FILTER"

        return ScopeResolutionResult(
            scope=QueryScope.COLLECTION,
            intent=inferred_intent,
            confidence=0.90,
            reason="Question queries data collections or records.",
        )
