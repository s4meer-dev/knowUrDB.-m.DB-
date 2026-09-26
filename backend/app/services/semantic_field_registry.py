import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SemanticConcept(str, Enum):
    REVENUE = "REVENUE"
    CUSTOMER_SPENDING = "CUSTOMER_SPENDING"
    PRICE = "PRICE"
    ACADEMIC = "ACADEMIC"
    COMPENSATION = "COMPENSATION"
    QUANTITY = "QUANTITY"
    TRANSACTION_VALUE = "TRANSACTION_VALUE"
    DATE = "DATE"
    CATEGORICAL = "CATEGORICAL"
    IDENTIFIER = "IDENTIFIER"
    GENERAL_NUMERIC = "GENERAL_NUMERIC"
    UNKNOWN = "UNKNOWN"


@dataclass
class SemanticFieldProfile:
    name: str
    concept: SemanticConcept
    data_type: str
    description: str
    is_monetary: bool = False
    is_aggregate_revenue: bool = False
    sample_values: list[Any] = field(default_factory=list)


@dataclass
class MetricMatchResult:
    status: str  # "EXACT_MATCH", "RELATED_ALTERNATIVE", "INCOMPATIBLE", "NOT_FOUND"
    field_name: str | None = None
    concept: SemanticConcept = SemanticConcept.UNKNOWN
    explanation: str = ""
    alternative_fields: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0


