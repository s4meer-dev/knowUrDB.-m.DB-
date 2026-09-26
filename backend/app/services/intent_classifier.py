import re
from dataclasses import dataclass, field
from typing import Any

from app.services.dataset_intelligence import (
    CollectionIntelligenceService,
    CollectionResolver,
    DatasetIntelligenceService,
)
from app.services.semantic_field_registry import SemanticConcept, SemanticFieldRegistry
from app.services.semantic_filter_extractor import SemanticFilterExtractor, StructuredFilter

CANONICAL_INTENTS = {
    "DATASET_OVERVIEW",
    "COLLECTION_OVERVIEW",
    "COUNT",
    "LIST_RECORDS",
    "SEARCH",
    "FILTER",
    "SORT",
    "TOP_N",
    "BOTTOM_N",
    "AGGREGATION",
    "SUM",
    "AVERAGE",
    "MINIMUM",
    "MAXIMUM",
    "GROUP_BY",
    "COMPARISON",
    "TREND",
    "DISTRIBUTION",
    "DISTINCT_VALUES",
    "RECORD_DETAILS",
    "SCHEMA_QUERY",
    "METADATA_QUERY",
    "MULTI_COLLECTION",
    "DOCUMENT_RAG",
    "MULTI_SOURCE",
    "CLARIFICATION",
    "METRIC_UNAVAILABLE",
    "METRIC_ALTERNATIVE",
    "FIELD_NOT_AVAILABLE",
    "NO_MATCHING_RECORDS",
    "SCOPE_CONTEXT",
    "UNRELATED",
}

TYPO_CORRECTIONS: dict[str, str] = {
    "prodcut": "product",
    "prodcuts": "products",
    "porduct": "product",
    "porducts": "products",
    "prduct": "product",
    "prducts": "products",
    "custmer": "customer",
    "custmers": "customers",
    "costumer": "customer",
    "costumers": "customers",
    "cusotmer": "customer",
    "employe": "employee",
    "employes": "employees",
    "emplyee": "employee",
    "studnt": "student",
    "studnts": "students",
    "stduent": "student",
    "ordr": "order",
    "ordrs": "orders",
    "colection": "collection",
    "colections": "collections",
    "colletion": "collection",
    "colletions": "collections",
    "collcetion": "collection",
    "databse": "database",
    "datbase": "database",
    "datset": "dataset",
    "datsets": "datasets",
    "dataest": "dataset",
    "recrod": "record",
    "recrods": "records",
    "avergae": "average",
    "avarage": "average",
    "expensve": "expensive",
    "catgory": "category",
    "salry": "salary",
    "departmnt": "department",
    "banglore": "bangalore",
    "revene": "revenue",
    "revnue": "revenue",
    "reveneu": "revenue",
    "revenuee": "revenue",
    "reveue": "revenue",
    "spnding": "spending",
    "spnd": "spend",
}

SEMANTIC_FIELD_SYNONYMS: dict[str, list[str]] = {
    "expensive": ["price", "amount", "total_amount", "salary"],
    "cheap": ["price", "amount"],
    "cheapest": ["price", "amount"],
    "cost": ["price", "amount"],
    "price": ["price", "unit_price"],
    "revenue": ["revenue", "total_revenue", "sales_amount", "order_total", "total_amount"],
    "sales": ["sales", "sales_amount", "total_amount", "revenue"],
    "selling": ["total_amount", "amount"],
    "sold": ["units_sold"],
    "stock": ["stock", "inventory", "quantity"],
    "inventory": ["stock", "quantity"],
    "spent": ["total_spent", "amount_spent"],
    "spending": ["total_spent", "amount_spent"],
    "spend": ["total_spent", "amount_spent"],
    "salary": ["salary", "compensation"],
    "paid": ["salary", "total_spent"],
    "earner": ["salary"],
    "gpa": ["gpa", "Attendance_Percentage", "score", "rating"],
    "grade": ["gpa", "score"],
    "attendance": ["Attendance_Percentage"],
    "rating": ["rating", "performance_score", "gpa"],
    "performance": ["performance_score", "rating"],
    "city": ["address.city", "city"],
    "state": ["address.state", "state"],
    "email": ["contact.email", "email"],
    "phone": ["contact.phone", "phone"],
    "department": ["department", "role", "category"],
    "category": ["category", "department", "major", "status", "loyalty_tier", "tier"],
    "major": ["major", "department"],
}


