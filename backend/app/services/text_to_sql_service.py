import json
import re
from typing import Any

from app.services.mongo_validator import MongoQuerySafetyError, MongoQueryValidator
from app.services.schema_service import MongoSchemaService


def _parse_numeric_threshold(text: str) -> float | None:
    """
    Parses numeric values including Indian currency units ('1 lakh', '1,00,000', '50k', '3.5').
    """
    q = text.lower().replace(",", "").replace("₹", "").replace("$", "")
    m_lakh = re.search(r"(\d+(?:\.\d+)?)\s*lakh", q)
    if m_lakh:
        return float(m_lakh.group(1)) * 100000.0
    m_k = re.search(r"(\d+(?:\.\d+)?)\s*k\b", q)
    if m_k:
        return float(m_k.group(1)) * 1000.0
    # Ignore numbers that are part of "top 10" or years like "2025" when looking for filter thresholds
    q_no_top = re.sub(r"\b(top|limit|first|last)\s+\d+", "", q)
    m_num = re.search(r"(?:above|over|more than|greater than|exceeding|>|below|under|less than|<|=)\s*(\d+(?:\.\d+)?)", q_no_top)
    if m_num:
        return float(m_num.group(1))
    return None


class MongoQueryService:
    """
    Deterministic + Schema-Aware Natural Language to MongoDB Aggregation Pipeline Engine.
    Generates structured MongoDB queries (`aggregate`, `find`, `count`, `distinct`)
    without SQL intermediates.
    """

    def __init__(self, schema_service: MongoSchemaService | None = None):
        self.schema_service = schema_service or MongoSchemaService()

    def generate_structured_query(
        self, question: str, source_id: str | None = None
    ) -> dict[str, Any]:
        MongoQueryValidator.validate_question_safety(question)

        schema = self.schema_service.get_schema(source_id)
        collections = schema.get("tables", [])
        if not collections:
            raise ValueError("No MongoDB collections available to query.")

        q = question.strip()
        q_lower = q.lower()

        # Helper to find best matching collection by base name or field names
        def _find_collection(keywords: list[str]) -> dict[str, Any] | None:
            for kw in keywords:
                for col in collections:
                    cname = col["name"].lower()
                    if cname == kw or cname.endswith(f"_{kw}") or kw in cname:
                        return col
            return None

        # 1. Detect target collection from question keywords or schema field overlap
        target_col = None
        for col in collections:
            cname = col["name"].lower()
            base_name = cname.split("_")[-1]
            singular = base_name.rstrip("s")
            if re.search(rf"\b({ re.escape(cname) }|{ re.escape(base_name) }|{ re.escape(singular) })\b", q_lower):
                target_col = col
                break

        # Semantic domain mapping if collection name wasn't literally stated
        if not target_col:
            if any(w in q_lower for w in ("revenue", "product", "stock", "price", "category")):
                target_col = _find_collection(["products", "orders"])
            if not target_col and any(w in q_lower for w in ("spent", "customer", "tier", "lakh")):
                target_col = _find_collection(["customers", "orders"])
            if not target_col and any(w in q_lower for w in ("order", "sales", "january", "february", "march", "monthly", "month")):
                target_col = _find_collection(["orders", "sales", "products"])
            if not target_col and any(w in q_lower for w in ("salary", "employee", "role", "hired")):
                target_col = _find_collection(["employees", "staff"])
            if not target_col and any(w in q_lower for w in ("student", "gpa", "major", "enrollment", "credits")):
                target_col = _find_collection(["students"])

        # Fallback: match collection that has the highest overlap with column names mentioned in question
        if not target_col:
            best_score = 0
            for col in collections:
                score = 0
                for cinfo in col.get("columns", []):
                    c_leaf = cinfo["name"].split(".")[-1].lower()
                    if len(c_leaf) > 2 and c_leaf in q_lower:
                        score += 2
                if score > best_score:
                    best_score = score
                    target_col = col

        # If only 1 collection exists in the source and the question has analytical intent, use it
        if not target_col and len(collections) == 1:
            analytical_words = {
                "how", "many", "count", "total", "average", "avg", "sum", "top", "show",
                "list", "all", "find", "which", "what", "highest", "lowest", "max", "min", "compare"
            }
            if any(w in q_lower.split() for w in analytical_words):
                target_col = collections[0]

        if not target_col:
            raise ValueError("Could not map question to any collection in the active MongoDB database.")

        col_name = target_col["name"]
        col_fields = {c["name"]: c["data_type"] for c in target_col.get("columns", [])}
        top_level_fields = [f for f in col_fields.keys() if "." not in f and "[]" not in f and f != "_id"]

        # Identify numeric and categorical fields in the chosen collection
        numeric_fields = [
            f for f, t in col_fields.items() if t in ("Double", "Int64") and "." not in f
        ]
        categorical_fields = [
            f for f, t in col_fields.items() if t == "String" and "." not in f and not f.endswith("_id")
        ]

        # Match specific metric field mentioned in question
        metric_field = None
        for nf in numeric_fields:
            if nf.lower() in q_lower or nf.lower().replace("_", " ") in q_lower:
                metric_field = nf
                break
        if not metric_field:
            for alias, candidates in [
                ("revenue", ["revenue", "total", "amount", "price", "total_spent"]),
                ("sales", ["amount", "total", "revenue", "total_spent"]),
                ("spent", ["total_spent", "amount", "total"]),
                ("salary", ["salary", "compensation"]),
                ("gpa", ["gpa", "score", "rating"]),
            ]:
                if alias in q_lower:
                    metric_field = next((c for c in candidates if c in col_fields), None)
                    if metric_field:
                        break
        if not metric_field and numeric_fields:
            metric_field = numeric_fields[0]

        # Top-N detection (e.g., "Top 10 products by revenue")
        m_top = re.search(r"\btop\s+(\d+)", q_lower)
        top_n = int(m_top.group(1)) if m_top else None

        # Match grouping dimension ("by department", "by category", "by month", "by city")
        # Exclude numeric sort metrics when top_n is present (e.g., "top 10 products by revenue")
        group_field = None
        m_by = re.search(r"\b(?:by|per|across|for each)\s+([a-zA-Z_]+)", q_lower)
        if m_by:
            candidate_dim = m_by.group(1).rstrip("s")
            for f in col_fields.keys():
                if candidate_dim in f.lower():
                    if top_n is not None and f in numeric_fields:
                        metric_field = f
                    else:
                        group_field = f.replace("[].", ".")
                    break
        if not group_field and ("january" in q_lower or "february" in q_lower or "monthly" in q_lower or "month" in q_lower):
            if "month" in col_fields:
                group_field = "month"

        # Build filter conditions ($match)
        match_stage: dict[str, Any] = {}
        threshold = _parse_numeric_threshold(q_lower)
        if threshold is not None and metric_field:
            if any(w in q_lower for w in ("above", "over", "more than", "greater than", "exceeding", ">")):
                match_stage[metric_field] = {"$gt": threshold}
            elif any(w in q_lower for w in ("below", "under", "less than", "<")):
                match_stage[metric_field] = {"$lt": threshold}
            else:
                match_stage[metric_field] = {"$gte": threshold}

        # Month comparison filter (e.g., "Compare sales between January and February")
        months_mentioned = [
            m.capitalize()
            for m in ("january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december")
            if m in q_lower
        ]
        if months_mentioned and "month" in col_fields:
            match_stage["month"] = {"$in": months_mentioned}

        pipeline: list[dict[str, Any]] = []
        if match_stage:
            pipeline.append({"$match": match_stage})

        # CASE A: Count Query ("How many ...")
        if re.search(r"\b(how many|count|total number of)\b", q_lower) and not group_field:
            count_alias = f"total_{col_name.split('_')[-1]}"
            pipeline.append({"$count": count_alias})
            return {
                "collection": col_name,
                "operation": "aggregate",
                "pipeline": pipeline,
                "limit": 10,
            }

        # CASE B: Grouped Aggregation ("Average salary by department", "Compare sales between January and February", "Monthly revenue")
        if group_field or (top_n is None and any(w in q_lower for w in ("average", "avg", "total sales", "compare", "sum of"))):
            dim = group_field or (categorical_fields[0] if categorical_fields else None)
            if dim and metric_field:
                is_avg = any(w in q_lower for w in ("average", "avg", "mean"))
                agg_op = "$avg" if is_avg else "$sum"
                agg_label = f"average_{metric_field}" if is_avg else f"total_{metric_field}"
                pipeline.extend(
                    [
                        {
                            "$group": {
                                "_id": f"${dim}",
                                agg_label: {agg_op: f"${metric_field}"},
                                "document_count": {"$sum": 1},
                            }
                        },
                        {
                            "$project": {
                                "_id": 0,
                                dim.split(".")[-1]: "$_id",
                                agg_label: {"$round": [f"${agg_label}", 2]},
                                "document_count": 1,
                            }
                        },
                        {"$sort": {agg_label: -1}},
                    ]
                )
                return {
                    "collection": col_name,
                    "operation": "aggregate",
                    "pipeline": pipeline,
                    "limit": top_n or 50,
                }
            elif metric_field and any(w in q_lower for w in ("average", "avg", "sum", "total", "max", "min", "highest", "lowest")):
                is_avg = any(w in q_lower for w in ("average", "avg"))
                is_max = any(w in q_lower for w in ("max", "maximum", "highest"))
                is_min = any(w in q_lower for w in ("min", "minimum", "lowest"))
                agg_op = "$avg" if is_avg else ("$max" if is_max else ("$min" if is_min else "$sum"))
                label = f"{agg_op.lstrip('$')}_{metric_field}"
                pipeline.extend(
                    [
                        {"$group": {"_id": None, label: {agg_op: f"${metric_field}"}}},
                        {"$project": {"_id": 0, label: {"$round": [f"${label}", 2]}}},
                    ]
                )
                return {
                    "collection": col_name,
                    "operation": "aggregate",
                    "pipeline": pipeline,
                    "limit": 10,
                }

        # CASE C: Cross-Collection $lookup ("join" / "with customer details" / "orders with customer")
        if "customer" in q_lower and "order" in q_lower and col_name.endswith("orders"):
            cust_col = _find_collection(["customers"])
            if cust_col:
                pipeline.extend(
                    [
                        {
                            "$lookup": {
                                "from": cust_col["name"],
                                "localField": "customer_id",
                                "foreignField": "customer_id",
                                "as": "customer_info",
                            }
                        },
                        {"$unwind": "$customer_info"},
                        {
                            "$project": {
                                "_id": 0,
                                "order_id": 1,
                                "customer_id": 1,
                                "customer_name": "$customer_info.name",
                                "tier": "$customer_info.tier",
                                "month": 1,
                                "amount": 1,
                                "status": 1,
                            }
                        },
                        {"$sort": {"amount": -1}},
                        {"$limit": top_n or 25},
                    ]
                )
                return {
                    "collection": col_name,
                    "operation": "aggregate",
                    "pipeline": pipeline,
                    "limit": top_n or 25,
                }

        # CASE D: Top-N or Filtered Find/Aggregate ("What are the top 10 products by revenue?", "Which customers have spent more than ₹1 lakh?")
        sort_field = metric_field or (top_level_fields[0] if top_level_fields else "_id")
        sort_dir = 1 if any(w in q_lower for w in ("lowest", "least", "bottom", "cheapest")) else -1
        pipeline.append({"$sort": {sort_field: sort_dir}})
        pipeline.append({"$limit": top_n or 50})

        proj = {"_id": 0}
        for f in top_level_fields[:8]:
            proj[f] = 1
        if len(proj) > 1:
            pipeline.append({"$project": proj})

        return {
            "collection": col_name,
            "operation": "aggregate",
            "pipeline": pipeline,
            "limit": top_n or 50,
        }

    def translate(self, question: str, source_id: str | None = None) -> str:
        """
        Translates a natural language question into a formatted, human-readable
        MongoDB aggregation pipeline string (`db.<collection>.aggregate([...])`)
        that can also be validated and executed directly by MongoQueryExecutor.
        """
        structured = self.generate_structured_query(question, source_id)
        return MongoQueryValidator.format_human_readable(structured)


# Backwards-compatible alias
TextToSQLService = MongoQueryService
