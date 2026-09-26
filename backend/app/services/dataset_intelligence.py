import re
import time
from dataclasses import dataclass, field
from typing import Any

from app.services.schema_service import MongoSchemaService
from app.services.source_manager import SourceManager
from app.services.semantic_filter_extractor import SemanticFilterExtractor

COLLECTION_DESCRIPTIONS: dict[str, str] = {
    "products": "Product catalog with pricing, categories, stock levels, ratings, and units sold",
    "customers": "Customer profiles with city, state, contact info, loyalty tiers, and total spend",
    "orders": "E-commerce order transactions with customer links, line items, dates, and totals",
    "employees": "Organization directory with departments, roles, salaries, and performance scores",
    "students": "Campus academic records with majors, GPA, attendance percentage, and credits",
}

KNOWN_COLLECTION_ALIASES: dict[str, set[str]] = {
    "products": {"product", "products", "prodcut", "prodcuts", "porduct", "porducts", "item", "items", "catalog", "merchandise"},
    "customers": {"customer", "customers", "custmer", "custmers", "costumer", "costumers", "client", "clients", "buyer", "buyers"},
    "orders": {"order", "orders", "ordr", "ordrs", "purchase", "purchases"},
    "employees": {"employee", "employees", "employe", "employes", "emplyee", "staff", "worker", "workers", "personnel"},
    "students": {"student", "students", "studnt", "studnts", "stduent", "learner", "learners", "pupil", "pupils"},
    "patients": {"patient", "patients"},
    "doctors": {"doctor", "doctors", "physician", "physicians"},
    "appointments": {"appointment", "appointments", "visit", "visits"},
    "prescriptions": {"prescription", "prescriptions", "medication", "medications"},
    "lab_results": {"lab_result", "lab_results", "lab", "labs", "test_result", "test_results"},
    "accounts": {"account", "accounts"},
    "transactions": {"transaction", "transactions", "transfer", "transfers"},
    "investments": {"investment", "investments", "portfolio", "portfolios"},
    "branches": {"branch", "branches"},
    "shipments": {"shipment", "shipments", "freight", "cargo"},
    "vehicles": {"vehicle", "vehicles", "truck", "trucks", "fleet"},
    "drivers": {"driver", "drivers", "courier", "couriers"},
    "warehouses": {"warehouse", "warehouses", "depot", "depots"},
    "deliveries": {"delivery", "deliveries"},
    "courses": {"course", "courses", "class", "classes"},
    "faculty": {"faculty", "professor", "professors", "instructor", "instructors"},
    "enrollments": {"enrollment", "enrollments", "registration", "registrations"},
    "examinations": {"examination", "examinations", "exam", "exams"},
    "shoppers": {"shopper", "shoppers"},
    "catalog_items": {"catalog_item", "catalog_items"},
    "carts": {"cart", "carts", "basket", "baskets"},
    "reviews": {"review", "reviews", "feedback"},
}

# Domain nouns that, if NOT present in the currently active dataset, trigger not_found clarification
COMMON_EXTERNAL_ENTITIES = {
    "teacher", "teachers", "professor", "professors", "faculty",
    "hospital", "hospitals", "doctor", "doctors", "patient", "patients",
    "appointment", "appointments", "prescription", "prescriptions",
    "account", "accounts", "investment", "investments", "branch", "branches",
    "shipment", "shipments", "delivery", "deliveries", "driver", "drivers",
    "flight", "flights", "airline", "airlines", "hotel", "hotels",
    "movie", "movies", "song", "songs", "book", "books",
    "vehicle", "vehicles", "car", "cars", "supplier", "suppliers",
    "vendor", "vendors", "invoice", "invoices", "warehouse", "warehouses",
    "student", "students", "employee", "employees", "product", "products",
    "customer", "customers", "order", "orders", "course", "courses",
}


@dataclass
class CollectionResolutionResult:
    status: str  # "resolved" | "multi_collection" | "ambiguous" | "dataset_level" | "not_found" | "unrelated"
    candidates: list[dict[str, Any]] = field(default_factory=list)
    selected_collection: str | None = None
    secondary_collection: str | None = None
    confidence: float = 0.0
    reason: str = ""
    evidence: list[str] = field(default_factory=list)
    missing_entity: str | None = None
    is_collection_switch: bool = False