@dataclass
class QueryPlan:
    original_question: str = ""
    normalized_question: str = ""
    intent: str = "FILTER"
    confidence: float = 0.95
    source_id: str | None = None
    source_name: str | None = None
    collection: str | None = None
    secondary_collection: str | None = None
    collection_status: str = "resolved"
    candidate_collections: list[dict[str, Any]] = field(default_factory=list)
    target_fields: list[str] = field(default_factory=list)
    metric_field: str | None = None
    secondary_metric_field: str | None = None
    group_field: str | None = None
    filters: dict[str, Any] = field(default_factory=dict)
    filter_descriptions: list[str] = field(default_factory=list)
    sort: dict[str, int] | None = None
    limit: int = 50
    operation: str = "aggregate"
    aggregation_op: str | None = None
    presentation_type: str = "table"
    clarification_message: str | None = None
    clarification_options: list[dict[str, Any]] = field(default_factory=list)
    requested_concept: str | None = None
    explanation: str | None = None
    requested_filters: list[dict[str, Any]] = field(default_factory=list)
    missing_filter_field: str | None = None
    available_fields: list[str] = field(default_factory=list)


class QuestionNormalizer:
    """Normalizes natural language questions, fixes common typos, and preserves user intent."""

    @staticmethod
    def normalize(question: str) -> str:
        if not question:
            return ""
        text = question.strip()
        tokens = re.split(r"(\W+)", text)
        normalized_tokens = []
        for tok in tokens:
            low = tok.lower()
            if low in TYPO_CORRECTIONS:
                normalized_tokens.append(TYPO_CORRECTIONS[low])
            else:
                normalized_tokens.append(tok)
        joined = "".join(normalized_tokens)
        joined = re.sub(r"\bhow many data\b", "how many documents", joined, flags=re.IGNORECASE)
        joined = re.sub(r"\bhow much data\b", "how many documents", joined, flags=re.IGNORECASE)
        joined = re.sub(r"\bhow many record\b", "how many records", joined, flags=re.IGNORECASE)
        joined = re.sub(r"\bhow many entry\b", "how many entries", joined, flags=re.IGNORECASE)
        return joined.strip()


