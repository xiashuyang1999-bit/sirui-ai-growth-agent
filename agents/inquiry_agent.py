"""Inquiry qualification agent for local, approval-gated B2B review."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

INQUIRY_AGENT_VERSION = "0.1"

B2B_SEGMENTS = {
    "importer",
    "distributor",
    "paint-tool brand",
    "hardware distributor",
    "building-material distributor",
    "wholesaler",
    "private-label buyer",
}

QUOTE_FIELDS = [
    "product",
    "material",
    "size",
    "components",
    "quantity",
    "oem_private_label",
    "packaging",
    "destination",
    "target_delivery_time",
    "sample_requirements",
]

QUESTION_MAP = {
    "company": "What is your company name and website?",
    "country": "Which country and market will the products be supplied to?",
    "segment": "Is your company an importer, distributor, brand, wholesaler, or private-label buyer?",
    "product": "Which paint roller, cover, frame, set, or other painting tool are you sourcing?",
    "material": "Which material or performance requirement should be reviewed?",
    "size": "Which size, width, nap, or relevant dimensions do you require?",
    "components": "Which cover, frame, handle, core, or set components are required?",
    "quantity": "What estimated quantity should the sales team review?",
    "oem_private_label": "Do you require OEM, ODM, logo, color, or private-label support?",
    "packaging": "What retail packaging, label, or carton requirements should be reviewed?",
    "destination": "What is the destination country or port?",
    "target_delivery_time": "What target delivery timing should be considered?",
    "sample_requirements": "Do you need samples, and which product or specification should be sampled?",
}


def _has_value(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, dict, set)):
        return bool(value)
    return True


def _normalized_segment(value: Any) -> str:
    return str(value or "").strip().lower()


def _score_inquiry(inquiry: dict[str, Any]) -> tuple[int, list[str]]:
    score = 0
    evidence = []

    scoring_rules = [
        ("company", 10, "Company name supplied"),
        ("website", 10, "Company website supplied"),
        ("contact_name", 5, "Named contact supplied"),
        ("email", 5, "Contact email supplied"),
        ("product", 15, "Relevant product requirement supplied"),
        ("quantity", 10, "Estimated quantity supplied"),
        ("country", 5, "Buyer country supplied"),
    ]
    for field, points, label in scoring_rules:
        if _has_value(inquiry.get(field)):
            score += points
            evidence.append(f"+{points}: {label}")

    if inquiry.get("company_verified") is True:
        score += 15
        evidence.append("+15: Company verification explicitly confirmed")

    if _normalized_segment(inquiry.get("segment")) in B2B_SEGMENTS:
        score += 15
        evidence.append("+15: Segment matches the target B2B buyer profile")

    if any(_has_value(inquiry.get(field)) for field in ("material", "size", "components")):
        score += 5
        evidence.append("+5: Product specification detail supplied")

    if any(
        _has_value(inquiry.get(field))
        for field in ("oem_private_label", "packaging")
    ):
        score += 5
        evidence.append("+5: OEM, private-label, or packaging requirement supplied")

    score = min(score, 100)
    if inquiry.get("company_verified") is not True and score > 69:
        evidence.append("Score capped at 69 because company verification is not confirmed")
        score = 69
    return score, evidence


def _grade(score: int) -> str:
    if score >= 70:
        return "A"
    if score >= 45:
        return "B"
    return "C"


def _missing_fields(inquiry: dict[str, Any]) -> tuple[list[str], list[str]]:
    identity_fields = [
        "company",
        "website",
        "contact_name",
        "email",
        "country",
        "segment",
    ]
    missing_identity = [
        field for field in identity_fields if not _has_value(inquiry.get(field))
    ]
    missing_quote = [
        field for field in QUOTE_FIELDS if not _has_value(inquiry.get(field))
    ]
    return missing_identity, missing_quote


def _questions(fields: list[str]) -> list[str]:
    questions = []
    for field in fields:
        question = QUESTION_MAP.get(field)
        if question and question not in questions:
            questions.append(question)
        if len(questions) == 5:
            break
    return questions


def _reply_draft(
    inquiry: dict[str, Any], grade: str, questions: list[str]
) -> dict[str, Any]:
    name = str(inquiry.get("contact_name") or "there").strip()
    product = str(inquiry.get("product") or "painting tools").strip()
    company = str(inquiry.get("company") or "your company").strip()
    subject = f"Your {product} inquiry - information for review"

    lines = [
        f"Hi {name},",
        "",
        f"Thank you for your inquiry about {product} for {company}.",
    ]
    if questions:
        lines.extend(
            [
                "To help our sales team review the request, please confirm:",
                *[f"- {question}" for question in questions],
            ]
        )
    elif grade == "A":
        lines.append(
            "The supplied company and project details are ready for an internal sales review."
        )
    else:
        lines.append(
            "Please share your company and product requirements so the request can be reviewed."
        )
    lines.extend(
        [
            "",
            "Pricing, MOQ, samples, specifications, and lead time remain subject to sales confirmation.",
            "",
            "Best regards,",
            "SIRUI Sales Team",
        ]
    )
    return {
        "subject": subject,
        "body": "\n".join(lines),
        "language": "English",
        "status": "approval_required",
        "sent": False,
    }


def qualify_inquiry(inquiry: dict[str, Any]) -> dict[str, Any]:
    """Score one local inquiry and prepare a human-review package."""

    if not isinstance(inquiry, dict):
        raise ValueError("inquiry must be a dictionary.")

    score, score_evidence = _score_inquiry(inquiry)
    grade = _grade(score)
    missing_identity, missing_quote = _missing_fields(inquiry)
    clarification_questions = _questions(missing_identity + missing_quote)

    if grade == "A":
        status = "qualified_priority"
        next_action = "Route to sales for human review within 15 minutes."
    elif grade == "B":
        status = "needs_clarification"
        next_action = "Review the company evidence and request the missing project details."
    else:
        status = "low_priority_or_unverified"
        next_action = "Verify the company identity and B2B requirement before sales prioritization."

    quotation_checklist = {
        field: inquiry.get(field) if _has_value(inquiry.get(field)) else "Needs verification"
        for field in QUOTE_FIELDS
    }
    return {
        "inquiry_agent_version": INQUIRY_AGENT_VERSION,
        "qualified_at": datetime.now(timezone.utc).isoformat(),
        "source": inquiry.get("source", "Needs verification"),
        "qualification": {
            "score": score,
            "grade": grade,
            "status": status,
            "company_verified": inquiry.get("company_verified") is True,
            "score_evidence": score_evidence,
            "missing_identity_fields": missing_identity,
            "missing_quotation_fields": missing_quote,
            "next_action": next_action,
        },
        "clarification_questions": clarification_questions,
        "quotation_checklist": quotation_checklist,
        "reply_draft": _reply_draft(inquiry, grade, clarification_questions),
        "approval_gate": {
            "external_message_allowed": False,
            "crm_write_allowed": False,
            "quotation_allowed": False,
            "required_approver": "sales owner",
            "status": "review_required",
        },
        "privacy": {
            "contains_personal_data": True,
            "storage_rule": "Keep real inquiry input and output out of the public repository.",
        },
    }