class DatasetIntelligenceService:
    """
    Top-level Dataset Context Provider & Metadata Cache.
    Provides complete collection catalog, field summaries, document counts,
    and cross-collection relationship hints without scanning full collections.
    """

    _catalog_cache: dict[str, tuple[float, dict[str, Any]]] = {}
    _CACHE_TTL_SEC = 15.0

    def __init__(
        self,
        schema_service: MongoSchemaService | None = None,
        source_manager: SourceManager | None = None,
    ):
        self.schema_service = schema_service or MongoSchemaService()
        self.source_manager = source_manager or SourceManager()

    @classmethod
    def invalidate_cache(cls, source_id: str | None = None) -> None:
        if source_id:
            cls._catalog_cache.pop(source_id, None)
        else:
            cls._catalog_cache.clear()

    def get_dataset_catalog(self, source_id: str | None = None) -> dict[str, Any]:
        from app.core.mongodb import MongoDBManager

        effective_source_id = source_id or MongoDBManager.get_active_source_id()
        cache_key = effective_source_id or "__active__"
        now = time.monotonic()
        cached = self._catalog_cache.get(cache_key)
        if cached and (now - cached[0]) < self._CACHE_TTL_SEC:
            return cached[1]

        schema = self.schema_service.get_schema(effective_source_id)
        raw_tables = schema.get("tables", [])
        source_meta = self.source_manager.get_source(effective_source_id) if effective_source_id else None
        if not source_meta:
            all_sources = self.source_manager.list_sources()
            source_meta = all_sources[0] if all_sources else None

        dataset_name = (
            source_meta.database_name
            if source_meta and getattr(source_meta, "database_name", None)
            else "demo_database"
        )
        display_name = (
            source_meta.name
            if source_meta
            else "Enterprise & Campus Intelligence (demo_database)"
        )
        resolved_source_id = source_meta.source_id if source_meta else (effective_source_id or "demo-source-id")


        collections_catalog: list[dict[str, Any]] = []
        total_docs = 0

        for tbl in raw_tables:
            cname = tbl["name"]
            base_name = cname.split("_")[-1].lower()
            doc_cnt = int(tbl.get("document_count", 0))
            total_docs += doc_cnt
            cols = tbl.get("columns", [])
            top_fields = [
                c["name"]
                for c in cols
                if c["name"] != "_id" and "." not in c["name"] and "[]" not in c["name"]
            ]
            collections_catalog.append(
                {
                    "name": cname,
                    "display_name": cname.replace("_", " ").title(),
                    "document_count": doc_cnt,
                    "field_count": len(cols),
                    "fields_preview": top_fields[:6],
                    "description": COLLECTION_DESCRIPTIONS.get(
                        base_name,
                        f"MongoDB collection with {doc_cnt:,} documents and {len(cols)} fields",
                    ),
                    "columns": cols,
                    "indexes": tbl.get("indexes", []),
                    "foreign_keys": tbl.get("foreign_keys", []),
                }
            )

        # Infer cross-collection relationships (e.g. customer_id in orders & customers)
        relationships: list[dict[str, str]] = []
        col_field_map = {
            c["name"]: {f["name"] for f in c["columns"]} for c in collections_catalog
        }
        for c1 in collections_catalog:
            for c2 in collections_catalog:
                if c1["name"] >= c2["name"]:
                    continue
                shared_ids = [
                    f
                    for f in col_field_map[c1["name"]].intersection(col_field_map[c2["name"]])
                    if f.endswith("_id") and f != "_id"
                ]
                for sid in shared_ids:
                    relationships.append(
                        {
                            "from_collection": c1["name"],
                            "to_collection": c2["name"],
                            "join_field": sid,
                        }
                    )

        catalog = {
            "dataset": {
                "source_id": resolved_source_id,
                "name": dataset_name,
                "display_name": display_name,
                "collection_count": len(collections_catalog),
                "total_documents": total_docs,
            },
            "collections": collections_catalog,
            "relationships": relationships,
        }
        self._catalog_cache[cache_key] = (now, catalog)
        return catalog


class CollectionIntelligenceService:
    """
    Provides deep collection-level schema inspection, field semantics, and sample values
    ONLY after collection resolution is complete.
    """

    def __init__(self, dataset_service: DatasetIntelligenceService):
        self.dataset_service = dataset_service

    def get_collection_schema(
        self, collection_name: str, source_id: str | None = None
    ) -> dict[str, Any] | None:
        catalog = self.dataset_service.get_dataset_catalog(source_id)
        for col in catalog["collections"]:
            if col["name"].lower() == collection_name.lower():
                return col
        return None