class QueryPlannerEngine:
    """
    Dataset-First Schema-Aware Intent Classifier, Collection Resolver,
    Field Resolver, and Structured Query Planner.
    Separates:
      1. Dataset Intelligence & Collection Resolution (`CollectionResolver`)
      2. Collection Schema Inspection (`CollectionIntelligenceService`)
      3. Intent & Query Plan Construction
    Never silently guesses a collection when multiple collections exist and the question is ambiguous.
    """

    def __init__(self, schema_service: Any):
        self.schema_service = schema_service
        self.dataset_service = DatasetIntelligenceService(schema_service)
        self.collection_service = CollectionIntelligenceService(self.dataset_service)
        self.resolver = CollectionResolver(self.dataset_service)

    def build_plan(
        self,
        question: str,
        source_id: str | None = None,
        source_name: str | None = None,
        active_collection: str | None = None,
        conversation_context: dict[str, Any] | None = None,
    ) -> QueryPlan:
        normalized = QuestionNormalizer.normalize(question)
        q_lower = normalized.lower()
        q_clean = re.sub(r"[^\w\s]", " ", q_lower)

        # 1. Explicit Off-Topic / Unrelated Check
        unrelated_phrases = (
            "weather",
            "write a poem",
            "tell me a joke",
            "capital of france",
            "who won the world cup",
            "who is the president",
            "recipe for",
            "2+2",
            "2 + 2",
            "translate to spanish",
            "how to cook",
        )
        if any(p in q_lower for p in unrelated_phrases):
            return QueryPlan(
                original_question=question,
                normalized_question=normalized,
                intent="UNRELATED",
                collection_status="unrelated",
                confidence=0.98,
                source_id=source_id,
                source_name=source_name,
                presentation_type="error",
            )

        # 2. Run Dataset-First Collection Resolution
        res = self.resolver.resolve(
            question=normalized,
            source_id=source_id,
            explicit_collection=active_collection,
            conversation_context=conversation_context,
        )

        # 2A. Dataset-Level Question ("give me info about dataset", "what collections are available?", "how many collections are there?")
        if res.status == "dataset_level":
            intent_type = (
                "COLLECTION_OVERVIEW"
                if "collection" in q_lower or "table" in q_lower
                else "DATASET_OVERVIEW"
            )
            return QueryPlan(
                original_question=question,
                normalized_question=normalized,
                intent=intent_type,
                collection_status="dataset_level",
                candidate_collections=res.candidates,
                confidence=res.confidence,
                source_id=source_id,
                source_name=source_name,
                presentation_type="dataset_overview",
            )

        # 2B. Non-Existent Collection Mentioned ("show teachers", "how many flights")
        if res.status == "not_found":
            missing = res.missing_entity or "requested"
            return QueryPlan(
                original_question=question,
                normalized_question=normalized,
                intent="CLARIFICATION",
                collection_status="not_found",
                candidate_collections=res.candidates,
                confidence=res.confidence,
                source_id=source_id,
                source_name=source_name,
                clarification_message=f"I couldn't find a `{missing}` collection in this dataset. Which of the {len(res.candidates)} available collections would you like to explore?",
                clarification_options=res.candidates,
                presentation_type="clarification",
            )

        # 2C. Ambiguous Collection ("how many data are there?", "show me the records", "give me information")
        if res.status == "ambiguous":
            is_count_intent = bool(
                re.search(r"\b(how many|count|number of|total)\b", q_lower)
            )
            action_verb = "count" if is_count_intent else "use"
            msg = (
                f"I found {len(res.candidates)} collections in this dataset. "
                f"Which collection would you like me to {action_verb}?"
            )
            return QueryPlan(
                original_question=question,
                normalized_question=normalized,
                intent="CLARIFICATION",
                collection_status="ambiguous",
                candidate_collections=res.candidates,
                confidence=res.confidence,
                source_id=source_id,
                source_name=source_name,
                clarification_message=msg,
                clarification_options=res.candidates,
                presentation_type="clarification",
            )

        # 2D. Unrelated
        if res.status == "unrelated":
            return QueryPlan(
                original_question=question,
                normalized_question=normalized,
                intent="UNRELATED",
                collection_status="unrelated",
                candidate_collections=res.candidates,
                confidence=res.confidence,
                source_id=source_id,
                source_name=source_name,
                presentation_type="error",
            )

        # 2E. Multi-Collection Query ("which customers placed the most orders?", "how many customers have orders?")
        if res.status == "multi_collection":
            return QueryPlan(
                original_question=question,
                normalized_question=normalized,
                intent="MULTI_COLLECTION",
                collection=res.selected_collection or "orders",
                secondary_collection=res.secondary_collection or "customers",
                collection_status="multi_collection",
                candidate_collections=res.candidates,
                confidence=res.confidence,
                source_id=source_id,
                source_name=source_name,
                limit=15,
                operation="aggregate",
                presentation_type="table",
            )

        # 3. Single Resolved Collection -> Deep Collection Schema Inspection
        col_name = res.selected_collection
        if not col_name:
            return QueryPlan(
                original_question=question,
                normalized_question=normalized,
                intent="CLARIFICATION",
                collection_status="ambiguous",
                candidate_collections=res.candidates,
                confidence=0.85,
                source_id=source_id,
                source_name=source_name,
                clarification_message=f"I found {len(res.candidates)} collections in this dataset. Which collection would you like me to use?",
                clarification_options=res.candidates,
                presentation_type="clarification",
            )

        # If the user typed a conversational collection switch ("actually customers", "I meant customers", "customers")
        # inherit the intent/question from conversation_context if the input only named the collection!
        effective_q_lower = q_lower
        if res.is_collection_switch and conversation_context:
            prev_question = conversation_context.get("pending_question") or conversation_context.get("last_question")
            prev_intent = conversation_context.get("intent")
            if prev_question:
                effective_q_lower = QuestionNormalizer.normalize(str(prev_question)).lower()
            elif prev_intent == "COUNT":
                effective_q_lower = f"how many {col_name} are there"
            else:
                effective_q_lower = f"show me {col_name}"

        target_col = self.collection_service.get_collection_schema(col_name, source_id)
        if not target_col:
            return QueryPlan(
                original_question=question,
                normalized_question=normalized,
                intent="UNRELATED",
                collection_status="unrelated",
                confidence=0.95,
                source_id=source_id,
                source_name=source_name,
                presentation_type="error",
            )

        col_columns = target_col.get("columns", [])
        col_fields = {c["name"]: c.get("data_type", "String") for c in col_columns}
        top_level_fields = [f for f in col_fields if "." not in f and "[]" not in f and f != "_id"]
        numeric_fields = [
            f
            for f, t in col_fields.items()
            if t in ("Double", "Int64", "Number", "Integer") and "." not in f and not f.endswith("_id")
        ]
        categorical_fields = [
            f
            for f, t in col_fields.items()
            if t == "String" and not f.endswith("_id") and "[]" not in f
        ]

        # Check SCHEMA_QUERY on the resolved collection ("what fields are in products?", "show schema of customers")
        if re.search(r"\b(fields|columns|schema|structure|attributes|data types|bson types)\b", effective_q_lower) and not re.search(
            r"\b(sort|filter|where|above|below)\b", effective_q_lower
        ):
            return QueryPlan(
                original_question=question,
                normalized_question=normalized,
                intent="SCHEMA_QUERY",
                confidence=0.96,
                source_id=source_id,
                source_name=source_name,
                collection=col_name,
                candidate_collections=res.candidates,
                presentation_type="schema",
            )

        # 4. Resolve Mentioned Fields & Semantic Field Synonyms
        requested_concept: str | None = None
        if re.search(r"\b(revenue|sales|turnover|gross revenue|net revenue)\b", effective_q_lower):
            requested_concept = "REVENUE"
        elif re.search(r"\b(spend|spending|spent|expenditure)\b", effective_q_lower):
            requested_concept = "SPENDING"
        elif re.search(r"\b(gpa|academic|grade|score)\b", effective_q_lower):
            requested_concept = "GPA"
        elif re.search(r"\b(salary|wage|compensation)\b", effective_q_lower):
            requested_concept = "SALARY"
        elif re.search(r"\b(price|unit price)\b", effective_q_lower):
            requested_concept = "PRICE"
        elif re.search(r"\b(stock|inventory|quantity)\b", effective_q_lower):
            requested_concept = "QUANTITY"

        matched_numeric: list[str] = []

        if requested_concept:
            match_res = SemanticFieldRegistry.match_requested_metric(
                requested_concept, col_name, col_columns
            )
            if match_res.status == "EXACT_MATCH" and match_res.field_name:
                matched_numeric = [match_res.field_name]
            elif match_res.status == "RELATED_ALTERNATIVE":
                return QueryPlan(
                    original_question=question,
                    normalized_question=normalized,
                    intent="METRIC_ALTERNATIVE",
                    confidence=match_res.confidence,
                    source_id=source_id,
                    source_name=source_name,
                    collection=col_name,
                    metric_field=match_res.field_name,
                    requested_concept=requested_concept,
                    explanation=match_res.explanation,
                    clarification_message=match_res.explanation,
                    clarification_options=match_res.alternative_fields,
                    presentation_type="clarification",
                )
            elif match_res.status in ("INCOMPATIBLE", "NOT_FOUND"):
                return QueryPlan(
                    original_question=question,
                    normalized_question=normalized,
                    intent="METRIC_UNAVAILABLE",
                    confidence=match_res.confidence,
                    source_id=source_id,
                    source_name=source_name,
                    collection=col_name,
                    requested_concept=requested_concept,
                    explanation=match_res.explanation,
                    clarification_message=match_res.explanation,
                    presentation_type="warning",
                )

        if not matched_numeric:
            for nf in numeric_fields:
                nf_clean = nf.lower().replace("_", " ")
                if re.search(rf"\b({re.escape(nf.lower())}|{re.escape(nf_clean)})\b", effective_q_lower):
                    matched_numeric.append(nf)

        if not matched_numeric:
            for word, candidates in SEMANTIC_FIELD_SYNONYMS.items():
                if re.search(rf"\b{re.escape(word)}\b", effective_q_lower):
                    for cand in candidates:
                        if cand in numeric_fields and cand not in matched_numeric:
                            matched_numeric.append(cand)

        if not matched_numeric and len(numeric_fields) > 1:
            is_vague_numeric = any(
                p in effective_q_lower
                for p in (
                    "total value",
                    "average value",
                    "sum value",
                    "highest value",
                    "lowest value",
                    "max value",
                    "min value",
                    "total amount",
                    "average amount",
                )
            )
            # Only trigger if 'amount' or 'value' isn't an actual field in the collection
            if is_vague_numeric and "value" not in col_fields and "amount" not in col_fields:
                field_candidates = [
                    {
                        "source_id": source_id or "",
                        "name": nf,
                        "collection": col_name,
                        "description": f"Calculate on {nf.replace('_', ' ')}",
                        "clarification_type": "field",
                    }
                    for nf in numeric_fields[:5]
                ]
                return QueryPlan(
                    original_question=question,
                    normalized_question=normalized,
                    intent="CLARIFICATION",
                    collection=col_name,
                    collection_status="ambiguous_field",
                    candidate_collections=field_candidates,
                    clarification_message=f"In `{col_name}`, which field would you like to calculate: {', '.join(numeric_fields[:4])}?",
                    clarification_options=field_candidates,
                    presentation_type="clarification",
                )

        primary_metric = (
            matched_numeric[0]
            if matched_numeric
            else (numeric_fields[0] if numeric_fields else None)
        )
        secondary_metric = (
            matched_numeric[1]
            if len(matched_numeric) > 1
            else next((nf for nf in numeric_fields if nf != primary_metric), None)
        )

        # Resolve Group / Dimension Field ("by category", "by department", "by month", "per city")
        group_field = None
        m_by = re.search(
            r"\b(?:by|per|across|for each|grouped by)\s+([a-zA-Z0-9_.\s]+?)(?:\s+and\s+|\s+in\s+|$)",
            effective_q_lower,
        )
        if m_by:
            cand_phrase = m_by.group(1).strip()
            for f in col_fields:
                f_leaf = f.split(".")[-1].replace("[]", "").lower()
                f_words = f_leaf.replace("_", " ")
                singular_cand = cand_phrase.rstrip("s")
                if (
                    f_leaf == cand_phrase
                    or f_leaf == singular_cand
                    or f_words in cand_phrase
                    or singular_cand in f_leaf
                ):
                    if (
                        f not in numeric_fields
                        or "group" in effective_q_lower
                        or "average" in effective_q_lower
                        or "count" in effective_q_lower
                        or "total" in effective_q_lower
                    ):
                        group_field = f.replace("[].", ".")
                        break

        if not group_field and (
            "monthly" in effective_q_lower
            or "by month" in effective_q_lower
            or ("january" in effective_q_lower and "february" in effective_q_lower)
        ):
            if "month" in col_fields:
                group_field = "month"

        # 5. Build Filter Conditions ($match) with SemanticFilterExtractor
        filters: dict[str, Any] = {}
        filter_descriptions: list[str] = []
        requested_filters: list[dict[str, Any]] = []

        if (
            not res.is_collection_switch
            and conversation_context
            and conversation_context.get("collection") == col_name
        ):
            if re.search(
                r"^(?:only|just|and|also|sort them|order them|how many are there|how many|which of them)\b",
                q_clean,
            ):
                prev_filters = conversation_context.get("filters") or {}
                if isinstance(prev_filters, dict) and prev_filters:
                    filters.update(prev_filters)

        # 5A. Extract Natural Language Filters & Validate Against Target Collection Schema
        extracted_filters = SemanticFilterExtractor.extract_filters(normalized)
        for ef in extracted_filters:
            target_f, mongo_cond, desc = SemanticFilterExtractor.resolve_filter_to_collection(
                ef, col_columns, primary_numeric_field=primary_metric
            )
            if target_f is None:
                # FAIL-CLOSED: Field does not exist in target collection!
                missing_name = desc or ef.raw_field
                col_field_names = [c["name"] for c in col_columns]
                return QueryPlan(
                    original_question=question,
                    normalized_question=normalized,
                    intent="FIELD_NOT_AVAILABLE",
                    confidence=0.98,
                    source_id=source_id,
                    source_name=source_name,
                    collection=col_name,
                    candidate_collections=res.candidates,
                    missing_filter_field=missing_name,
                    available_fields=col_field_names,
                    clarification_message=f"The `{col_name}` collection does not contain a `{missing_name}` field, so I couldn't apply your requested filter.",
                    explanation=f"The `{col_name}` collection does not contain a `{missing_name}` field, so I couldn't apply your requested filter.",
                    presentation_type="field_unavailable",
                )
            else:
                filters.update(mongo_cond)
                if desc and desc not in filter_descriptions:
                    filter_descriptions.append(desc)
                requested_filters.append(
                    {
                        "field": target_f,
                        "operator": ef.operator,
                        "value": ef.value,
                        "description": desc,
                        "raw_field": ef.raw_field,
                    }
                )

        # 5B. Auxiliary Fallback: Schema sample values if no filter for that field was extracted
        for col_info in col_columns:
            fname = col_info["name"]
            if (
                fname in numeric_fields
                or fname == "_id"
                or fname == "month"
                or (fname in ("city", "address.city") and ("city" in filters or "address.city" in filters))
                or fname in filters
            ):
                continue
            for sv in col_info.get("sample_values", []) or []:
                sv_str = str(sv).strip()
                if len(sv_str) >= 3 and re.search(rf"\b{re.escape(sv_str.lower())}\b", effective_q_lower):
                    clean_path = fname.replace("[].", ".")
                    if clean_path not in filters:
                        filters[clean_path] = sv_str
                        f_desc = f"{clean_path.split('.')[-1]} = '{sv_str}'"
                        filter_descriptions.append(f_desc)
                        requested_filters.append(
                            {
                                "field": clean_path,
                                "operator": "eq",
                                "value": sv_str,
                                "description": f_desc,
                                "raw_field": clean_path,
                            }
                        )
                    break

        months_mentioned = [
            m.capitalize()
            for m in (
                "january",
                "february",
                "march",
                "april",
                "may",
                "june",
                "july",
                "august",
                "september",
                "october",
                "november",
                "december",
            )
            if re.search(rf"\b{m}\b", effective_q_lower)
        ]
        if months_mentioned and "month" in col_fields and "month" not in filters:
            m_val = months_mentioned if len(months_mentioned) > 1 else months_mentioned[0]
            filters["month"] = {"$in": months_mentioned} if len(months_mentioned) > 1 else months_mentioned[0]
            m_desc = f"month in {months_mentioned}"
            filter_descriptions.append(m_desc)
            requested_filters.append(
                {
                    "field": "month",
                    "operator": "in" if len(months_mentioned) > 1 else "eq",
                    "value": m_val,
                    "description": m_desc,
                    "raw_field": "month",
                }
            )

        # 6. Determine Exact Intent
        if (
            re.search(
                r"\b(how many|count|total number of|number of|total records|total documents|total products|total customers|total orders|total employees|total students)\b",
                effective_q_lower,
            )
            and not group_field
        ):
            return QueryPlan(
                original_question=question,
                normalized_question=normalized,
                intent="COUNT",
                confidence=0.98,
                source_id=source_id,
                source_name=source_name,
                collection=col_name,
                candidate_collections=res.candidates,
                filters=filters,
                filter_descriptions=filter_descriptions,
                requested_filters=requested_filters,
                limit=10,
                operation="aggregate",
                aggregation_op="count",
                presentation_type="kpi",
            )

        m_top = re.search(r"\b(?:top|first|highest)\s+(\d+)\b", effective_q_lower)
        m_bottom = re.search(r"\b(?:bottom|lowest|cheapest|least)\s+(\d+)\b", effective_q_lower)
        if m_top or m_bottom:
            n_val = int(m_top.group(1)) if m_top else int(m_bottom.group(1))
            is_bottom = bool(m_bottom)
            sort_f = primary_metric or (top_level_fields[0] if top_level_fields else "_id")
            return QueryPlan(
                original_question=question,
                normalized_question=normalized,
                intent="BOTTOM_N" if is_bottom else "TOP_N",
                confidence=0.97,
                source_id=source_id,
                source_name=source_name,
                collection=col_name,
                candidate_collections=res.candidates,
                target_fields=top_level_fields[:8],
                metric_field=sort_f,
                filters=filters,
                filter_descriptions=filter_descriptions,
                requested_filters=requested_filters,
                sort={sort_f: 1 if is_bottom else -1},
                limit=n_val,
                operation="aggregate",
                presentation_type="ranked_table",
            )

        is_superlative_max = bool(
            re.search(
                r"\b(most expensive|highest|maximum|max|best selling|top earner|richest|largest|biggest)\b",
                effective_q_lower,
            )
            and not re.search(
                r"\b(top\s+\d+|by\s+department|by\s+category|by\s+month)\b", effective_q_lower
            )
        )
        is_superlative_min = bool(
            re.search(
                r"\b(least expensive|cheapest|lowest|minimum|min|smallest)\b",
                effective_q_lower,
            )
            and not re.search(
                r"\b(bottom\s+\d+|by\s+department|by\s+category|by\s+month)\b", effective_q_lower
            )
        )
        if (is_superlative_max or is_superlative_min) and primary_metric:
            sort_dir = -1 if is_superlative_max else 1
            return QueryPlan(
                original_question=question,
                normalized_question=normalized,
                intent="MAXIMUM" if is_superlative_max else "MINIMUM",
                confidence=0.97,
                source_id=source_id,
                source_name=source_name,
                collection=col_name,
                candidate_collections=res.candidates,
                target_fields=top_level_fields[:8],
                metric_field=primary_metric,
                filters=filters,
                filter_descriptions=filter_descriptions,
                requested_filters=requested_filters,
                sort={primary_metric: sort_dir},
                limit=1,
                operation="aggregate",
                aggregation_op="max" if is_superlative_max else "min",
                presentation_type="detail",
            )

        if re.search(r"\b(compare|comparison|versus|vs\.?|against)\b", effective_q_lower):
            return QueryPlan(
                original_question=question,
                normalized_question=normalized,
                intent="COMPARISON",
                confidence=0.95,
                source_id=source_id,
                source_name=source_name,
                collection=col_name,
                candidate_collections=res.candidates,
                target_fields=top_level_fields[:8],
                metric_field=primary_metric,
                secondary_metric_field=secondary_metric,
                group_field=group_field,
                filters=filters,
                filter_descriptions=filter_descriptions,
                requested_filters=requested_filters,
                limit=25,
                operation="aggregate",
                presentation_type="comparison",
            )

        is_avg = bool(re.search(r"\b(average|avg|mean)\b", effective_q_lower))
        is_sum = bool(
            re.search(
                r"\b(sum|total\s+(?:revenue|sales|amount|spent|salary|stock|units))\b",
                effective_q_lower,
            )
            or (
                requested_concept == "REVENUE"
                and primary_metric
                and not re.search(r"\b(which|who|list\s+orders|show\s+orders)\b", effective_q_lower)
            )
            or (
                requested_concept == "SPENDING"
                and primary_metric
                and re.search(r"\b(how much|total|sum|overall)\b", effective_q_lower)
            )
        )
        is_trend = bool(re.search(r"\b(trend|monthly|by month|over time)\b", effective_q_lower))

        if is_avg or is_sum or is_trend or group_field:
            intent_name = (
                "TREND"
                if is_trend
                else ("GROUP_BY" if group_field else ("AVERAGE" if is_avg else "SUM"))
            )
            agg_op = "$avg" if is_avg else ("$sum" if (is_sum or primary_metric) else "$count")
            return QueryPlan(
                original_question=question,
                normalized_question=normalized,
                intent=intent_name,
                confidence=0.96,
                source_id=source_id,
                source_name=source_name,
                collection=col_name,
                candidate_collections=res.candidates,
                target_fields=top_level_fields[:8],
                metric_field=primary_metric,
                requested_concept=requested_concept,
                group_field=group_field
                or ("month" if is_trend and "month" in col_fields else None),
                filters=filters,
                filter_descriptions=filter_descriptions,
                requested_filters=requested_filters,
                limit=50,
                operation="aggregate",
                aggregation_op=agg_op,
                presentation_type="chart" if (group_field or is_trend) else "kpi",
            )

        if re.search(r"\b(distinct|unique|different)\b", effective_q_lower):
            dist_field = group_field or (
                categorical_fields[0] if categorical_fields else top_level_fields[0]
            )
            return QueryPlan(
                original_question=question,
                normalized_question=normalized,
                intent="DISTINCT_VALUES",
                confidence=0.95,
                source_id=source_id,
                source_name=source_name,
                collection=col_name,
                candidate_collections=res.candidates,
                target_fields=[dist_field],
                group_field=dist_field,
                filters=filters,
                filter_descriptions=filter_descriptions,
                requested_filters=requested_filters,
                limit=50,
                operation="aggregate",
                presentation_type="table",
            )

        if re.search(r"\b(sort|sorted|order|ordered)\b", effective_q_lower) or (
            "expensive" in effective_q_lower and not is_superlative_max
        ):
            sort_f = primary_metric or (top_level_fields[0] if top_level_fields else "_id")
            is_asc = bool(
                re.search(
                    r"\b(asc|ascending|lowest to highest|low to high|smallest)\b",
                    effective_q_lower,
                )
            )
            sort_dir = 1 if is_asc else -1
            return QueryPlan(
                original_question=question,
                normalized_question=normalized,
                intent="SORT",
                confidence=0.96,
                source_id=source_id,
                source_name=source_name,
                collection=col_name,
                candidate_collections=res.candidates,
                target_fields=top_level_fields[:8],
                metric_field=sort_f,
                filters=filters,
                filter_descriptions=filter_descriptions,
                requested_filters=requested_filters,
                sort={sort_f: sort_dir},
                limit=50,
                operation="aggregate",
                presentation_type="table",
            )

        if filters:
            return QueryPlan(
                original_question=question,
                normalized_question=normalized,
                intent="FILTER",
                confidence=0.96,
                source_id=source_id,
                source_name=source_name,
                collection=col_name,
                candidate_collections=res.candidates,
                target_fields=top_level_fields[:8],
                metric_field=primary_metric,
                filters=filters,
                filter_descriptions=filter_descriptions,
                requested_filters=requested_filters,
                sort=None,
                limit=50,
                operation="aggregate",
                presentation_type="table",
            )

        return QueryPlan(
            original_question=question,
            normalized_question=normalized,
            intent="LIST_RECORDS",
            confidence=0.97,
            source_id=source_id,
            source_name=source_name,
            collection=col_name,
            candidate_collections=res.candidates,
            target_fields=top_level_fields[:8],
            metric_field=None,
            filters={},
            filter_descriptions=[],
            requested_filters=[],
            sort=None,
            limit=50,
            operation="aggregate",
            presentation_type="table",
        )

    def compile_to_mongo_query(self, plan: QueryPlan) -> dict[str, Any]:
        """Compiles a structured QueryPlan into an executable MongoDB aggregation dictionary."""
        if not plan.collection:
            raise ValueError("QueryPlan has no target collection.")
        if plan.intent == "FIELD_NOT_AVAILABLE":
            raise ValueError("Cannot compile MongoDB query for FIELD_NOT_AVAILABLE intent.")

        # Multi-Collection $lookup query (e.g. "which customers placed the most orders?")
        if plan.intent == "MULTI_COLLECTION":
            sec_col = plan.secondary_collection or "customers"
            pipeline = [
                {
                    "$group": {
                        "_id": "$customer_id",
                        "orders_placed": {"$sum": 1},
                        "total_order_value": {"$sum": "$amount"},
                    }
                },
                {
                    "$lookup": {
                        "from": sec_col,
                        "localField": "_id",
                        "foreignField": "customer_id",
                        "as": "customer_info",
                    }
                },
                {"$unwind": {"path": "$customer_info", "preserveNullAndEmptyArrays": True}},
                {
                    "$project": {
                        "_id": 0,
                        "customer_id": "$_id",
                        "customer_name": "$customer_info.name",
                        "city": "$customer_info.city",
                        "tier": "$customer_info.tier",
                        "orders_placed": 1,
                        "total_order_value": {"$round": ["$total_order_value", 2]},
                    }
                },
                {"$sort": {"orders_placed": -1, "total_order_value": -1}},
                {"$limit": plan.limit or 15},
            ]
            return {
                "collection": plan.collection,
                "operation": "aggregate",
                "pipeline": pipeline,
                "limit": plan.limit or 15,
            }

        pipeline = []
        if plan.filters:
            pipeline.append({"$match": plan.filters})

        if plan.intent == "COUNT":
            count_alias = f"total_{plan.collection.split('_')[-1]}"
            pipeline.append({"$count": count_alias})
            return {
                "collection": plan.collection,
                "operation": "aggregate",
                "pipeline": pipeline,
                "limit": 10,
            }

        if plan.intent in ("AVERAGE", "SUM") and not plan.group_field and plan.metric_field:
            agg_op = "$avg" if plan.intent == "AVERAGE" else "$sum"
            label = f"{'average' if plan.intent == 'AVERAGE' else 'total'}_{plan.metric_field}"
            pipeline.extend(
                [
                    {
                        "$group": {
                            "_id": None,
                            label: {agg_op: f"${plan.metric_field}"},
                            "document_count": {"$sum": 1},
                        }
                    },
                    {
                        "$project": {
                            "_id": 0,
                            label: {"$round": [f"${label}", 2]},
                            "document_count": 1,
                        }
                    },
                ]
            )
            return {
                "collection": plan.collection,
                "operation": "aggregate",
                "pipeline": pipeline,
                "limit": 10,
            }

        if plan.intent in ("GROUP_BY", "TREND", "DISTRIBUTION") or (
            plan.intent in ("AVERAGE", "SUM") and plan.group_field
        ):
            dim = plan.group_field or "_id"
            dim_label = dim.split(".")[-1]
            if plan.metric_field:
                is_avg = plan.intent == "AVERAGE" or plan.aggregation_op == "$avg"
                agg_op = "$avg" if is_avg else "$sum"
                agg_label = f"{'average' if is_avg else 'total'}_{plan.metric_field}"
                pipeline.extend(
                    [
                        {
                            "$group": {
                                "_id": f"${dim}",
                                agg_label: {agg_op: f"${plan.metric_field}"},
                                "document_count": {"$sum": 1},
                            }
                        },
                        {
                            "$project": {
                                "_id": 0,
                                dim_label: "$_id",
                                agg_label: {"$round": [f"${agg_label}", 2]},
                                "document_count": 1,
                            }
                        },
                        {"$sort": {agg_label: -1}},
                    ]
                )
            else:
                pipeline.extend(
                    [
                        {"$group": {"_id": f"${dim}", "document_count": {"$sum": 1}}},
                        {"$project": {"_id": 0, dim_label: "$_id", "document_count": 1}},
                        {"$sort": {"document_count": -1}},
                    ]
                )
            return {
                "collection": plan.collection,
                "operation": "aggregate",
                "pipeline": pipeline,
                "limit": plan.limit,
            }

        if plan.intent == "COMPARISON":
            if plan.group_field and plan.metric_field:
                dim = plan.group_field
                dim_label = dim.split(".")[-1]
                agg_label = f"total_{plan.metric_field}"
                pipeline.extend(
                    [
                        {
                            "$group": {
                                "_id": f"${dim}",
                                agg_label: {"$sum": f"${plan.metric_field}"},
                                "average": {"$avg": f"${plan.metric_field}"},
                                "orders_count": {"$sum": 1},
                            }
                        },
                        {
                            "$project": {
                                "_id": 0,
                                dim_label: "$_id",
                                agg_label: {"$round": [f"${agg_label}", 2]},
                                "average": {"$round": ["$average", 2]},
                                "orders_count": 1,
                            }
                        },
                        {"$sort": {agg_label: -1}},
                    ]
                )
                return {
                    "collection": plan.collection,
                    "operation": "aggregate",
                    "pipeline": pipeline,
                    "limit": plan.limit,
                }
            proj: dict[str, Any] = {"_id": 0}
            for f in plan.target_fields:
                if f.endswith("_id") or f in ("name", "title", "category", "department"):
                    proj[f] = 1
            if plan.metric_field:
                proj[plan.metric_field] = 1
            if plan.secondary_metric_field:
                proj[plan.secondary_metric_field] = 1
            if len(proj) <= 1:
                for f in plan.target_fields[:6]:
                    proj[f] = 1
            if plan.metric_field:
                pipeline.append({"$sort": {plan.metric_field: -1}})
            pipeline.append({"$limit": plan.limit})
            pipeline.append({"$project": proj})
            return {
                "collection": plan.collection,
                "operation": "aggregate",
                "pipeline": pipeline,
                "limit": plan.limit,
            }

        if plan.intent == "DISTINCT_VALUES" and plan.group_field:
            dim = plan.group_field
            dim_label = dim.split(".")[-1]
            pipeline.extend(
                [
                    {"$group": {"_id": f"${dim}", "document_count": {"$sum": 1}}},
                    {"$project": {"_id": 0, dim_label: "$_id", "document_count": 1}},
                    {"$sort": {dim_label: 1}},
                ]
            )
            return {
                "collection": plan.collection,
                "operation": "aggregate",
                "pipeline": pipeline,
                "limit": plan.limit,
            }

        if plan.sort:
            pipeline.append({"$sort": plan.sort})
        pipeline.append({"$limit": plan.limit})

        proj = {"_id": 0}
        for f in plan.target_fields[:8]:
            proj[f] = 1
        if plan.metric_field:
            proj[plan.metric_field] = 1
        for filter_f in plan.filters:
            clean_f = filter_f.split(".")[0]
            proj[clean_f] = 1
        if len(proj) > 1:
            pipeline.append({"$project": proj})

        if plan.filters and not any("$match" in stage for stage in pipeline):
            raise ValueError("Filter preservation invariant violated: compiled pipeline is missing $match stage!")

        return {
            "collection": plan.collection,
            "operation": "aggregate",
            "pipeline": pipeline,
            "limit": plan.limit,
        }
