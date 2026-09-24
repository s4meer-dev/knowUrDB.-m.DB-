from typing import Any

from app.services.intent_classifier import QueryPlan

CURRENCY_FIELDS = {
    "price",
    "salary",
    "total_spent",
    "total_amount",
    "amount",
    "revenue",
    "line_total",
    "average_price",
    "total_price",
    "average_salary",
    "total_salary",
    "average_total_amount",
    "total_total_amount",
    "average_amount",
    "total_amount",
}


def format_indian_number(val: int | float, is_currency: bool = False) -> str:
    """Formats numbers cleanly (e.g., 145000 -> ₹1,45,000 or 145,000) without unnecessary .00."""
    if isinstance(val, float):
        if val.is_integer():
            val = int(val)
        else:
            rounded = round(val, 2)
            if rounded.is_integer():
                val = int(rounded)
            else:
                prefix = "₹" if is_currency else ""
                return f"{prefix}{rounded:,.2f}"

    if isinstance(val, int) and is_currency:
        s = str(abs(val))
        sign = "-" if val < 0 else ""
        if len(s) > 3:
            last3 = s[-3:]
            rest = s[:-3]
            groups = []
            while len(rest) > 2:
                groups.insert(0, rest[-2:])
                rest = rest[:-2]
            if rest:
                groups.insert(0, rest)
            return f"{sign}₹{','.join(groups)},{last3}"
        return f"{sign}₹{s}"

    return f"{val:,}"


