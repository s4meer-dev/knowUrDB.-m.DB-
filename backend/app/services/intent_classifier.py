import re
from dataclasses import dataclass, field
from typing import Any

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
    "DOCUMENT_RAG",
    "MULTI_SOURCE",
    "CLARIFICATION",
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
    "collcetion": "collection",
    "databse": "database",
    "datbase": "database",
    "datset": "dataset",
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
}

SEMANTIC_FIELD_SYNONYMS: dict[str, list[str]] = {
    "expensive": ["price", "amount", "total_amount", "total_spent", "salary"],
    "cheap": ["price", "amount", "total_amount"],
    "cheapest": ["price", "amount", "total_amount"],
    "cost": ["price", "amount", "total_amount"],
    "price": ["price", "amount", "total_amount"],
    "revenue": ["revenue", "total_amount", "amount", "price", "total_spent"],
    "sales": ["units_sold", "total_amount", "amount", "revenue", "price"],
    "selling": ["units_sold", "total_amount", "amount"],
    "sold": ["units_sold"],
    "stock": ["stock", "inventory", "quantity"],
    "inventory": ["stock", "quantity"],
    "spent": ["total_spent", "total_amount", "amount"],
    "spend": ["total_spent", "total_amount", "amount"],
    "salary": ["salary", "compensation"],
    "paid": ["salary", "total_spent", "total_amount"],
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
    original_question: str
    normalized_question: str
    intent: str
    confidence: float = 0.95
    source_id: str | None = None
    source_name: str | None = None
    collection: str | None = None
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
    clarification_options: list[dict[str, str]] = field(default_factory=list)


class QuestionNormalizer:
    """Normalizes natural language questions, fixes common typos, and preserves user intent."""

    @staticmethod
    def normalize(question: str) -> str:
        if not question:
            return ""
        text = question.strip()
        # Normalize tokens while preserving case for proper nouns in original question
        tokens = re.split(r"(\W+)", text)
        normalized_tokens = []
        for tok in tokens:
            low = tok.lower()
            if low in TYPO_CORRECTIONS:
                normalized_tokens.append(TYPO_CORRECTIONS[low])
            else:
                normalized_tokens.append(tok)
        joined = "".join(normalized_tokens)
        # Canonicalize colloquial phrases without altering intent
        joined = re.sub(r"\bhow many data\b", "how many documents", joined, flags=re.IGNORECASE)
        joined = re.sub(r"\bhow much data\b", "how many documents", joined, flags=re.IGNORECASE)
        joined = re.sub(r"\bhow many record\b", "how many records", joined, flags=re.IGNORECASE)
        joined = re.sub(r"\bhow many entry\b", "how many entries", joined, flags=re.IGNORECASE)
        return joined.strip()


class QueryPlannerEngine:
    """
    Deterministic-first Schema-Aware Intent Classifier, Collection Resolver,
    Field Resolver, and Structured Query Planner.
    Never invents rankings or aggregations the user did not ask for.
    """

    def __init__(self, schema_service: Any):
        self.schema_service = schema_service

    def resolve_collection(
        self,
        q_lower: str,
        collections: list[dict[str, Any]],
        active_collection: str | None = None,
        conversation_context: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any] | None, str]:
        """
        Returns (matched_collection_dict, resolution_reason).
        Priority:
          1. Explicit collection name or singular/plural/alias in question
          2. Unique value or field name match in question (e.g. 'Bangalore', 'GPA', 'salary')
          3. Explicit `active_collection` from UI / request
          4. `conversation_context` last collection
          5. Single collection in dataset or primary active collection for generic collection queries
        """
        if not collections:
            return None, "no_collections"

        col_by_name = {c["name"].lower(): c for c in collections}

        # 1. Explicit collection name / singular / plural / stem match
        for col in collections:
            cname = col["name"].lower()
            base_name = cname.split("_")[-1]
            singular = base_name[:-1] if base_name.endswith("s") else base_name
            plural = f"{singular}s"
            patterns = {cname, base_name, singular, plural}
            if base_name == "customers":
                patterns.update({"client", "clients", "buyer", "buyers"})
            elif base_name == "employees":
                patterns.update({"staff", "worker", "workers", "personnel"})
            elif base_name == "orders":
                patterns.update({"purchase", "purchases", "transaction", "transactions"})
            elif base_name == "products":
                patterns.update({"item", "items", "catalog", "merchandise"})
            elif base_name == "students":
                patterns.update({"learner", "learners", "pupil", "pupils"})

            for pat in patterns:
                if pat and re.search(rf"\b{re.escape(pat)}\b", q_lower):
                    return col, f"explicit_mention:{pat}"

        # 2. Match sample values or distinctive field names (e.g. "Bangalore", "Engineering", "gpa", "salary")
        best_col = None
        best_score = 0
        for col in collections:
            score = 0
            for cinfo in col.get("columns", []):
                cname_full = cinfo["name"].lower()
                c_leaf = cname_full.split(".")[-1].replace("[]", "")
                if len(c_leaf) > 2 and re.search(rf"\b{re.escape(c_leaf)}\b", q_lower):
                    # Give higher weight to distinctive fields (e.g. gpa, salary, stock, loyalty_tier)
                    if c_leaf not in {"name", "status", "id"}:
                        score += 5
                    else:
                        score += 2
                for sv in cinfo.get("sample_values", []) or []:
                    sv_str = str(sv).strip().lower()
                    if len(sv_str) > 2 and re.search(rf"\b{re.escape(sv_str)}\b", q_lower):
                        score += 8
            if score > best_score:
                best_score = score
                best_col = col

        if best_col and best_score >= 4:
            return best_col, "schema_field_or_value_match"

        # Domain keyword fallback
        domain_map = [
            (["price", "stock", "units_sold", "expensive", "cheapest", "product"], "products"),
            (["bangalore", "mumbai", "delhi", "chennai", "hyderabad", "pune", "kolkata", "total_spent", "lakh", "loyalty_tier", "customer"], "customers"),
            (["order_date", "january", "february", "march", "april", "may", "june", "total_amount", "order"], "orders"),
            (["salary", "department", "performance_score", "role", "employee"], "employees"),
            (["gpa", "major", "attendance", "credits_completed", "student"], "students"),
        ]
        for keywords, target_base in domain_map:
            if any(re.search(rf"\b{re.escape(k)}\b", q_lower) for k in keywords):
                for col in collections:
                    if col["name"].lower().endswith(target_base) or col["name"].lower() == target_base:
                        return col, f"domain_keyword:{target_base}"

        # 3. Active collection passed from UI
        if active_collection:
            ac_low = active_collection.lower()
            if ac_low in col_by_name:
                return col_by_name[ac_low], "active_collection"
            for col in collections:
                if col["name"].lower().endswith(ac_low):
                    return col, "active_collection"

        # 4. Conversation context
        if conversation_context and conversation_context.get("collection"):
            ctx_col = str(conversation_context["collection"]).lower()
            if ctx_col in col_by_name:
                return col_by_name[ctx_col], "conversation_context"

        # 5. Generic collection reference ("in the collection", "this collection", "how many data are there")
        if len(collections) == 1:
            return collections[0], "single_collection_in_source"

        if re.search(
            r"\b(in the collection|in this collection|in collection|the collection|this collection|how many documents|how many records|how many data|show me data|show all data|what is inside)\b",
            q_lower,
        ):
            # Default to first collection (`products` in demo_database) as active collection
            return collections[0], "default_active_collection"

        return None, "unresolved"

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
        q_words = set(q_clean.split())

        schema = self.schema_service.get_schema(source_id)
        collections: list[dict[str, Any]] = schema.get("tables", [])

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
                confidence=0.98,
                source_id=source_id,
                source_name=source_name,
                presentation_type="error",
            )

        if not collections:
            return QueryPlan(
                original_question=question,
                normalized_question=normalized,
                intent="UNRELATED",
                confidence=0.95,
                source_id=source_id,
                source_name=source_name,
                presentation_type="error",
            )

        # 2. DATASET_OVERVIEW vs COLLECTION_OVERVIEW vs SCHEMA_QUERY
        # Check if a specific collection was named
        explicit_col = None
        for col in collections:
            cname = col["name"].lower()
            base_name = cname.split("_")[-1]
            singular = base_name[:-1] if base_name.endswith("s") else base_name
            if re.search(rf"\b({re.escape(cname)}|{re.escape(base_name)}|{re.escape(singular)})\b", q_lower):
                explicit_col = col
                break

        # DATASET_OVERVIEW: "give me info about dataset", "tell me about this database", "what data do I have", "dataset overview"
        if not explicit_col and (
            re.search(
                r"\b(info|information|overview|summary|about|describe|what is in|what data|tell me about)\b.*\b(dataset|database|db|source|workspace|data)\b",
                q_lower,
            )
            or re.search(
                r"\b(dataset|database)\s+(info|information|overview|summary|details)\b",
                q_lower,
            )
            or q_clean.strip() in {"dataset", "database", "info about dataset", "give me info about dataset", "about dataset", "what data do i have"}
        ):
            return QueryPlan(
                original_question=question,
                normalized_question=normalized,
                intent="DATASET_OVERVIEW",
                confidence=0.98,
                source_id=source_id,
                source_name=source_name,
                presentation_type="dataset_overview",
            )

        # COLLECTION_OVERVIEW (All collections): "what collections are available?", "list collections", "show tables"
        if not explicit_col and (
            re.search(
                r"\b(what|which|list|show|available|all)\b.*\b(collections|tables)\b",
                q_lower,
            )
            or q_clean.strip() in {"collections", "show collections", "list collections", "show tables", "list tables", "what collections are available"}
        ):
            return QueryPlan(
                original_question=question,
                normalized_question=normalized,
                intent="COLLECTION_OVERVIEW",
                confidence=0.98,
                source_id=source_id,
                source_name=source_name,
                presentation_type="dataset_overview",
            )

        # SCHEMA_QUERY: "what fields are available?", "show schema of products", "what columns are in customers"
        if re.search(r"\b(fields|columns|schema|structure|attributes|data types|bson types)\b", q_lower) and not re.search(r"\b(sort|filter|where|above|below)\b", q_lower):
            target_col = explicit_col or (
                self.resolve_collection(q_lower, collections, active_collection, conversation_context)[0]
            )
            return QueryPlan(
                original_question=question,
                normalized_question=normalized,
                intent="SCHEMA_QUERY",
                confidence=0.96,
                source_id=source_id,
                source_name=source_name,
                collection=target_col["name"] if target_col else None,
                presentation_type="schema",
            )

        # COLLECTION_OVERVIEW for a specific collection: "tell me about the products collection", "overview of customers collection"
        if explicit_col and re.search(
            r"\b(tell me about|overview of|summary of|describe|info about|information about)\b.*\bcollection\b",
            q_lower,
        ):
            return QueryPlan(
                original_question=question,
                normalized_question=normalized,
                intent="COLLECTION_OVERVIEW",
                confidence=0.96,
                source_id=source_id,
                source_name=source_name,
                collection=explicit_col["name"],
                presentation_type="collection_overview",
            )

        # 3. Resolve Target Collection
        target_col, col_reason = self.resolve_collection(
            q_lower, collections, active_collection, conversation_context
        )

        # Check if user asked a total count across the entire database ("how many total documents in database")
        if not explicit_col and re.search(
            r"\b(total documents in database|how many total records in database|how many records across all collections)\b",
            q_lower,
        ):
            return QueryPlan(
                original_question=question,
                normalized_question=normalized,
                intent="DATASET_OVERVIEW",
                confidence=0.95,
                source_id=source_id,
                source_name=source_name,
                presentation_type="dataset_overview",
            )

        if not target_col:
            # Check if the question has general data/analytical words; if so, ask clarification rather than UNRELATED
            data_intent_words = {
                "show", "list", "display", "get", "find", "count", "how", "many", "average",
                "avg", "sum", "total", "top", "highest", "lowest", "max", "min", "compare",
                "filter", "search", "data", "records", "documents", "entries", "rows", "info",
                "information", "details", "only", "above", "below", "under", "over", "more", "less",
                "sort", "order", "by",
            }
            if q_words.intersection(data_intent_words):
                return QueryPlan(
                    original_question=question,
                    normalized_question=normalized,
                    intent="CLARIFICATION",
                    confidence=0.85,
                    source_id=source_id,
                    source_name=source_name,
                    clarification_message=f"I found {len(collections)} collections in this dataset. Which collection would you like me to query?",
                    clarification_options=[
                        {"collection": c["name"], "label": f"{c['name']} ({c.get('document_count', 0)} docs)"}
                        for c in collections
                    ],
                    presentation_type="clarification",
                )

            return QueryPlan(
                original_question=question,
                normalized_question=normalized,
                intent="UNRELATED",
                confidence=0.95,
                source_id=source_id,
                source_name=source_name,
                presentation_type="error",
            )

        col_name = target_col["name"]
        col_columns = target_col.get("columns", [])
        col_fields = {c["name"]: c.get("data_type", "String") for c in col_columns}
        top_level_fields = [f for f in col_fields if "." not in f and "[]" not in f and f != "_id"]
        numeric_fields = [
            f for f, t in col_fields.items() if t in ("Double", "Int64", "Number", "Integer") and "." not in f and not f.endswith("_id")
        ]
        categorical_fields = [
            f for f, t in col_fields.items() if t == "String" and not f.endswith("_id") and "[]" not in f
        ]

        # 4. Resolve Mentioned Fields & Semantic Field Synonyms
        matched_numeric: list[str] = []
        for nf in numeric_fields:
            nf_clean = nf.lower().replace("_", " ")
            if re.search(rf"\b({re.escape(nf.lower())}|{re.escape(nf_clean)})\b", q_lower):
                matched_numeric.append(nf)

        if not matched_numeric:
            for word, candidates in SEMANTIC_FIELD_SYNONYMS.items():
                if re.search(rf"\b{re.escape(word)}\b", q_lower):
                    for cand in candidates:
                        if cand in numeric_fields and cand not in matched_numeric:
                            matched_numeric.append(cand)

        primary_metric = matched_numeric[0] if matched_numeric else (numeric_fields[0] if numeric_fields else None)
        secondary_metric = matched_numeric[1] if len(matched_numeric) > 1 else (
            next((nf for nf in numeric_fields if nf != primary_metric), None)
        )

        # Resolve Group / Dimension Field ("by category", "by department", "by month", "per city")
        group_field = None
        m_by = re.search(r"\b(?:by|per|across|for each|grouped by)\s+([a-zA-Z0-9_.\s]+?)(?:\s+and\s+|\s+in\s+|$)", q_lower)
        if m_by:
            cand_phrase = m_by.group(1).strip()
            for f in col_fields:
                f_leaf = f.split(".")[-1].replace("[]", "").lower()
                f_words = f_leaf.replace("_", " ")
                singular_cand = cand_phrase.rstrip("s")
                if f_leaf == cand_phrase or f_leaf == singular_cand or f_words in cand_phrase or singular_cand in f_leaf:
                    if f not in numeric_fields or "group" in q_lower or "average" in q_lower or "count" in q_lower or "total" in q_lower:
                        group_field = f.replace("[].", ".")
                        break

        if not group_field and ("monthly" in q_lower or "by month" in q_lower or ("january" in q_lower and "february" in q_lower)):
            if "month" in col_fields:
                group_field = "month"

        # 5. Build Filter Conditions ($match)
        filters: dict[str, Any] = {}
        filter_descriptions: list[str] = []

        # Inherit filters from conversation context if user says "only ...", "sort them ...", "out of those, how many..."
        if conversation_context and conversation_context.get("collection") == col_name:
            if re.search(r"^(?:only|just|and|also|sort them|order them|how many are there|which of them)\b", q_lower):
                prev_filters = conversation_context.get("filters") or {}
                if isinstance(prev_filters, dict) and prev_filters:
                    filters.update(prev_filters)

        # Numeric threshold filters ("above 50000", "more than 1 lakh", "under 20000", "gpa above 3.5", "low stock")
        q_no_top = re.sub(r"\b(?:top|bottom|first|last|limit)\s+\d+", "", q_lower)
        q_no_top_clean = q_no_top.replace(",", "").replace("₹", "").replace("$", "")

        m_lakh = re.search(r"(\d+(?:\.\d+)?)\s*lakh", q_no_top_clean)
        threshold_val: float | None = None
        if m_lakh:
            threshold_val = float(m_lakh.group(1)) * 100000.0
        else:
            m_k = re.search(r"(\d+(?:\.\d+)?)\s*k\b", q_no_top_clean)
            if m_k:
                threshold_val = float(m_k.group(1)) * 1000.0
            else:
                m_num = re.search(
                    r"(?:above|over|more than|greater than|exceeding|at least|>=|>|below|under|less than|fewer than|<=|<|=)\s*(\d+(?:\.\d+)?)",
                    q_no_top_clean,
                )
                if m_num:
                    threshold_val = float(m_num.group(1))

        if threshold_val is not None and primary_metric:
            # Format display number cleanly
            disp_val = f"{int(threshold_val):,}" if threshold_val.is_integer() else f"{threshold_val:,.2f}"
            if any(w in q_no_top for w in ("above", "over", "more than", "greater than", "exceeding", ">")):
                filters[primary_metric] = {"$gt": threshold_val}
                filter_descriptions.append(f"{primary_metric} > {disp_val}")
            elif any(w in q_no_top for w in ("below", "under", "less than", "fewer than", "<")):
                filters[primary_metric] = {"$lt": threshold_val}
                filter_descriptions.append(f"{primary_metric} < {disp_val}")
            elif "at least" in q_no_top or ">=" in q_no_top:
                filters[primary_metric] = {"$gte": threshold_val}
                filter_descriptions.append(f"{primary_metric} >= {disp_val}")
            else:
                filters[primary_metric] = threshold_val
                filter_descriptions.append(f"{primary_metric} = {disp_val}")
        elif "low stock" in q_lower and "stock" in col_fields:
            filters["stock"] = {"$lt": 25}
            filter_descriptions.append("stock < 25")

        # Categorical / String value filters (e.g., "from Bangalore", "in Electronics", "status Delivered")
        city_synonyms = {
            "bangalore": ["Bangalore", "Bengaluru"],
            "bengaluru": ["Bangalore", "Bengaluru"],
            "mumbai": ["Mumbai", "Bombay"],
            "bombay": ["Mumbai", "Bombay"],
            "chennai": ["Chennai", "Madras"],
            "kolkata": ["Kolkata", "Calcutta"],
        }
        for city_key, city_vals in city_synonyms.items():
            if re.search(rf"\b{re.escape(city_key)}\b", q_lower):
                if "city" in col_fields:
                    filters["city"] = {"$in": city_vals}
                    filter_descriptions.append(f"city = '{city_vals[0]}'")
                elif "address.city" in col_fields:
                    filters["address.city"] = {"$in": city_vals}
                    filter_descriptions.append(f"city = '{city_vals[0]}'")
                break

        for col_info in col_columns:
            fname = col_info["name"]
            if fname in numeric_fields or fname == "_id" or fname in ("city", "address.city") and ("city" in filters or "address.city" in filters):
                continue
            for sv in col_info.get("sample_values", []) or []:
                sv_str = str(sv).strip()
                if len(sv_str) >= 3 and re.search(rf"\b{re.escape(sv_str.lower())}\b", q_lower):
                    clean_path = fname.replace("[].", ".")
                    filters[clean_path] = sv_str
                    filter_descriptions.append(f"{clean_path.split('.')[-1]} = '{sv_str}'")
                    break

        # Also check explicit city/category patterns like "from <City>"
        if ("city" in col_fields or "address.city" in col_fields) and "city" not in filters and "address.city" not in filters:
            m_city = re.search(r"\b(?:from|in)\s+([a-zA-Z]+)\b", q_lower)
            if m_city:
                city_cand = m_city.group(1).capitalize()
                if city_cand.lower() not in {"the", "this", "collection", "database", "dataset", "january", "february", "march", "orders", "products", "customers"}:
                    target_city_field = "city" if "city" in col_fields else "address.city"
                    filters[target_city_field] = {"$regex": f"^{re.escape(city_cand)}$", "$options": "i"}
                    filter_descriptions.append(f"city = '{city_cand}'")

        # Month filter
        months_mentioned = [
            m.capitalize()
            for m in ("january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december")
            if re.search(rf"\b{m}\b", q_lower)
        ]
        if months_mentioned and "month" in col_fields:
            filters["month"] = {"$in": months_mentioned} if len(months_mentioned) > 1 else months_mentioned[0]
            filter_descriptions.append(f"month in {months_mentioned}")

        # 6. Determine Exact Intent & Build MongoDB Pipeline
        # 6A. COUNT ("how many products?", "how many data are there in the collection", "count orders", "number of students")
        if re.search(
            r"\b(how many|count|total number of|number of|total records|total documents|total products|total customers|total orders|total employees|total students)\b",
            q_lower,
        ) and not group_field:
            return QueryPlan(
                original_question=question,
                normalized_question=normalized,
                intent="COUNT",
                confidence=0.98,
                source_id=source_id,
                source_name=source_name,
                collection=col_name,
                filters=filters,
                filter_descriptions=filter_descriptions,
                limit=10,
                operation="aggregate",
                aggregation_op="count",
                presentation_type="kpi",
            )

        # 6B. TOP_N / BOTTOM_N ("top 5 products by price", "bottom 3 products by stock", "5 most expensive products")
        m_top = re.search(r"\b(?:top|first|highest)\s+(\d+)\b", q_lower)
        m_bottom = re.search(r"\b(?:bottom|lowest|cheapest|least)\s+(\d+)\b", q_lower)
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
                target_fields=top_level_fields[:8],
                metric_field=sort_f,
                filters=filters,
                filter_descriptions=filter_descriptions,
                sort={sort_f: 1 if is_bottom else -1},
                limit=n_val,
                operation="aggregate",
                presentation_type="ranked_table",
            )

        # 6C. MAXIMUM / MINIMUM (Single superlative question: "what is the most expensive product?", "which product has the highest price?", "cheapest product")
        is_superlative_max = bool(
            re.search(
                r"\b(most expensive|highest|maximum|max|best selling|top earner|richest|largest|biggest)\b",
                q_lower,
            )
            and not re.search(r"\b(top\s+\d+|by\s+department|by\s+category|by\s+month)\b", q_lower)
        )
        is_superlative_min = bool(
            re.search(
                r"\b(least expensive|cheapest|lowest|minimum|min|smallest)\b",
                q_lower,
            )
            and not re.search(r"\b(bottom\s+\d+|by\s+department|by\s+category|by\s+month)\b", q_lower)
        )
        if (is_superlative_max or is_superlative_min) and primary_metric:
            # If user asked "show expensive products" (plural without "most"/"what is the"/"which is the"), treat as FILTER/SORT table;
            # If user asked "what is the most expensive product?" or "what is the highest product price?", return MAXIMUM/MINIMUM (limit=1)
            sort_dir = -1 if is_superlative_max else 1
            return QueryPlan(
                original_question=question,
                normalized_question=normalized,
                intent="MAXIMUM" if is_superlative_max else "MINIMUM",
                confidence=0.97,
                source_id=source_id,
                source_name=source_name,
                collection=col_name,
                target_fields=top_level_fields[:8],
                metric_field=primary_metric,
                filters=filters,
                filter_descriptions=filter_descriptions,
                sort={primary_metric: sort_dir},
                limit=1,
                operation="aggregate",
                aggregation_op="max" if is_superlative_max else "min",
                presentation_type="detail",
            )

        # 6D. COMPARISON ("compare products by price and units sold", "compare sales between January and February")
        if re.search(r"\b(compare|comparison|versus|vs\.?|against)\b", q_lower):
            return QueryPlan(
                original_question=question,
                normalized_question=normalized,
                intent="COMPARISON",
                confidence=0.95,
                source_id=source_id,
                source_name=source_name,
                collection=col_name,
                target_fields=top_level_fields[:8],
                metric_field=primary_metric,
                secondary_metric_field=secondary_metric,
                group_field=group_field,
                filters=filters,
                filter_descriptions=filter_descriptions,
                limit=25,
                operation="aggregate",
                presentation_type="comparison",
            )

        # 6E. AVERAGE / SUM / GROUP_BY / TREND
        is_avg = bool(re.search(r"\b(average|avg|mean)\b", q_lower))
        is_sum = bool(re.search(r"\b(sum|total\s+(?:revenue|sales|amount|spent|salary|stock|units))\b", q_lower))
        is_trend = bool(re.search(r"\b(trend|monthly|by month|over time)\b", q_lower))

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
                target_fields=top_level_fields[:8],
                metric_field=primary_metric,
                group_field=group_field or ("month" if is_trend and "month" in col_fields else None),
                filters=filters,
                filter_descriptions=filter_descriptions,
                limit=50,
                operation="aggregate",
                aggregation_op=agg_op,
                presentation_type="chart" if (group_field or is_trend) else "kpi",
            )

        # 6F. DISTINCT_VALUES ("unique categories", "distinct cities")
        if re.search(r"\b(distinct|unique|different)\b", q_lower):
            dist_field = group_field or (categorical_fields[0] if categorical_fields else top_level_fields[0])
            return QueryPlan(
                original_question=question,
                normalized_question=normalized,
                intent="DISTINCT_VALUES",
                confidence=0.95,
                source_id=source_id,
                source_name=source_name,
                collection=col_name,
                target_fields=[dist_field],
                group_field=dist_field,
                filters=filters,
                filter_descriptions=filter_descriptions,
                limit=50,
                operation="aggregate",
                presentation_type="table",
            )

        # 6G. EXPLICIT SORT ("show products sorted by stock", "order customers by total_spent")
        if re.search(r"\b(sort|sorted|order|ordered)\b", q_lower) or ("expensive" in q_lower and not is_superlative_max):
            sort_f = primary_metric or (top_level_fields[0] if top_level_fields else "_id")
            is_asc = bool(re.search(r"\b(asc|ascending|lowest to highest|low to high|smallest)\b", q_lower))
            # If user asked "show products sorted by stock", default ascending or descending naturally
            if "stock" in sort_f.lower() and not re.search(r"\b(desc|descending|highest)\b", q_lower):
                sort_dir = 1 if is_asc else -1
            else:
                sort_dir = 1 if is_asc else -1
            return QueryPlan(
                original_question=question,
                normalized_question=normalized,
                intent="SORT",
                confidence=0.96,
                source_id=source_id,
                source_name=source_name,
                collection=col_name,
                target_fields=top_level_fields[:8],
                metric_field=sort_f,
                filters=filters,
                filter_descriptions=filter_descriptions,
                sort={sort_f: sort_dir},
                limit=50,
                operation="aggregate",
                presentation_type="table",
            )

        # 6H. FILTER ("show me products above 50000", "show customers from Bangalore")
        if filters:
            return QueryPlan(
                original_question=question,
                normalized_question=normalized,
                intent="FILTER",
                confidence=0.96,
                source_id=source_id,
                source_name=source_name,
                collection=col_name,
                target_fields=top_level_fields[:8],
                metric_field=primary_metric,
                filters=filters,
                filter_descriptions=filter_descriptions,
                sort=None,  # DO NOT arbitrarily sort/rank unless asked
                limit=50,
                operation="aggregate",
                presentation_type="table",
            )

        # 6I. LIST_RECORDS / SEARCH ("show me data related to product", "show me products", "tell me about the customers")
        # CRITICAL RULE: NEVER add an unrequested price sort or Top Result ranking!
        return QueryPlan(
            original_question=question,
            normalized_question=normalized,
            intent="LIST_RECORDS",
            confidence=0.97,
            source_id=source_id,
            source_name=source_name,
            collection=col_name,
            target_fields=top_level_fields[:8],
            metric_field=None,
            filters={},
            filter_descriptions=[],
            sort=None,
            limit=50,
            operation="aggregate",
            presentation_type="table",
        )

    def compile_to_mongo_query(self, plan: QueryPlan) -> dict[str, Any]:
        """Compiles a structured QueryPlan into an executable MongoDB aggregation dictionary."""
        if not plan.collection:
            raise ValueError("QueryPlan has no target collection.")

        pipeline: list[dict[str, Any]] = []
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

        if plan.intent in ("GROUP_BY", "TREND", "DISTRIBUTION") or (plan.intent in ("AVERAGE", "SUM") and plan.group_field):
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
            # Entity-level comparison across two metrics (e.g. "compare products by price and units sold")
            proj: dict[str, Any] = {"_id": 0}
            # Include identifier/name columns + compared metrics
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

        # Standard projection for LIST_RECORDS, FILTER, SORT, TOP_N, BOTTOM_N, MAXIMUM, MINIMUM
        if plan.sort:
            pipeline.append({"$sort": plan.sort})
        pipeline.append({"$limit": plan.limit})

        proj = {"_id": 0}
        for f in plan.target_fields[:8]:
            proj[f] = 1
        if len(proj) > 1:
            pipeline.append({"$project": proj})

        return {
            "collection": plan.collection,
            "operation": "aggregate",
            "pipeline": pipeline,
            "limit": plan.limit,
        }
