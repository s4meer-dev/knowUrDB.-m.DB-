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