class PresentationPlanner:
    """
    Deterministic Presentation Planner.
    Guarantees that the UI presentation mode, primary answer, summary, and follow-ups
    strictly match what the user asked—never inventing a 'Top Result by Price' when
    the user asked for a list or filter.
    """

    @staticmethod
    def build_dataset_overview(
        source_name: str, collections: list[dict[str, Any]]
    ) -> dict[str, Any]:
        total_docs = sum(int(c.get("document_count", 0)) for c in collections)
        col_rows = []
        for c in collections:
            cols = c.get("columns", [])
            top_fields = [col["name"] for col in cols if col["name"] != "_id"][:6]
            col_rows.append(
                {
                    "collection": c["name"],
                    "documents": int(c.get("document_count", 0)),
                    "fields": len(cols),
                    "key_fields": ", ".join(top_fields),
                }
            )
        summary = f"Your active dataset ({source_name}) contains {len(collections)} collections and {total_docs:,} total documents."
        return {
            "intent": "DATASET_OVERVIEW",
            "presentation": {
                "type": "dataset_overview",
                "title": "Dataset Overview",
                "subtitle": source_name,
                "summary": summary,
                "primary_value": f"{len(collections)} Collections • {total_docs:,} Documents",
                "primary_unit": "active dataset",
                "collections_summary": col_rows,
                "show_technical_by_default": False,
            },
            "answer": {
                "headline": "DATASET OVERVIEW",
                "value": str(len(collections)),
                "unit": f"collections ({total_docs:,} documents)",
                "summary": summary,
            },
            "columns": ["collection", "documents", "fields", "key_fields"],
            "rows": col_rows,
            "insights": [
                f"{c['collection']} — {c['documents']:,} documents ({c['fields']} fields)"
                for c in col_rows
            ],
            "follow_ups": [
                f"Show me {col_rows[0]['collection']}" if col_rows else "Show collections",
                f"How many {col_rows[0]['collection']} are there?" if col_rows else "Count documents",
                f"What fields are in {col_rows[0]['collection']}?" if col_rows else "Show schema",
            ],
        }

    @staticmethod
    def build_schema_presentation(
        source_name: str,
        collections: list[dict[str, Any]],
        target_collection: str | None = None,
    ) -> dict[str, Any]:
        target_cols = (
            [c for c in collections if c["name"] == target_collection]
            if target_collection
            else collections
        )
        if not target_cols:
            target_cols = collections

        rows = []
        for col in target_cols:
            for f in col.get("columns", []):
                samples = ", ".join(str(v) for v in (f.get("sample_values") or [])[:3])
                rows.append(
                    {
                        "collection": col["name"],
                        "field": f["name"],
                        "type": f.get("data_type") or f.get("type") or "String",
                        "sample_values": samples or "—",
                    }
                )

        col_label = target_collection or source_name
        summary = f"Found {len(rows)} schema fields in {col_label}."
        return {
            "intent": "SCHEMA_QUERY",
            "presentation": {
                "type": "schema",
                "title": f"{col_label.title()} Schema",
                "subtitle": f"{len(rows)} BSON fields discovered",
                "summary": summary,
                "primary_value": str(len(rows)),
                "primary_unit": "fields",
                "schema_fields": rows,
                "show_technical_by_default": False,
            },
            "answer": {
                "headline": f"SCHEMA • {col_label.upper()}",
                "value": str(len(rows)),
                "unit": "fields",
                "summary": summary,
            },
            "columns": ["collection", "field", "type", "sample_values"],
            "rows": rows,
            "insights": [
                f"Collection `{c['name']}` contains {len(c.get('columns', []))} fields and {c.get('document_count', 0)} documents."
                for c in target_cols
            ],
            "follow_ups": [
                f"Show me {target_cols[0]['name']}" if target_cols else "Show data",
                f"How many {target_cols[0]['name']} are there?" if target_cols else "Count records",
            ],
        }

    @staticmethod
    def plan_presentation(
        plan: QueryPlan,
        rows: list[dict[str, Any]],
        columns: list[str],
        collections: list[dict[str, Any]],
    ) -> dict[str, Any]:
        col_display = (plan.collection or "records").split("_")[-1]
        singular_col = col_display[:-1] if col_display.endswith("s") else col_display
        row_count = len(rows)

        # 0. Empty Result Set
        if row_count == 0 and plan.intent != "COUNT":
            summary = f"I couldn't find any {col_display} matching that condition."
            return {
                "presentation": {
                    "type": "empty",
                    "title": f"No Matching {col_display.title()}",
                    "subtitle": ", ".join(plan.filter_descriptions) if plan.filter_descriptions else col_display,
                    "summary": summary,
                    "primary_value": "0",
                    "primary_unit": col_display,
                    "show_technical_by_default": False,
                },
                "answer": {
                    "headline": f"NO MATCHING {col_display.upper()}",
                    "value": "0",
                    "unit": col_display,
                    "summary": summary,
                },
                "insights": [],
                "follow_ups": [
                    f"Show all {col_display}",
                    f"How many {col_display} are there?",
                ],
            }

        # 1. COUNT Intent -> KPI Card
        if plan.intent == "COUNT":
            count_val = 0
            if rows and columns:
                raw_v = rows[0].get(columns[0], 0)
                count_val = int(raw_v) if isinstance(raw_v, (int, float)) else 0
            filter_suffix = f" matching ({', '.join(plan.filter_descriptions)})" if plan.filter_descriptions else ""
            summary = f"Your active `{col_display}` collection contains {count_val:,} documents{filter_suffix}."
            return {
                "presentation": {
                    "type": "kpi",
                    "title": f"Total {col_display.title()}",
                    "subtitle": f"Collection: {col_display}",
                    "summary": summary,
                    "primary_value": f"{count_val:,}",
                    "primary_unit": "documents",
                    "show_technical_by_default": False,
                },
                "answer": {
                    "headline": f"TOTAL {col_display.upper()}",
                    "value": f"{count_val:,}",
                    "unit": "documents",
                    "summary": summary,
                },
                "insights": [],
                "follow_ups": PresentationPlanner._generate_follow_ups(plan, collections),
            }

        # 2. LIST_RECORDS / SEARCH / FILTER / SORT -> Clean Table (NEVER 'Top Result by Price'!)
        if plan.intent in ("LIST_RECORDS", "SEARCH", "FILTER", "SORT", "DISTINCT_VALUES"):
            if plan.intent == "FILTER" and plan.filter_descriptions:
                title = f"Filtered {col_display.title()}"
                summary = f"Showing {row_count:,} matching {col_display} ({', '.join(plan.filter_descriptions)})."
            elif plan.intent == "SORT" and plan.metric_field:
                title = f"{col_display.title()} Sorted by {plan.metric_field.replace('_', ' ').title()}"
                summary = f"Here are {row_count:,} {col_display} sorted by {plan.metric_field.replace('_', ' ')}."
            else:
                title = col_display.title()
                summary = f"Here are the {row_count:,} {col_display} in the active collection."

            return {
                "presentation": {
                    "type": "table",
                    "title": title,
                    "subtitle": f"{row_count:,} matching documents",
                    "summary": summary,
                    "primary_value": f"{row_count:,}",
                    "primary_unit": f"matching {col_display}",
                    "show_technical_by_default": False,
                },
                "answer": {
                    "headline": title.upper(),
                    "value": f"{row_count:,}",
                    "unit": f"matching {col_display}",
                    "summary": summary,
                },
                "insights": [],
                "follow_ups": PresentationPlanner._generate_follow_ups(plan, collections),
            }

        # 3. MAXIMUM / MINIMUM -> Single-Value Result + Relevant Record Card
        if plan.intent in ("MAXIMUM", "MINIMUM"):
            top_row = rows[0]
            metric = plan.metric_field or (columns[-1] if columns else "value")
            is_curr = metric.lower() in CURRENCY_FIELDS
            raw_metric_val = top_row.get(metric, 0)
            val_formatted = (
                format_indian_number(raw_metric_val, is_currency=is_curr)
                if isinstance(raw_metric_val, (int, float))
                else str(raw_metric_val)
            )
            name_val = top_row.get("name") or top_row.get(columns[0]) or singular_col
            id_val = next((str(top_row[k]) for k in columns if k.endswith("_id") and top_row.get(k)), "")
            entity_label = f"{name_val} ({id_val})" if id_val and id_val != str(name_val) else str(name_val)
            superlative_label = (
                f"Most Expensive {singular_col.title()}"
                if metric == "price" and plan.intent == "MAXIMUM"
                else (
                    f"Cheapest {singular_col.title()}"
                    if metric == "price" and plan.intent == "MINIMUM"
                    else f"{'Highest' if plan.intent == 'MAXIMUM' else 'Lowest'} {metric.replace('_', ' ').title()} {singular_col.title()}"
                )
            )
            summary = f"The {superlative_label.lower()} is {entity_label} with {metric.replace('_', ' ')} of {val_formatted}."
            return {
                "presentation": {
                    "type": "detail",
                    "title": superlative_label,
                    "subtitle": entity_label,
                    "summary": summary,
                    "primary_value": val_formatted,
                    "primary_unit": entity_label,
                    "highlight_record": top_row,
                    "show_technical_by_default": False,
                },
                "answer": {
                    "headline": superlative_label.upper(),
                    "value": val_formatted,
                    "unit": entity_label,
                    "summary": summary,
                },
                "insights": [],
                "follow_ups": PresentationPlanner._generate_follow_ups(plan, collections),
            }

        # 4. TOP_N / BOTTOM_N -> Ranked Table + Optional Bar Chart
        if plan.intent in ("TOP_N", "BOTTOM_N"):
            metric = plan.metric_field or "value"
            rank_prefix = "Bottom" if plan.intent == "BOTTOM_N" else "Top"
            title = f"{rank_prefix} {row_count} {col_display.title()} by {metric.replace('_', ' ').title()}"
            # Add explicit Rank column (#1, #2, ...) if not already present
            ranked_rows = []
            for idx, r in enumerate(rows, start=1):
                ranked_rows.append({"rank": idx, **r})
            ranked_cols = ["rank"] + [c for c in columns if c != "rank"]

            top_row = rows[0]
            top_name = top_row.get("name") or top_row.get(columns[0]) or "#1"
            raw_v = top_row.get(metric, 0)
            val_fmt = (
                format_indian_number(raw_v, is_currency=metric.lower() in CURRENCY_FIELDS)
                if isinstance(raw_v, (int, float))
                else str(raw_v)
            )
            summary = f"Here are the {title.lower()}, led by {top_name} ({val_fmt})."
            return {
                "columns": ranked_cols,
                "rows": ranked_rows,
                "presentation": {
                    "type": "ranked_table",
                    "title": title,
                    "subtitle": f"Ranked by {metric.replace('_', ' ')}",
                    "summary": summary,
                    "primary_value": f"{top_name}",
                    "primary_unit": f"#1 • {val_fmt}",
                    "chart_type": "bar",
                    "show_technical_by_default": False,
                },
                "answer": {
                    "headline": title.upper(),
                    "value": str(top_name),
                    "unit": f"({val_fmt})",
                    "summary": summary,
                },
                "insights": [],
                "follow_ups": PresentationPlanner._generate_follow_ups(plan, collections),
            }

        # 5. AVERAGE / SUM (Single KPI vs Grouped Chart)
        if plan.intent in ("AVERAGE", "SUM") and not plan.group_field:
            metric = plan.metric_field or (columns[0] if columns else "value")
            expected_col = f"{'average' if plan.intent == 'AVERAGE' else 'total'}_{metric}"
            val_col = (
                expected_col
                if expected_col in rows[0]
                else next((c for c in columns if c != "document_count"), columns[0])
            )
            raw_v = rows[0].get(val_col, 0)
            doc_cnt = rows[0].get("document_count", row_count)
            is_curr = metric.lower() in CURRENCY_FIELDS or val_col.lower() in CURRENCY_FIELDS
            val_fmt = (
                format_indian_number(raw_v, is_currency=is_curr)
                if isinstance(raw_v, (int, float))
                else str(raw_v)
            )
            op_word = "Average" if plan.intent == "AVERAGE" else "Total"
            title = f"{op_word} {singular_col.title()} {metric.replace('_', ' ').title()}"
            summary = f"The {op_word.lower()} {metric.replace('_', ' ')} across {doc_cnt} {col_display} is {val_fmt}."
            return {
                "presentation": {
                    "type": "kpi",
                    "title": title,
                    "subtitle": f"{doc_cnt} {col_display} included",
                    "summary": summary,
                    "primary_value": val_fmt,
                    "primary_unit": f"across {doc_cnt} {col_display}",
                    "show_technical_by_default": False,
                },
                "answer": {
                    "headline": title.upper(),
                    "value": val_fmt,
                    "unit": f"({doc_cnt} {col_display})",
                    "summary": summary,
                },
                "insights": [],
                "follow_ups": PresentationPlanner._generate_follow_ups(plan, collections),
            }

        # 6. COMPARISON -> Comparison Table + Chart
        if plan.intent == "COMPARISON":
            m1 = plan.metric_field or ""
            m2 = plan.secondary_metric_field or ""
            if plan.group_field:
                title = f"{col_display.title()} Comparison by {plan.group_field.split('.')[-1].title()}"
            elif m1 and m2:
                title = f"{col_display.title()} Comparison: {m1.replace('_', ' ').title()} vs {m2.replace('_', ' ').title()}"
            else:
                title = f"{col_display.title()} Comparison"
            summary = f"Comparing {row_count} {col_display} across {', '.join(c.replace('_', ' ') for c in columns[:4])}."
            return {
                "presentation": {
                    "type": "comparison",
                    "title": title,
                    "subtitle": f"{row_count} items compared",
                    "summary": summary,
                    "primary_value": f"{row_count} compared",
                    "primary_unit": col_display,
                    "chart_type": "comparison_bar",
                    "show_technical_by_default": False,
                },
                "answer": {
                    "headline": title.upper(),
                    "value": f"{row_count}",
                    "unit": f"{col_display} compared",
                    "summary": summary,
                },
                "insights": [],
                "follow_ups": PresentationPlanner._generate_follow_ups(plan, collections),
            }

        # 7. GROUP_BY / TREND / DISTRIBUTION -> Chart + Table
        dim_label = (plan.group_field or columns[0]).split(".")[-1].replace("_", " ").title()
        metric_label = (plan.metric_field or "count").replace("_", " ").title()
        title = f"{col_display.title()} — {metric_label} by {dim_label}"
        summary = f"Breakdown of {col_display} {metric_label.lower()} across {row_count} {dim_label.lower()} groups."
        return {
            "presentation": {
                "type": "chart",
                "title": title,
                "subtitle": f"{row_count} groups",
                "summary": summary,
                "primary_value": f"{row_count} groups",
                "primary_unit": f"by {dim_label.lower()}",
                "chart_type": "line" if plan.intent == "TREND" else "bar",
                "show_technical_by_default": False,
            },
            "answer": {
                "headline": title.upper(),
                "value": f"{row_count}",
                "unit": "groups",
                "summary": summary,
            },
            "insights": [],
            "follow_ups": PresentationPlanner._generate_follow_ups(plan, collections),
        }

    @staticmethod
    def _generate_follow_ups(plan: QueryPlan, collections: list[dict[str, Any]]) -> list[str]:
        """Generates 3 schema-grounded, context-relevant follow-up questions for the active collection."""
        col_name = (plan.collection or "products").split("_")[-1]
        suggestions: list[str] = []

        if col_name == "products":
            candidates = [
                "What is the most expensive product?",
                "What is the average product price?",
                "Show products above 50000",
                "Give me the top 5 products by price",
                "Compare products by price and units sold",
                "How many products are there?",
            ]
        elif col_name == "customers":
            candidates = [
                "Show customers from Bangalore",
                "Which customers have spent more than ₹1 lakh?",
                "How many customers are there?",
                "Show me customers",
            ]
        elif col_name == "orders":
            candidates = [
                "How many orders are there?",
                "Compare sales between January and February",
                "Show orders by month",
            ]
        elif col_name == "employees":
            candidates = [
                "Average salary by department",
                "How many employees are there?",
                "Show me employees",
            ]
        elif col_name == "students":
            candidates = [
                "How many students have GPA above 3.5?",
                "How many students are there?",
                "Show me students",
            ]
        else:
            candidates = [
                f"How many {col_name} are there?",
                f"Show me {col_name}",
                f"What fields are in {col_name}?",
            ]

        q_low = plan.original_question.strip().lower()
        for c in candidates:
            if c.lower() != q_low and len(suggestions) < 3:
                suggestions.append(c)
        return suggestions
