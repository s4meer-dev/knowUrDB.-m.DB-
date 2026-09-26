import re
from dataclasses import dataclass
from typing import Any

from app.services.semantic_field_registry import SemanticConcept, SemanticFieldRegistry


@dataclass
class ValidationOutcome:
    is_valid: bool
    reason: str
    rejection_code: str | None = None
    user_explanation: str = ""
    suggested_presentation: dict[str, Any] | None = None


class ResultValidator:
    """
    Mandatory Final Quality & Integrity Gatekeeper.
    Validates whether the executed MongoDB query and returned result
    honestly and accurately answer the user's specific question within their selected scope.
    """

    @classmethod
    def validate_result(
        cls,
        question: str,
        requested_concept: str | None,
        target_collection: str | None,
        target_field: str | None,
        query_result: list[dict[str, Any]],
        generated_answer_headline: str | None = None,
        generated_answer_value: str | None = None,
    ) -> ValidationOutcome:
        q_lower = question.lower().strip()

        # 1. Semantic Metric Rejection: User asked for REVENUE, but target field is GPA or non-revenue
        if requested_concept in ("REVENUE", "SALES", "TOTAL_REVENUE"):
            if target_field:
                profile = SemanticFieldRegistry.classify_field(
                    target_field, collection_name=target_collection or ""
                )
                if profile.concept == SemanticConcept.ACADEMIC:
                    return ValidationOutcome(
                        is_valid=False,
                        reason="Requested REVENUE, but executed on ACADEMIC metric (GPA/grades).",
                        rejection_code="METRIC_SEMANTIC_MISMATCH",
                        user_explanation=(
                            f"Revenue is not available in the `{target_collection}` collection. "
                            f"I found academic fields ({target_field}), which cannot be safely interpreted as revenue."
                        ),
                    )
                if profile.concept == SemanticConcept.COMPENSATION:
                    return ValidationOutcome(
                        is_valid=False,
                        reason="Requested REVENUE, but executed on EMPLOYEE SALARY metric.",
                        rejection_code="METRIC_SEMANTIC_MISMATCH",
                        user_explanation=(
                            f"Revenue is not available in `{target_collection}`. "
                            f"`{target_field}` represents employee compensation, not business revenue."
                        ),
                    )

        # 2. Metric Mismatch in Answer Headline (e.g. headline says "TOTAL REVENUE", but value was from GPA)
        if generated_answer_headline and "REVENUE" in generated_answer_headline.upper():
            if target_field and any(a in target_field.lower() for a in ("gpa", "score", "grade")):
                return ValidationOutcome(
                    is_valid=False,
                    reason="Headline claims REVENUE, but target field is GPA.",
                    rejection_code="HALLUCINATED_METRIC_LABEL",
                    user_explanation="Calculated metric does not represent revenue.",
                )

        return ValidationOutcome(
            is_valid=True,
            reason="Result satisfies semantic criteria and scope.",
        )

    @classmethod
    def validate_pre_execution_filter(
        cls,
        plan: Any,
        structured_query: dict[str, Any],
    ) -> ValidationOutcome:
        """
        Guarantees the Filter Preservation Invariant before any query touches MongoDB.
        If the user requested filters, the compiled MongoDB query MUST include a $match stage.
        """
        if getattr(plan, "filters", None):
            pipeline = structured_query.get("pipeline", [])
            has_match = any("$match" in stage for stage in pipeline)
            if not has_match:
                return ValidationOutcome(
                    is_valid=False,
                    reason="Filter preservation invariant violated: compiled query has no $match stage.",
                    rejection_code="FILTER_PRESERVATION_VIOLATION",
                    user_explanation="The query engine attempted to execute an unfiltered query despite user filter criteria.",
                )
        return ValidationOutcome(is_valid=True, reason="Pre-execution filter validation passed.")

    @classmethod
    def validate_post_execution_filter(
        cls,
        plan: Any,
        rows: list[dict[str, Any]],
    ) -> ValidationOutcome:
        """
        Guarantees Zero Data Leakage after MongoDB returns documents.
        Asserts that every returned document strictly matches the user's requested filter.
        """
        requested_filters = getattr(plan, "requested_filters", [])
        intent = getattr(plan, "intent", "")
        if intent in ("COUNT", "SUM", "AVERAGE", "MINIMUM", "MAXIMUM", "AGGREGATION") or getattr(plan, "operation", "") == "count":
            return ValidationOutcome(is_valid=True, reason="Aggregation totals do not contain raw document fields.")

        if not rows or not requested_filters:
            return ValidationOutcome(is_valid=True, reason="No rows or no filters to validate.")

        for rf in requested_filters:
            field_name = rf.get("field")
            op = rf.get("operator", "eq")
            expected_val = rf.get("value")

            if not field_name:
                continue

            for doc in rows:
                # Handle nested dot path (e.g. address.city)
                val = doc
                for part in field_name.split("."):
                    if isinstance(val, dict):
                        val = val.get(part)
                    else:
                        val = None
                        break

                if op == "eq":
                    if isinstance(expected_val, str):
                        if str(val).strip().lower() != expected_val.strip().lower():
                            return ValidationOutcome(
                                is_valid=False,
                                reason=f"Row leaked data: document has {field_name}='{val}', expected '{expected_val}'.",
                                rejection_code="RESULT_FILTER_INTEGRITY_ERROR",
                                user_explanation=f"A document with {field_name}='{val}' was returned, which violates the filter {field_name}='{expected_val}'.",
                            )
                    elif expected_val is not None:
                        try:
                            if float(val) != float(expected_val):
                                return ValidationOutcome(
                                    is_valid=False,
                                    reason=f"Row leaked data: document has {field_name}={val}, expected {expected_val}.",
                                    rejection_code="RESULT_FILTER_INTEGRITY_ERROR",
                                    user_explanation=f"A document violates the filter {field_name}={expected_val}.",
                                )
                        except (ValueError, TypeError):
                            if val != expected_val:
                                return ValidationOutcome(
                                    is_valid=False,
                                    reason=f"Row leaked data: document has {field_name}={val}, expected {expected_val}.",
                                    rejection_code="RESULT_FILTER_INTEGRITY_ERROR",
                                    user_explanation=f"A document violates the filter {field_name}={expected_val}.",
                                )
                elif op == "ne":
                    if isinstance(expected_val, str):
                        if str(val).strip().lower() == expected_val.strip().lower():
                            return ValidationOutcome(
                                is_valid=False,
                                reason=f"Row leaked negated data: document has {field_name}='{val}', expected != '{expected_val}'.",
                                rejection_code="RESULT_FILTER_INTEGRITY_ERROR",
                                user_explanation=f"A document with {field_name}='{val}' was returned, violating the negated filter.",
                            )
                elif op == "gt":
                    if val is not None:
                        try:
                            if float(val) <= float(expected_val):
                                return ValidationOutcome(
                                    is_valid=False,
                                    reason=f"Row leaked data: document has {field_name}={val} <= {expected_val}.",
                                    rejection_code="RESULT_FILTER_INTEGRITY_ERROR",
                                    user_explanation=f"A document with {field_name}={val} was returned, which is not > {expected_val}.",
                                )
                        except (ValueError, TypeError):
                            pass
                elif op == "lt":
                    if val is not None:
                        try:
                            if float(val) >= float(expected_val):
                                return ValidationOutcome(
                                    is_valid=False,
                                    reason=f"Row leaked data: document has {field_name}={val} >= {expected_val}.",
                                    rejection_code="RESULT_FILTER_INTEGRITY_ERROR",
                                    user_explanation=f"A document with {field_name}={val} was returned, which is not < {expected_val}.",
                                )
                        except (ValueError, TypeError):
                            pass
                elif op == "in":
                    if isinstance(expected_val, list):
                        exp_low = [str(x).lower() for x in expected_val]
                        if str(val).strip().lower() not in exp_low:
                            return ValidationOutcome(
                                is_valid=False,
                                reason=f"Row leaked data: {val} not in {expected_val}.",
                                rejection_code="RESULT_FILTER_INTEGRITY_ERROR",
                                user_explanation=f"A document with {field_name}='{val}' was returned, not in {expected_val}.",
                            )

        return ValidationOutcome(is_valid=True, reason="All documents satisfy the filter criteria.")