class CollectionResolver:
    """
    Dedicated Dataset -> Collection Resolution & Ambiguity Engine.
    Determines whether a user question:
      1. Targets the dataset/metadata as a whole (`dataset_level`)
      2. Explicitly or semantically resolves to a single collection (`resolved`)
      3. Spans multiple related collections (`multi_collection`)
      4. Switches collections in a conversational correction (`resolved` with `is_collection_switch=True`)
      5. Mentions a non-existent collection (`not_found`)
      6. Is ambiguous across multiple collections in the dataset (`ambiguous` -> triggers Clarification UI)
    Never silently guesses `collections[0]` (`products`) when the question is ambiguous!
    """

    HIGH_CONFIDENCE_THRESHOLD = 0.75

    def __init__(self, dataset_service: DatasetIntelligenceService):
        self.dataset_service = dataset_service

    def resolve(
        self,
        question: str,
        source_id: str | None = None,
        explicit_collection: str | None = None,
        conversation_context: dict[str, Any] | None = None,
    ) -> CollectionResolutionResult:
        catalog = self.dataset_service.get_dataset_catalog(source_id)
        collections: list[dict[str, Any]] = catalog["collections"]
        if not collections:
            return CollectionResolutionResult(
                status="unrelated",
                confidence=0.95,
                reason="Dataset contains no collections.",
            )

        q_raw = question.strip()
        q_lower = q_raw.lower()
        q_clean = re.sub(r"[^\w\s]", " ", q_lower).strip()
        q_words = set(q_clean.split())

        # Check if question specifies a filter field (e.g. status)
        extracted_filters = SemanticFilterExtractor.extract_filters(q_raw)
        filter_req_field = extracted_filters[0].raw_field if extracted_filters else None

        candidate_cards = []
        for c in collections:
            col_col_names = {f["name"].lower() for f in c.get("columns", [])}
            col_col_names.update(f["name"].split(".")[-1].lower() for f in c.get("columns", []))
            has_filter_field = (filter_req_field.lower() in col_col_names) if filter_req_field else None
            filter_status = f"{filter_req_field} ✓" if has_filter_field is True else (f"{filter_req_field} ✕" if has_filter_field is False else None)

            desc = c["description"]
            if has_filter_field is True:
                desc = f"Contains '{filter_req_field}' field • {desc}"
            elif has_filter_field is False:
                desc = f"No '{filter_req_field}' field • {desc}"

            candidate_cards.append(
                {
                    "source_id": catalog["dataset"]["source_id"],
                    "collection": c["name"],
                    "name": c["display_name"],
                    "document_count": c["document_count"],
                    "field_count": c["field_count"],
                    "fields_preview": c["fields_preview"],
                    "description": desc,
                    "has_filter_field": has_filter_field,
                    "filter_field_status": filter_status,
                }
            )

        if filter_req_field:
            candidate_cards.sort(
                key=lambda card: (card.get("has_filter_field") is True, card.get("document_count", 0)),
                reverse=True,
            )

        col_by_name = {c["name"].lower(): c for c in collections}

        # 0. Explicit collection chosen by user via Clarification Card or Change Collection UI
        if explicit_collection and explicit_collection.lower() in col_by_name:
            matched_col = col_by_name[explicit_collection.lower()]
            return CollectionResolutionResult(
                status="resolved",
                candidates=candidate_cards,
                selected_collection=matched_col["name"],
                confidence=1.0,
                reason="User explicitly selected collection.",
                evidence=[f"selected_collection={matched_col['name']}"],
            )

        # 1. Check if the user is typing a collection selection or conversational correction
        # e.g., "customers", "I meant customers", "actually orders", "use employees instead", "switch to students"
        correction_match = re.match(
            r"^(?:actually|i\s+mean|i\s+meant|use|switch\s+to|change\s+to|no\s*,?\s*|try|how\s+about|what\s+about|show\s+me\s+instead)?\s*([a-zA-Z_]+)\s*(?:instead|collection|please|now)?$",
            q_clean,
        )
        if correction_match:
            cand_token = correction_match.group(1).lower()
            for col in collections:
                cname = col["name"].lower()
                base = cname.split("_")[-1]
                aliases = KNOWN_COLLECTION_ALIASES.get(base, {cname, base, base.rstrip("s")})
                if cand_token in aliases:
                    return CollectionResolutionResult(
                        status="resolved",
                        candidates=candidate_cards,
                        selected_collection=col["name"],
                        confidence=0.99,
                        reason=f"Conversational collection selection/switch to '{col['name']}'.",
                        evidence=[f"conversational_switch:{cand_token}"],
                        is_collection_switch=True,
                    )

        # 2. Check for explicit collection mentions in the question
        explicitly_matched_cols: list[dict[str, Any]] = []
        for col in collections:
            cname = col["name"].lower()
            base = cname.split("_")[-1]
            aliases = KNOWN_COLLECTION_ALIASES.get(base, {cname, base, base.rstrip("s")})
            if any(re.search(rf"\b{re.escape(a)}\b", q_lower) for a in aliases if a):
                explicitly_matched_cols.append(col)

        # 2A. Multi-Collection Detection (e.g. "which customers placed the most orders?", "how many customers have orders?")
        if len(explicitly_matched_cols) >= 2:
            c_names = [c["name"] for c in explicitly_matched_cols]
            # Prefer orders + customers when both are mentioned
            primary = "orders" if "orders" in c_names else c_names[0]
            secondary = next((n for n in c_names if n != primary), c_names[1])
            return CollectionResolutionResult(
                status="multi_collection",
                candidates=candidate_cards,
                selected_collection=primary,
                secondary_collection=secondary,
                confidence=0.96,
                reason=f"Question spans multiple collections: {', '.join(c_names)}.",
                evidence=[f"multi_collection:{','.join(c_names)}"],
            )

        # 2B. Dataset-Level Questions (when NO specific collection is named)
        # e.g., "tell me about this dataset", "what collections are available?", "what data do I have?", "how many collections are there?"
        if not explicitly_matched_cols:
            is_dataset_meta = bool(
                re.search(
                    r"\b(what|which|list|show|available|all|how many)\b.*\b(collections|tables|datasets|sources)\b",
                    q_lower,
                )
                or re.search(
                    r"\b(info|information|overview|summary|about|describe|tell me about)\b.*\b(dataset|database|db|source|workspace)\b",
                    q_lower,
                )
                or re.search(
                    r"\b(what data do i have|what data is available|what is in this database|what is in this dataset|describe database|dataset overview)\b",
                    q_lower,
                )
            )
            if is_dataset_meta:
                return CollectionResolutionResult(
                    status="dataset_level",
                    candidates=candidate_cards,
                    confidence=0.98,
                    reason="Question asks about dataset-level overview or available collections.",
                    evidence=["dataset_meta_pattern"],
                )

        # 2C. Exact Single Collection Mentioned
        if len(explicitly_matched_cols) == 1:
            chosen = explicitly_matched_cols[0]
            return CollectionResolutionResult(
                status="resolved",
                candidates=candidate_cards,
                selected_collection=chosen["name"],
                confidence=0.98,
                reason=f"Question explicitly mentions collection '{chosen['name']}'.",
                evidence=[f"explicit_collection:{chosen['name']}"],
            )

        # 3. Check if user asked for a non-existent collection (e.g., "show teachers", "how many flights")
        found_external = q_words.intersection(COMMON_EXTERNAL_ENTITIES)
        if found_external:
            missing_name = sorted(found_external)[0]
            return CollectionResolutionResult(
                status="not_found",
                candidates=candidate_cards,
                confidence=0.95,
                reason=f"Collection '{missing_name}' does not exist in the active dataset.",
                missing_entity=missing_name,
            )

        # 4. Score Collections by Schema Field & Sample Value Evidence
        scores: dict[str, float] = {c["name"]: 0.0 for c in collections}
        evidence_map: dict[str, list[str]] = {c["name"]: [] for c in collections}

        distinctive_keywords = {
            "products": {"price", "stock", "units_sold", "expensive", "cheapest", "merchandise", "laptop", "workstation"},
            "customers": {"bangalore", "bengaluru", "mumbai", "delhi", "chennai", "hyderabad", "pune", "kolkata", "total_spent", "lakh", "loyalty_tier"},
            "orders": {"order_date", "january", "february", "march", "april", "may", "june", "delivered", "shipped"},
            "employees": {"salary", "department", "performance_score", "hired", "engineering", "compensation"},
            "students": {"gpa", "major", "attendance", "credits_completed", "semester"},
        }

        for col in collections:
            cname = col["name"]
            base = cname.split("_")[-1].lower()
            for kw in distinctive_keywords.get(base, set()):
                if re.search(rf"\b{re.escape(kw)}\b", q_lower):
                    scores[cname] += 0.85
                    evidence_map[cname].append(f"domain_keyword:{kw}")

            for cinfo in col.get("columns", []):
                f_leaf = cinfo["name"].split(".")[-1].replace("[]", "").lower()
                if len(f_leaf) > 2 and f_leaf not in {"name", "status", "id", "type"}:
                    if re.search(rf"\b{re.escape(f_leaf)}\b", q_lower):
                        scores[cname] += 0.65
                        evidence_map[cname].append(f"field:{f_leaf}")
                for sv in cinfo.get("sample_values", []) or []:
                    sv_low = str(sv).strip().lower()
                    if len(sv_low) >= 3 and re.search(rf"\b{re.escape(sv_low)}\b", q_lower):
                        scores[cname] += 0.80
                        evidence_map[cname].append(f"sample_value:{sv_low}")

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        best_col_name, best_score = ranked[0]
        second_score = ranked[1][1] if len(ranked) > 1 else 0.0

        if best_score >= self.HIGH_CONFIDENCE_THRESHOLD and (best_score - second_score) >= 0.35:
            return CollectionResolutionResult(
                status="resolved",
                candidates=candidate_cards,
                selected_collection=best_col_name,
                confidence=min(0.95, best_score),
                reason=f"Unambiguously matched schema evidence for '{best_col_name}'.",
                evidence=evidence_map[best_col_name],
            )

        # 5. Check Active Conversational Context for Genuine Follow-Ups
        # e.g., User previously ran "show products" (so conversation_context has collection="products")
        # and now asks "how many?", "how many are there?", "what is the average price?", "only above 50000", "sort them by stock"
        prev_col = (conversation_context or {}).get("collection")
        if prev_col and str(prev_col).lower() in col_by_name:
            is_followup_phrasing = bool(
                re.search(
                    r"^(?:how many|how many are there|count them|what is the average|what is the highest|what is the lowest|only|filter|sort|sort them|order them|above|below|under|over|in|from|and|also|which one|which of them)\b",
                    q_clean,
                )
                or q_clean in {"how many", "how many are there", "count", "average", "highest", "lowest"}
            )
            # Note: If the user asks a brand new generic question like "how many data are there" or "how many data are there in the collection"
            # WITHOUT a follow-up pronoun and only if they explicitly want context or if it's a direct follow-up ("how many?", "only above 50000")
            if is_followup_phrasing and not re.search(r"\b(how many data|show me data|give me information)\b", q_clean):
                return CollectionResolutionResult(
                    status="resolved",
                    candidates=candidate_cards,
                    selected_collection=col_by_name[str(prev_col).lower()]["name"],
                    confidence=0.90,
                    reason=f"Resolved from active conversation context ('{prev_col}').",
                    evidence=[f"conversation_context:{prev_col}"],
                )

        # 6. If the dataset only has 1 collection total, use it for data queries
        if len(collections) == 1:
            return CollectionResolutionResult(
                status="resolved",
                candidates=candidate_cards,
                selected_collection=collections[0]["name"],
                confidence=0.95,
                reason="Single collection in dataset.",
                evidence=["single_collection"],
            )

        # 7. Ambiguous Question Detection ("how many data are there", "how many records are there?", "show me the records", "give me information", "show me data")
        # NEVER silently pick `products` (collections[0])! Always ask the user which collection they want.
        data_intent_words = {
            "how", "many", "count", "number", "total", "data", "record", "records",
            "document", "documents", "entry", "entries", "row", "rows", "show",
            "list", "display", "get", "find", "give", "info", "information",
            "details", "average", "avg", "sum", "top", "highest", "lowest",
            "max", "min", "compare", "filter", "search", "collection",
        }
        if q_words.intersection(data_intent_words):
            return CollectionResolutionResult(
                status="ambiguous",
                candidates=candidate_cards,
                confidence=0.88,
                reason=f"Question does not specify which of the {len(collections)} collections to use.",
                evidence=["ambiguous_across_collections"],
            )

        return CollectionResolutionResult(
            status="unrelated",
            candidates=candidate_cards,
            confidence=0.95,
            reason="Question has no relationship to the active dataset.",
        )
