import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class StructuredFilter:
    raw_field: str
    operator: str  # "eq", "ne", "gt", "gte", "lt", "lte", "in"
    value: Any
    source_phrase: str
    is_negated: bool = False


KNOWN_STATUS_VALUES = {
    "verified": "verified",
    "unverified": "unverified",
    "pending": "pending",
    "active": "active",
    "inactive": "inactive",
    "completed": "completed",
    "cancelled": "cancelled",
    "canceled": "cancelled",
    "processing": "processing",
    "delivered": "delivered",
    "shipped": "shipped",
    "approved": "approved",
    "rejected": "rejected",
    "open": "open",
    "closed": "closed",
    "paid": "paid",
    "unpaid": "unpaid",
    "successful": "successful",
    "failed": "failed",
}

CITY_SYNONYMS: dict[str, list[str]] = {
    "bangalore": ["Bangalore", "Bengaluru"],
    "bengaluru": ["Bangalore", "Bengaluru"],
    "mumbai": ["Mumbai", "Bombay"],
    "bombay": ["Mumbai", "Bombay"],
    "chennai": ["Chennai", "Madras"],
    "madras": ["Chennai", "Madras"],
    "kolkata": ["Kolkata", "Calcutta"],
    "calcutta": ["Kolkata", "Calcutta"],
    "delhi": ["Delhi", "New Delhi"],
    "new delhi": ["Delhi", "New Delhi"],
    "hyderabad": ["Hyderabad"],
    "pune": ["Pune"],
}


