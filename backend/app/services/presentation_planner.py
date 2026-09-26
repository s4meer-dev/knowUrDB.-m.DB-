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
    def build_platform_dataset_count(
        count: int, datasets: list[dict[str, Any]]
    ) -> dict[str, Any]:
        if count > 0:
            names = ", ".join(d.get("display_name") or d.get("database_name") or "Dataset" for d in datasets)
            summary = f"You currently have {count} registered datasets in KnowUrDB: {names}."
        else:
            summary = "There are currently 0 datasets registered in KnowUrDB. Click 'Generate Random MongoDB Demo Dataset' or upload a file to get started."

        rows = [
            {
                "dataset": d.get("display_name") or d.get("database_name") or "Dataset",
                "domain": d.get("domain") or "General",
                "collections": len(d.get("collections", [])) if d.get("collections") else (d.get("collection_count") or 0),
                "documents": d.get("document_count") or 0,
            }
            for d in datasets
        ]

        follow_ups = ["List all datasets"]
        if datasets:
            first_name = datasets[0].get("display_name") or "this dataset"
            follow_ups.extend([
                f"Tell me about {first_name}",
                f"How many collections in {first_name}?",
            ])

        return {
            "intent": "META_COUNT_DATASETS",
            "presentation": {
                "type": "kpi",
                "title": "TOTAL DATASETS",
                "subtitle": "KnowUrDB Platform Registry",
                "summary": summary,
                "primary_value": str(count),
                "primary_unit": "datasets",
                "datasets_summary": rows,
                "show_technical_by_default": False,
            },
            "answer": {
                "headline": "TOTAL DATASETS",
                "value": str(count),
                "unit": "datasets",
                "summary": summary,
            },
            "columns": ["dataset", "domain", "collections", "documents"],
            "rows": rows,
            "insights": [
                f"{r['dataset']} ({r['domain']}): {r['collections']} collections, {r['documents']:,} documents"
                for r in rows
            ],
            "follow_ups": follow_ups,
        }

    @staticmethod
    def build_scope_dataset_explanation(source_meta: Any) -> dict[str, Any]:
        name = getattr(source_meta, "display_name", None) or getattr(source_meta, "name", None) or "Selected Dataset"
        cols = getattr(source_meta, "collections", []) or []
        doc_count = getattr(source_meta, "record_count", 0) or 0
        col_list_str = ", ".join(cols) if cols else "none"
        summary = (
            f"You currently have 1 dataset selected: '{name}'. "
            f"Within this dataset, there are {len(cols)} collections ({col_list_str}) with {doc_count:,} total records. "
            f"To view the total count of all registered datasets across KnowUrDB, switch your scope to 'All Sources'."
        )
        rows = [{"collection": c} for c in cols]
        return {
            "intent": "META_DATASET_SCOPE_CONTEXT",
            "presentation": {
                "type": "kpi",
                "title": "DATASET SCOPED VIEW",
                "subtitle": f"Active Dataset: {name}",
                "summary": summary,
                "primary_value": "1",
                "primary_unit": "selected dataset",
                "show_technical_by_default": False,
            },
            "answer": {
                "headline": "DATASET SCOPE",
                "value": "1",
                "unit": f"selected dataset ({name})",
                "summary": summary,
            },
            "columns": ["collection"],
            "rows": rows,
            "insights": [
                f"Active Dataset: {name}",
                f"Contains {len(cols)} collections: {col_list_str}",
            ],
            "follow_ups": [
                f"How many collections in {name}?",
                f"Show me {cols[0]}" if cols else "Show data",
                "Show all datasets in KnowUrDB",
            ],
        }

    @staticmethod
    def build_scope_collection_explanation(collection_name: str) -> dict[str, Any]:
        summary = (
            f"You're currently viewing the '{collection_name}' collection. "
            f"A dataset-level count isn't available within a single collection. "
            f"If you want the total number of datasets across KnowUrDB, switch your scope to 'All Sources'."
        )
        return {
            "intent": "META_COLLECTION_SCOPE_CONTEXT",
            "presentation": {
                "type": "kpi",
                "title": "COLLECTION SCOPED VIEW",
                "subtitle": f"Active Collection: {collection_name}",
                "summary": summary,
                "primary_value": collection_name,
                "primary_unit": "active collection",
                "show_technical_by_default": False,
            },
            "answer": {
                "headline": "COLLECTION SCOPE",
                "value": collection_name,
                "unit": "active collection",
                "summary": summary,
            },
            "columns": ["collection"],
            "rows": [{"collection": collection_name}],
            "insights": [
                f"Current focus is scoped to collection '{collection_name}'.",
                "Switch to 'All Sources' to query platform-wide dataset counts.",
            ],
            "follow_ups": [
                f"How many records in {collection_name}?",
                f"Show me {collection_name}",
                "Show all datasets in KnowUrDB",
            ],
        }

    @staticmethod
    def build_metric_unavailable_presentation(
        requested_metric: str,
        collection_name: str,
        explanation: str,
    ) -> dict[str, Any]:
        title = f"{requested_metric.upper()} NOT AVAILABLE"
        return {
            "intent": "METRIC_UNAVAILABLE",
            "presentation": {
                "type": "warning",
                "title": title,
                "subtitle": f"Collection: {collection_name}",
                "summary": explanation,
                "primary_value": "N/A",
                "primary_unit": f"not in {collection_name}",
                "show_technical_by_default": False,
            },
            "answer": {
                "headline": title,
                "value": "N/A",
                "unit": f"not in {collection_name}",
                "summary": explanation,
            },
            "columns": [],
            "rows": [],
            "insights": [explanation],
            "follow_ups": [
                f"Show fields in {collection_name}",
                f"Show me {collection_name}",
            ],
        }

    @staticmethod
    def build_metric_alternative_presentation(
        requested_metric: str,
        collection_name: str,
        explanation: str,
        alternatives: list[dict[str, Any]],
    ) -> dict[str, Any]:
        candidates = [
            {
                "name": alt.get("name"),
                "label": alt.get("label") or alt.get("name"),
                "description": alt.get("description") or f"Calculate {alt.get('name')}",
                "clarification_type": "field",
            }
            for alt in alternatives
        ]
        return {
            "intent": "METRIC_ALTERNATIVE",
            "presentation": {
                "type": "clarification",
                "clarification_type": "field",
                "title": "METRIC CLARIFICATION",
                "subtitle": f"Collection: {collection_name}",
                "summary": explanation,
                "candidate_collections": candidates,
            },
            "answer": {
                "headline": "METRIC CLARIFICATION",
                "value": "Clarification needed",
                "unit": "",
                "summary": explanation,
            },
            "columns": [],
            "rows": [],
            "candidates": candidates,
            "insights": [explanation],
            "follow_ups": [alt.get("label") for alt in alternatives if alt.get("label")],
        }

    @staticmethod
    def build_dataset_list(datasets: list[dict[str, Any]]) -> dict[str, Any]:
        count = len(datasets)
        summary = f"Found {count} registered datasets in KnowUrDB."
        rows = [
            {
                "dataset": d.get("display_name") or d.get("database_name") or "Dataset",
                "domain": (d.get("domain") or "General").capitalize(),
                "collections": ", ".join(d.get("collections", [])) if d.get("collections") else str(d.get("collection_count") or 0),
                "collection_count": len(d.get("collections", [])) if d.get("collections") else (d.get("collection_count") or 0),
                "documents": d.get("document_count") or 0,
                "source_id": d.get("source_id") or d.get("dataset_id"),
            }
            for d in datasets
        ]

        follow_ups = [
            f"Tell me about {d.get('display_name')}"
            for d in datasets[:3]
            if d.get("display_name")
        ]

        return {
            "intent": "META_LIST_DATASETS",
            "presentation": {
                "type": "dataset_list",
                "title": "Registered Datasets",
                "subtitle": f"{count} datasets registered",
                "summary": summary,
                "primary_value": str(count),
                "primary_unit": "datasets",
                "datasets_summary": rows,
                "show_technical_by_default": False,
            },
            "answer": {
                "headline": "REGISTERED DATASETS",
                "value": str(count),
                "unit": "datasets",
                "summary": summary,
            },
            "columns": ["dataset", "domain", "collections", "documents"],
            "rows": rows,
            "insights": [
                f"{r['dataset']}: {r['collection_count']} collections ({r['collections']}), {r['documents']:,} documents"
                for r in rows
            ],
            "follow_ups": follow_ups or ["How many datasets are there?"],
        }

    @staticmethod
    def build_active_dataset_presentation(dataset: dict[str, Any] | None) -> dict[str, Any]:
        if not dataset:
            summary = "No dataset is currently active. You are viewing 'All Sources' or no sources are connected."
            return {
                "intent": "META_ACTIVE_DATASET",
                "presentation": {
                    "type": "kpi",
                    "title": "Active Dataset",
                    "subtitle": "Scope: All Sources",
                    "summary": summary,
                    "primary_value": "All Sources",
                    "primary_unit": "active scope",
                    "show_technical_by_default": False,
                },
                "answer": {
                    "headline": "ACTIVE SCOPE",
                    "value": "All Sources",
                    "unit": "",
                    "summary": summary,
                },
                "columns": [],
                "rows": [],
                "insights": [],
                "follow_ups": ["List all datasets", "How many datasets are there?"],
            }

        name = dataset.get("display_name") or dataset.get("database_name") or "Dataset"
        cols = dataset.get("collections", [])
        total_docs = dataset.get("document_count", 0)
        summary = f"The active dataset is '{name}' ({dataset.get('domain', 'general')}), with {len(cols)} collections ({', '.join(cols)}) and {total_docs:,} documents."
        return {
            "intent": "META_ACTIVE_DATASET",
            "presentation": {
                "type": "kpi",
                "title": "Active Dataset",
                "subtitle": name,
                "summary": summary,
                "primary_value": name,
                "primary_unit": f"{len(cols)} collections",
                "show_technical_by_default": False,
            },
            "answer": {
                "headline": "ACTIVE DATASET",
                "value": name,
                "unit": f"({len(cols)} collections)",
                "summary": summary,
            },
            "columns": ["collection"],
            "rows": [{"collection": c} for c in cols],
            "insights": [
                f"Contains {len(cols)} collections: {', '.join(cols)}",
                f"Total document count: {total_docs:,}",
            ],
            "follow_ups": [
                f"Show me {cols[0]}" if cols else "Show data",
                f"How many {cols[0]} are there?" if cols else "Count records",
                "List all datasets",
            ],
        }

    @staticmethod
    def build_dataset_clarification(
        candidate_datasets: list[dict[str, Any]], original_question: str
    ) -> dict[str, Any]:
        candidates = [
            {
                "source_id": d.get("source_id") or d.get("dataset_id"),
                "name": d.get("display_name") or d.get("name"),
                "collection": d.get("display_name") or d.get("name"),
                "document_count": d.get("document_count", 0),
                "field_count": len(d.get("collections", [])),
                "fields_preview": d.get("collections", [])[:5],
                "description": d.get("description") or f"Domain: {d.get('domain', 'General')}",
                "clarification_type": "dataset",
            }
            for d in candidate_datasets
        ]
        msg = f"Multiple datasets could match '{original_question}'. Which dataset would you like to query?"
        return {
            "intent": "CLARIFICATION",
            "presentation": {
                "type": "clarification",
                "clarification_type": "dataset",
                "title": "NEED A LITTLE MORE CONTEXT",
                "summary": msg,
                "candidate_collections": candidates,
            },
            "answer": {
                "headline": "SELECT DATASET",
                "value": str(len(candidates)),
                "unit": "candidates",
                "summary": msg,
            },
            "candidates": candidates,
            "error": msg,
        }

    @staticmethod
    def build_field_clarification(
        collection: str, candidate_fields: list[str], original_question: str, source_id: str | None = None
    ) -> dict[str, Any]:
        candidates = [
            {
                "source_id": source_id or "",
                "name": f,
                "collection": collection,
                "document_count": None,
                "field_count": None,
                "fields_preview": [f],
                "description": f"Calculate on field '{f}'",
                "clarification_type": "field",
            }
            for f in candidate_fields
        ]
        msg = f"In `{collection}`, multiple numeric fields could match '{original_question}'. Which field would you like to calculate?"
        return {
            "intent": "CLARIFICATION",
            "presentation": {
                "type": "clarification",
                "clarification_type": "field",
                "title": "SELECT FIELD",
                "summary": msg,
                "candidate_collections": candidates,
            },
            "answer": {
                "headline": "SELECT FIELD",
                "value": str(len(candidates)),
                "unit": "candidate fields",
                "summary": msg,
            },
            "candidates": candidates,
            "error": msg,
        }

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

        # 0A. MULTI_COLLECTION ($lookup across collections, e.g. customers + orders)
        if plan.intent == "MULTI_COLLECTION":
            sec_col = plan.secondary_collection or "customers"
            ranked_rows = [{"rank": idx, **r} for idx, r in enumerate(rows, start=1)]
            ranked_cols = ["rank"] + [c for c in columns if c != "rank"]
            top_row = rows[0] if rows else {}
            leader = top_row.get("customer_name") or top_row.get("customer_id") or "#1"
            orders_cnt = top_row.get("orders_placed", 0)
            summary = (
                f"Joined `{sec_col}` and `{col_display}` on `customer_id`: "
                f"{leader} placed the most orders ({orders_cnt} orders)."
            )
            return {
                "columns": ranked_cols,
                "rows": ranked_rows,
                "presentation": {
                    "type": "ranked_table",
                    "title": f"{sec_col.title()} + {col_display.title()} Analysis",
                    "subtitle": f"Data Sources: {sec_col} ↔ {col_display} (customer_id)",
                    "summary": summary,
                    "primary_value": str(leader),
                    "primary_unit": f"{orders_cnt} orders placed",
                    "chart_type": "bar",
                    "candidate_collections": plan.candidate_collections,
                    "multi_collection_sources": [sec_col, col_display],
                    "show_technical_by_default": False,
                },
                "answer": {
                    "headline": f"{sec_col.upper()} + {col_display.upper()}",
                    "value": str(leader),
                    "unit": f"({orders_cnt} orders)",
                    "summary": summary,
                },
                "insights": [],
                "follow_ups": [],
            }

        # 1. COUNT Intent -> KPI Card
        if plan.intent == "COUNT":
            count_val = 0
            if rows and columns:
                raw_v = rows[0].get(columns[0], 0)
                count_val = int(raw_v) if isinstance(raw_v, (int, float)) else 0
            filter_suffix = f" matching ({', '.join(plan.filter_descriptions)})" if plan.filter_descriptions else ""
            summary = f"The `{col_display}` collection contains {count_val:,} documents{filter_suffix}."
            return {
                "presentation": {
                    "type": "kpi",
                    "title": f"Total {col_display.title()}",
                    "subtitle": f"Collection: {col_display}",
                    "summary": summary,
                    "primary_value": f"{count_val:,}",
                    "primary_unit": "documents",
                    "candidate_collections": plan.candidate_collections,
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
                    "candidate_collections": plan.candidate_collections,
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
                    "candidate_collections": plan.candidate_collections,
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
                    "candidate_collections": plan.candidate_collections,
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
            if getattr(plan, "requested_concept", None) == "REVENUE" or "revenue" in plan.original_question.lower():
                title = f"{op_word} Revenue"
                summary = f"{op_word} revenue is {val_fmt}, calculated from {plan.collection}.{metric} across {doc_cnt:,} records."
            elif getattr(plan, "requested_concept", None) == "SPENDING" or "spend" in plan.original_question.lower():
                title = f"{op_word} Spending"
                summary = f"{op_word} spending is {val_fmt}, calculated from {plan.collection}.{metric} across {doc_cnt:,} records."
            else:
                title = f"{op_word} {singular_col.title()} {metric.replace('_', ' ').title()}"
                summary = f"The {op_word.lower()} {metric.replace('_', ' ')} across {doc_cnt:,} {col_display} is {val_fmt}."
            return {
                "presentation": {
                    "type": "kpi",
                    "title": title,
                    "subtitle": f"{doc_cnt} {col_display} included",
                    "summary": summary,
                    "primary_value": val_fmt,
                    "primary_unit": f"across {doc_cnt} {col_display}",
                    "candidate_collections": plan.candidate_collections,
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
                    "candidate_collections": plan.candidate_collections,
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