class SemanticFieldRegistry:
    """
    Industrial-Grade Semantic Field Classifier & Profiler for KnowUrDB.
    Enforces strict distinction between:
      - REVENUE (order totals, sales revenue, transaction amounts)
      - CUSTOMER_SPENDING (total_spent by a customer)
      - UNIT PRICE (item price, not total revenue)
      - ACADEMIC (GPA, grades)
      - COMPENSATION (salary, wages)
      - QUANTITY (stock, count)
    Prevents silent metric substitutions (e.g. GPA for revenue).
    """

    REVENUE_FIELDS = {
        "revenue",
        "total_revenue",
        "sales",
        "sales_amount",
        "sales_value",
        "gross_revenue",
        "net_revenue",
        "total_sales",
        "order_total",
        "purchase_total",
        "invoice_amount",
    }

    TRANSACTION_COLLECTIONS = {
        "orders",
        "pos_transactions",
        "transactions",
        "sales",
        "invoices",
        "payments",
        "purchases",
        "bookings",
        "reservations",
    }

    @classmethod
    def classify_field(
        cls,
        field_name: str,
        collection_name: str = "",
        data_type: str = "String",
        sample_values: list[Any] | None = None,
    ) -> SemanticFieldProfile:
        f_lower = field_name.lower().strip()
        c_lower = collection_name.lower().strip()
        samples = sample_values or []

        # 1. Identifier
        if f_lower == "_id" or f_lower.endswith("_id") or f_lower.endswith("id"):
            return SemanticFieldProfile(
                name=field_name,
                concept=SemanticConcept.IDENTIFIER,
                data_type=data_type,
                description=f"Unique identifier for {collection_name or 'record'}",
                sample_values=samples,
            )

        # 2. Date
        if any(d in f_lower for d in ("date", "time", "created_at", "uploaded_at", "timestamp")):
            return SemanticFieldProfile(
                name=field_name,
                concept=SemanticConcept.DATE,
                data_type=data_type,
                description=f"Temporal / date attribute ({field_name})",
                sample_values=samples,
            )

        # 3. Academic
        if any(a in f_lower for a in ("gpa", "grade", "score", "attendance", "marks", "exam")):
            return SemanticFieldProfile(
                name=field_name,
                concept=SemanticConcept.ACADEMIC,
                data_type=data_type,
                description=f"Academic / educational performance metric ({field_name})",
                sample_values=samples,
            )

        # 4. Compensation / Salary
        if any(s in f_lower for s in ("salary", "wage", "bonus", "compensation", "stipend")):
            return SemanticFieldProfile(
                name=field_name,
                concept=SemanticConcept.COMPENSATION,
                data_type=data_type,
                description=f"Employee compensation / salary metric ({field_name})",
                is_monetary=True,
                sample_values=samples,
            )

        # 5. Customer Spending (Specific to customer entity)
        if (
            f_lower in ("total_spent", "amount_spent", "customer_spent", "lifetime_value", "ltv")
            or ("spent" in f_lower and "customer" in c_lower)
        ):
            return SemanticFieldProfile(
                name=field_name,
                concept=SemanticConcept.CUSTOMER_SPENDING,
                data_type=data_type,
                description="Cumulative customer expenditure (customer-level spending)",
                is_monetary=True,
                is_aggregate_revenue=False,
                sample_values=samples,
            )

        # 6. Explicit Revenue / Total Amount
        if f_lower in cls.REVENUE_FIELDS:
            return SemanticFieldProfile(
                name=field_name,
                concept=SemanticConcept.REVENUE,
                data_type=data_type,
                description=f"Direct aggregate revenue/sales metric ({field_name})",
                is_monetary=True,
                is_aggregate_revenue=True,
                sample_values=samples,
            )

        if f_lower in ("total_amount", "amount", "total") and (
            not c_lower or c_lower in cls.TRANSACTION_COLLECTIONS or "order" in c_lower or "trans" in c_lower
        ):
            return SemanticFieldProfile(
                name=field_name,
                concept=SemanticConcept.REVENUE,
                data_type=data_type,
                description=f"Transaction revenue / order total amount ({field_name})",
                is_monetary=True,
                is_aggregate_revenue=True,
                sample_values=samples,
            )

        # 7. Unit Price / Cost (Not total revenue!)
        if any(p in f_lower for p in ("price", "unit_price", "cost", "fee", "rate")):
            return SemanticFieldProfile(
                name=field_name,
                concept=SemanticConcept.PRICE,
                data_type=data_type,
                description=f"Unit price / rate per item ({field_name})",
                is_monetary=True,
                is_aggregate_revenue=False,
                sample_values=samples,
            )

        # 8. Quantity / Stock
        if any(q in f_lower for q in ("quantity", "stock", "units", "inventory", "count", "items")):
            return SemanticFieldProfile(
                name=field_name,
                concept=SemanticConcept.QUANTITY,
                data_type=data_type,
                description=f"Physical item or count metric ({field_name})",
                sample_values=samples,
            )

        # 9. Banking / Transaction Value
        if any(b in f_lower for b in ("transfer_amount", "loan_amount", "credit_limit", "balance")):
            return SemanticFieldProfile(
                name=field_name,
                concept=SemanticConcept.TRANSACTION_VALUE,
                data_type=data_type,
                description=f"Financial transaction value ({field_name})",
                is_monetary=True,
                sample_values=samples,
            )

        # 10. General Numeric
        if data_type in ("Double", "Int64", "Number", "Integer"):
            return SemanticFieldProfile(
                name=field_name,
                concept=SemanticConcept.GENERAL_NUMERIC,
                data_type=data_type,
                description=f"Numeric metric ({field_name})",
                sample_values=samples,
            )

        return SemanticFieldProfile(
            name=field_name,
            concept=SemanticConcept.CATEGORICAL if data_type == "String" else SemanticConcept.UNKNOWN,
            data_type=data_type,
            description=f"Attribute ({field_name})",
            sample_values=samples,
        )

    @classmethod
    def match_requested_metric(
        cls,
        requested_concept: str,
        collection_name: str,
        available_columns: list[dict[str, Any]],
    ) -> MetricMatchResult:
        """
        Validates whether the collection contains a field that genuinely answers the requested metric.
        Never substitutes GPA, salary, price, or spending for revenue.
        """
        req_norm = requested_concept.upper().strip()

        profiles = [
            cls.classify_field(
                col["name"],
                collection_name=collection_name,
                data_type=col.get("data_type", "String"),
                sample_values=col.get("sample_values", []),
            )
            for col in available_columns
        ]

        # Scenario: User asked for REVENUE or SALES
        if req_norm in ("REVENUE", "SALES", "TOTAL_REVENUE", "TURNOVER"):
            # Check for direct aggregate revenue fields
            exact_matches = [p for p in profiles if p.is_aggregate_revenue]
            if exact_matches:
                chosen = exact_matches[0]
                return MetricMatchResult(
                    status="EXACT_MATCH",
                    field_name=chosen.name,
                    concept=chosen.concept,
                    explanation=f"Revenue is represented by `{collection_name}.{chosen.name}`.",
                    confidence=0.98,
                )

            # Check for related monetary fields (e.g. customer total_spent or price)
            spending_matches = [p for p in profiles if p.concept == SemanticConcept.CUSTOMER_SPENDING]
            if spending_matches:
                spent_field = spending_matches[0].name
                return MetricMatchResult(
                    status="RELATED_ALTERNATIVE",
                    field_name=spent_field,
                    concept=SemanticConcept.CUSTOMER_SPENDING,
                    explanation=(
                        f"Revenue is not available in the `{collection_name}` collection. "
                        f"A related field, `{spent_field}` (customer spending), is available. "
                        f"If you want customer spending, I can calculate it."
                    ),
                    alternative_fields=[
                        {
                            "name": spent_field,
                            "label": f"Calculate {spent_field.replace('_', ' ').title()}",
                            "description": "Customer cumulative expenditure",
                        }
                    ],
                    confidence=0.85,
                )

            price_matches = [p for p in profiles if p.concept == SemanticConcept.PRICE]
            if price_matches:
                p_field = price_matches[0].name
                return MetricMatchResult(
                    status="RELATED_ALTERNATIVE",
                    field_name=p_field,
                    concept=SemanticConcept.PRICE,
                    explanation=(
                        f"Revenue is not available in the `{collection_name}` collection. "
                        f"The collection contains `{p_field}`, which is a unit price per item, not total sales revenue."
                    ),
                    alternative_fields=[
                        {
                            "name": p_field,
                            "label": f"Average {p_field.replace('_', ' ').title()}",
                            "description": "Unit catalog price",
                        }
                    ],
                    confidence=0.75,
                )

            # Incompatible fields found (e.g. GPA in students)
            academic_matches = [p for p in profiles if p.concept == SemanticConcept.ACADEMIC]
            if academic_matches:
                names = [p.name for p in academic_matches]
                return MetricMatchResult(
                    status="INCOMPATIBLE",
                    explanation=(
                        f"Revenue is not available in the `{collection_name}` collection. "
                        f"I found academic fields such as {', '.join(names)}, but none can be safely interpreted as revenue."
                    ),
                    confidence=0.95,
                )

            other_numerics = [p.name for p in profiles if p.concept in (SemanticConcept.GENERAL_NUMERIC, SemanticConcept.QUANTITY, SemanticConcept.COMPENSATION)]
            if other_numerics:
                return MetricMatchResult(
                    status="INCOMPATIBLE",
                    explanation=(
                        f"Revenue is not available in the `{collection_name}` collection. "
                        f"I found numeric fields ({', '.join(other_numerics[:3])}), but none represent revenue or sales."
                    ),
                    confidence=0.95,
                )

            return MetricMatchResult(
                status="NOT_FOUND",
                explanation=f"Revenue data is not available in the `{collection_name}` collection.",
                confidence=0.95,
            )

        # Scenario: User asked for SPENDING (e.g. "how much did customers spend?")
        if req_norm in ("SPENDING", "CUSTOMER_SPENDING", "EXPENSE"):
            spending_matches = [p for p in profiles if p.concept == SemanticConcept.CUSTOMER_SPENDING]
            if spending_matches:
                chosen = spending_matches[0]
                return MetricMatchResult(
                    status="EXACT_MATCH",
                    field_name=chosen.name,
                    concept=chosen.concept,
                    explanation=f"Customer spending is represented by `{collection_name}.{chosen.name}`.",
                    confidence=0.98,
                )
            rev_matches = [p for p in profiles if p.is_aggregate_revenue]
            if rev_matches:
                rev_field = rev_matches[0].name
                return MetricMatchResult(
                    status="RELATED_ALTERNATIVE",
                    field_name=rev_field,
                    concept=SemanticConcept.REVENUE,
                    explanation=(
                        f"Spending is not directly available in `{collection_name}`, but transaction revenue "
                        f"(`{rev_field}`) is available."
                    ),
                    confidence=0.85,
                )

        # Scenario: User asked for GPA or ACADEMIC
        if req_norm in ("GPA", "GRADE", "ACADEMIC", "SCORE"):
            acad_matches = [p for p in profiles if p.concept == SemanticConcept.ACADEMIC]
            if acad_matches:
                chosen = acad_matches[0]
                return MetricMatchResult(
                    status="EXACT_MATCH",
                    field_name=chosen.name,
                    concept=chosen.concept,
                    explanation=f"Academic performance is represented by `{collection_name}.{chosen.name}`.",
                    confidence=0.98,
                )

        # Scenario: User asked for SALARY / COMPENSATION
        if req_norm in ("SALARY", "COMPENSATION", "WAGE"):
            comp_matches = [p for p in profiles if p.concept == SemanticConcept.COMPENSATION]
            if comp_matches:
                chosen = comp_matches[0]
                return MetricMatchResult(
                    status="EXACT_MATCH",
                    field_name=chosen.name,
                    concept=chosen.concept,
                    explanation=f"Salary is represented by `{collection_name}.{chosen.name}`.",
                    confidence=0.98,
                )

        # Scenario: User asked for PRICE
        if req_norm in ("PRICE", "COST"):
            price_matches = [p for p in profiles if p.concept == SemanticConcept.PRICE]
            if price_matches:
                chosen = price_matches[0]
                return MetricMatchResult(
                    status="EXACT_MATCH",
                    field_name=chosen.name,
                    concept=chosen.concept,
                    explanation=f"Price is represented by `{collection_name}.{chosen.name}`.",
                    confidence=0.98,
                )

        # Scenario: User asked for QUANTITY / STOCK / INVENTORY
        if req_norm in ("QUANTITY", "STOCK", "INVENTORY", "UNITS"):
            qty_matches = [p for p in profiles if p.concept == SemanticConcept.QUANTITY]
            if qty_matches:
                chosen = qty_matches[0]
                return MetricMatchResult(
                    status="EXACT_MATCH",
                    field_name=chosen.name,
                    concept=chosen.concept,
                    explanation=f"Stock/Quantity is represented by `{collection_name}.{chosen.name}`.",
                    confidence=0.98,
                )

        return MetricMatchResult(
            status="NOT_FOUND",
            explanation=f"The metric '{requested_concept}' is not present in `{collection_name}`.",
            confidence=0.90,
        )