class SemanticFilterExtractor:
    """
    Schema-Aware Semantic Filter Extractor.
    Extracts structured filters from natural language questions
    independent of sample values cache, preserving exact user intent.
    """

    @classmethod
    def extract_filters(cls, question: str) -> list[StructuredFilter]:
        if not question or not question.strip():
            return []

        text = question.strip()
        low = text.lower()
        filters: list[StructuredFilter] = []
        captured_spans: list[tuple[int, int]] = []

        def is_overlapping(start: int, end: int) -> bool:
            return any(max(start, s) < min(end, e) for s, e in captured_spans)

        # 1. Explicit Field-Value Comparisons:
        # e.g., "whose status is verified", "who's status is verified", "where status = pending",
        # "with verification_status equal to verified", "having status: completed"
        eq_pattern = re.compile(
            r"\b(?:whose|who's|who\s+is|where|with|having)\s+([a-zA-Z_.]+)\s+(?:is|are|=|equals|equal\s+to|==|:)\s*(not\s+|!=|<>)?([a-zA-Z0-9_.\-]+|\"[^\"]+\"|'[^']+')\b",
            re.IGNORECASE,
        )
        for m in eq_pattern.finditer(low):
            start, end = m.span()
            if is_overlapping(start, end):
                continue
            raw_field = m.group(1).strip()
            neg = bool(m.group(2) and m.group(2).strip() in ("not", "!=", "<>"))
            raw_val = m.group(3).strip().strip("\"'")
            if raw_val.lower() in ("the", "a", "an", "all", "records", "data", "documents"):
                continue

            op = "ne" if neg else "eq"
            filters.append(
                StructuredFilter(
                    raw_field=raw_field,
                    operator=op,
                    value=raw_val,
                    source_phrase=m.group(0),
                    is_negated=neg,
                )
            )
            captured_spans.append((start, end))

        # 1B. Direct syntax comparisons: "status = verified", "status: pending", "amount > 50000"
        syntax_pattern = re.compile(
            r"\b([a-zA-Z_.]+)\s*(=|==|:|!=|<>|>=|<=|>|<)\s*([a-zA-Z0-9_.\-]+|\"[^\"]+\"|'[^']+')\b",
            re.IGNORECASE,
        )
        for m in syntax_pattern.finditer(low):
            start, end = m.span()
            if is_overlapping(start, end):
                continue
            raw_field = m.group(1).strip()
            sym = m.group(2).strip()
            raw_val = m.group(3).strip().strip("\"'")

            # Avoid false positives like "http://", "10:30"
            if raw_field in ("http", "https") or (raw_val.isdigit() and sym == ":"):
                continue

            op_map = {
                "=": "eq",
                "==": "eq",
                ":": "eq",
                "!=": "ne",
                "<>": "ne",
                ">": "gt",
                ">=": "gte",
                "<": "lt",
                "<=": "lte",
            }
            op = op_map.get(sym, "eq")

            # Try numeric parse if operator is numeric or val looks numeric
            num_val: Any = raw_val
            if op in ("gt", "gte", "lt", "lte") or re.match(r"^\d+(?:\.\d+)?$", raw_val):
                try:
                    num_val = float(raw_val)
                    if num_val.is_integer():
                        num_val = int(num_val)
                except ValueError:
                    num_val = raw_val

            filters.append(
                StructuredFilter(
                    raw_field=raw_field,
                    operator=op,
                    value=num_val,
                    source_phrase=m.group(0),
                    is_negated=(op == "ne"),
                )
            )
            captured_spans.append((start, end))

        # 2. Adjectival / Standalone Status Mention:
        # e.g., "verified menu items", "all verified records", "top 10 verified customers",
        # "pending delivery orders", "completed orders", "active users"
        has_status_filter = any(f.raw_field.lower() == "status" for f in filters)
        if not has_status_filter:
            for word, canonical_val in KNOWN_STATUS_VALUES.items():
                m_word = re.search(rf"\b{re.escape(word)}\b", low)
                if m_word:
                    start, end = m_word.span()
                    if is_overlapping(start, end):
                        continue
                    # Check if negated ("not verified", "unverified")
                    neg = False
                    if word == "unverified":
                        neg = True
                        canonical_val = "verified"
                    elif re.search(rf"\bnot\s+{re.escape(word)}\b", low):
                        neg = True

                    op = "ne" if neg else "eq"
                    filters.append(
                        StructuredFilter(
                            raw_field="status",
                            operator=op,
                            value=canonical_val,
                            source_phrase=m_word.group(0),
                            is_negated=neg,
                        )
                    )
                    captured_spans.append((start, end))
                    break

        # 3. Location / City Filters:
        # e.g., "from Bangalore", "in Mumbai", "Bangalore customers"
        has_city_filter = any(f.raw_field.lower() in ("city", "address.city") for f in filters)
        if not has_city_filter:
            for city_key, city_vals in CITY_SYNONYMS.items():
                m_city = re.search(rf"\b{re.escape(city_key)}\b", low)
                if m_city:
                    start, end = m_city.span()
                    if is_overlapping(start, end):
                        continue
                    filters.append(
                        StructuredFilter(
                            raw_field="city",
                            operator="in" if len(city_vals) > 1 else "eq",
                            value=city_vals if len(city_vals) > 1 else city_vals[0],
                            source_phrase=m_city.group(0),
                        )
                    )
                    captured_spans.append((start, end))
                    break

        if not any(f.raw_field.lower() in ("city", "address.city") for f in filters):
            m_from = re.search(r"\b(?:from|in)\s+([a-zA-Z]+)\b", low)
            if m_from:
                cand = m_from.group(1).capitalize()
                stop_words = {
                    "the",
                    "this",
                    "collection",
                    "database",
                    "dataset",
                    "order",
                    "orders",
                    "menu",
                    "item",
                    "items",
                    "table",
                    "record",
                    "records",
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
                }
                if cand.lower() not in stop_words:
                    filters.append(
                        StructuredFilter(
                            raw_field="city",
                            operator="eq",
                            value=cand,
                            source_phrase=m_from.group(0),
                        )
                    )

        # 3B. Inventory / Stock conditions (e.g. "low stock", "out of stock")
        if re.search(r"\b(low\s+stock|low\s+inventory)\b", low):
            filters.append(
                StructuredFilter(
                    raw_field="stock",
                    operator="lt",
                    value=25,
                    source_phrase="low stock",
                )
            )
        elif re.search(r"\b(out\s+of\s+stock|zero\s+stock|no\s+stock)\b", low):
            filters.append(
                StructuredFilter(
                    raw_field="stock",
                    operator="lte",
                    value=0,
                    source_phrase="out of stock",
                )
            )

        # 4. Numeric Threshold Filters:
        # e.g., "above 50000", "over 50k", "greater than 500", "below 200", "at least 1000", "5 lakh"
        has_num_threshold = any(f.operator in ("gt", "gte", "lt", "lte") for f in filters)
        if not has_num_threshold:
            clean_num_text = low.replace(",", "").replace("₹", "").replace("$", "")
            m_lakh = re.search(
                r"(?:above|over|more than|greater than|exceeding|>|below|under|less than|fewer than|<|at least|at most|>=|<=)?\s*(\d+(?:\.\d+)?)\s*lakh",
                clean_num_text,
            )
            m_k = re.search(
                r"(?:above|over|more than|greater than|exceeding|>|below|under|less than|fewer than|<|at least|at most|>=|<=)?\s*(\d+(?:\.\d+)?)\s*k\b",
                clean_num_text,
            )
            m_comp = re.search(
                r"\b(above|over|more than|greater than|exceeding|>|below|under|less than|fewer than|<|at least|at most|>=|<=)\s*(\d+(?:\.\d+)?)\b",
                clean_num_text,
            )

            thresh_val: float | None = None
            comp_word = "above"

            if m_lakh:
                thresh_val = float(m_lakh.group(1)) * 100000.0
                m_comp_sub = re.search(
                    r"\b(above|over|more than|greater than|exceeding|>|below|under|less than|fewer than|<|at least|at most|>=|<=)",
                    m_lakh.group(0),
                )
                if m_comp_sub:
                    comp_word = m_comp_sub.group(1)
            elif m_k:
                thresh_val = float(m_k.group(1)) * 1000.0
                m_comp_sub = re.search(
                    r"\b(above|over|more than|greater than|exceeding|>|below|under|less than|fewer than|<|at least|at most|>=|<=)",
                    m_k.group(0),
                )
                if m_comp_sub:
                    comp_word = m_comp_sub.group(1)
            elif m_comp:
                comp_word = m_comp.group(1)
                thresh_val = float(m_comp.group(2))

            if thresh_val is not None:
                if any(w in comp_word for w in ("above", "over", "more than", "greater than", "exceeding", ">")):
                    op = "gt"
                elif any(w in comp_word for w in ("below", "under", "less than", "fewer than", "<")):
                    op = "lt"
                elif "at least" in comp_word or ">=" in comp_word:
                    op = "gte"
                elif "at most" in comp_word or "<=" in comp_word:
                    op = "lte"
                else:
                    op = "eq"

                # Check if a specific numeric field name is in query
                target_num_field = "amount"
                m_field = re.search(
                    r"\b(price|amount|total_amount|total|salary|score|rating|balance|quantity|stock)\b",
                    low,
                )
                if m_field:
                    target_num_field = m_field.group(1)

                val = int(thresh_val) if thresh_val.is_integer() else thresh_val
                filters.append(
                    StructuredFilter(
                        raw_field=target_num_field,
                        operator=op,
                        value=val,
                        source_phrase=f"{comp_word} {thresh_val}",
                    )
                )

        return filters

    @classmethod
    def resolve_filter_to_collection(
        cls,
        st_filter: StructuredFilter,
        col_columns: list[dict[str, Any]],
        primary_numeric_field: str | None = None,
    ) -> tuple[str | None, dict[str, Any] | None, str | None]:
        """
        Validates whether `st_filter.raw_field` exists in `col_columns`.
        Returns:
            (target_field_name, mongo_match_dict, description) if field exists.
            (None, None, raw_field) if field does NOT exist (Field Missing).
        """
        col_fields = {c["name"]: c.get("data_type", "String") for c in col_columns}
        rf = st_filter.raw_field.strip()

        # Find target field in collection columns
        matched_target_field: str | None = None

        if rf in col_fields:
            matched_target_field = rf
        else:
            # Case-insensitive check
            for cname in col_fields:
                if cname.lower() == rf.lower():
                    matched_target_field = cname
                    break

        # Nested mapping for city: e.g. "city" -> "address.city"
        if not matched_target_field and rf == "city" and "address.city" in col_fields:
            matched_target_field = "address.city"

        # Stock / Inventory mapping: e.g. "stock" -> "stock_quantity" / "inventory"
        if not matched_target_field and rf in ("stock", "inventory", "quantity"):
            for cand in ("stock", "stock_quantity", "inventory", "quantity"):
                if cand in col_fields:
                    matched_target_field = cand
                    break

        # Numeric field fallback if user specified "amount" or generic threshold but collection has a specific numeric field
        if not matched_target_field and st_filter.operator in ("gt", "gte", "lt", "lte"):
            if primary_numeric_field and primary_numeric_field in col_fields:
                matched_target_field = primary_numeric_field
            elif "amount" in col_fields:
                matched_target_field = "amount"
            elif "price" in col_fields:
                matched_target_field = "price"
            elif "total" in col_fields:
                matched_target_field = "total"

        # If field still does not exist, fail-closed: return None
        if not matched_target_field:
            return None, None, rf

        # Construct MongoDB match dictionary and description
        clean_path = matched_target_field.replace("[].", ".")
        val = st_filter.value
        op = st_filter.operator

        mongo_cond: Any = None
        desc_op = "="

        if op == "eq":
            if isinstance(val, str):
                mongo_cond = {"$regex": f"^{re.escape(val)}$", "$options": "i"}
                desc_op = "="
            else:
                mongo_cond = val
                desc_op = "="
        elif op == "ne":
            if isinstance(val, str):
                mongo_cond = {"$not": {"$regex": f"^{re.escape(val)}$", "$options": "i"}}
                desc_op = "!="
            else:
                mongo_cond = {"$ne": val}
                desc_op = "!="
        elif op == "gt":
            mongo_cond = {"$gt": val}
            desc_op = ">"
        elif op == "gte":
            mongo_cond = {"$gte": val}
            desc_op = ">="
        elif op == "lt":
            mongo_cond = {"$lt": val}
            desc_op = "<"
        elif op == "lte":
            mongo_cond = {"$lte": val}
            desc_op = "<="
        elif op == "in":
            if isinstance(val, list):
                mongo_cond = {"$in": val}
                desc_op = "in"
            else:
                mongo_cond = val
                desc_op = "="

        formatted_val = f"'{val}'" if isinstance(val, str) else str(val)
        desc = f"{clean_path.split('.')[-1]} {desc_op} {formatted_val}"

        return matched_target_field, {clean_path: mongo_cond}, desc
