"""Approval-gated follow-up planning for overseas B2B leads and inquiries."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

FOLLOWUP_AGENT_VERSION = "0.1"
ELIGIBLE_GRADES = ("A", "B")


def _grade(lead: dict[str, Any]) -> str:
    qualification = lead.get("qualification")
    nested_grade = qualification.get("grade") if isinstance(qualification, dict) else ""
    grade = str(lead.get("grade") or nested_grade or "").strip().upper()
    return grade if grade in ("A", "B", "C") else "Needs verification"


def _start_date(lead: dict[str, Any]) -> tuple[date, str]:
    value = lead.get("start_date")
    if not value:
        return date.today(), "system_date"
    try:
        return date.fromisoformat(str(value)), "input"
    except ValueError as error:
        raise ValueError("start_date must use YYYY-MM-DD format.") from error


def _text(lead: dict[str, Any], field: str, fallback: str) -> str:
    value = lead.get(field)
    return str(value).strip() if value else fallback


def _stage_question(stage: str, product: str) -> str:
    questions = {
        "clarification": "Could you share the required product specification, quantity, packaging, and destination for review?",
        "qualified": f"Would you like the sales team to review relevant {product} options for your market?",
        "sample": "Could you confirm the product specifications and destination details that should be considered for the sample discussion?",
        "quotation": "Is there any product, packaging, quantity, or destination detail that should be clarified during quotation review?",
        "order": "Is there any approved order detail that requires clarification from the sales team?",
    }
    return questions.get(
        stage,
        f"Are {product} within your current buying scope?",
    )


def _message(
    day: int,
    due_date: date,
    objective: str,
    subject: str,
    body: str,
) -> dict[str, Any]:
    return {
        "day": day,
        "due_date": due_date.isoformat(),
        "channel": "email",
        "objective": objective,
        "subject": subject,
        "body": body,
        "word_count": len(body.split()),
        "status": "approval_required",
        "sent": False,
    }


def _build_sequence(lead: dict[str, Any], start: date) -> list[dict[str, Any]]:
    name = _text(lead, "contact_name", "there")
    company = _text(lead, "company", "your company")
    product = _text(lead, "product", "paint rollers")
    market = _text(lead, "market", _text(lead, "country", "your market"))
    stage = _text(lead, "stage", "new").lower()
    observation = ""
    if lead.get("fit_observation_verified") is True and lead.get("fit_observation"):
        observation = f" I noted that {str(lead['fit_observation']).strip()}"

    day_3 = (
        f"Hi {name},\n\n"
        f"I'm following up regarding {product} for {company}.{observation}\n"
        "SIRUI is a Paint Roller Manufacturer in China supporting OEM and private-label sourcing discussions. "
        f"{_stage_question(stage, product)}\n\n"
        "Best regards,\nSIRUI Sales Team"
    )
    day_7 = (
        f"Hi {name},\n\n"
        f"A quick follow-up on {product} for {market}. Does {company} source painting tools under its own brand? "
        "If so, which logo, color, handle, label, retail packaging, or carton details should be reviewed?\n\n"
        "Best regards,\nSIRUI Sales Team"
    )
    day_14 = (
        f"Hi {name},\n\n"
        f"I'm following up on the {product} discussion. Would approved factory and quality-control information, "
        "a short catalog review, or a sample discussion help your evaluation?\n\n"
        "Any specifications, pricing, MOQ, sample, or lead-time details remain subject to sales confirmation.\n\n"
        "Best regards,\nSIRUI Sales Team"
    )
    day_21 = (
        f"Hi {name},\n\n"
        f"When is {company}'s next purchasing window for {product}, and which specification and estimated quantity "
        "should the sales team review?\n\n"
        "Best regards,\nSIRUI Sales Team"
    )
    final = (
        f"Hi {name},\n\n"
        f"If this {product} category is not currently relevant for {company}, I will close the loop for now. "
        "If the timing changes, you can share the product, quantity, packaging, and market requirements for review.\n\n"
        "Best regards,\nSIRUI Sales Team"
    )

    return [
        _message(
            3,
            start + timedelta(days=3),
            "Confirm category fit or the next stage-specific input.",
            f"Follow-up: {product} for {market}",
            day_3,
        ),
        _message(
            7,
            start + timedelta(days=7),
            "Check OEM or private-label relevance.",
            f"Private-label {product} for {market}",
            day_7,
        ),
        _message(
            14,
            start + timedelta(days=14),
            "Offer an approved evidence, catalog, or sample discussion.",
            f"Factory and product review for {product}",
            day_14,
        ),
        _message(
            21,
            start + timedelta(days=21),
            "Ask about the next purchasing window.",
            f"Purchasing timing for {product}",
            day_21,
        ),
        _message(
            30,
            start + timedelta(days=30),
            "Close the loop respectfully.",
            f"Closing the loop on {product}",
            final,
        ),
    ]


def build_followup_plan(lead: dict[str, Any]) -> dict[str, Any]:
    """Build an unsent follow-up sequence for an eligible A/B record."""

    if not isinstance(lead, dict):
        raise ValueError("lead must be a dictionary.")

    grade = _grade(lead)
    start, start_source = _start_date(lead)
    eligible = grade in ELIGIBLE_GRADES
    sequence = _build_sequence(lead, start) if eligible else []
    generated_at = datetime.now(timezone.utc).isoformat()

    if grade == "C":
        recommendation = "Do not prioritize proactive follow-up; verify a relevant B2B requirement before reconsideration."
    elif grade == "Needs verification":
        recommendation = "Verify the A/B/C grade before creating a follow-up sequence."
    else:
        recommendation = "Review and approve each message shortly before its due date."

    return {
        "followup_agent_version": FOLLOWUP_AGENT_VERSION,
        "generated_at": generated_at,
        "start_date": start.isoformat(),
        "start_date_source": start_source,
        "lead_snapshot": {
            "record_id": _text(lead, "record_id", "Needs verification"),
            "grade": grade,
            "stage": _text(lead, "stage", "Needs verification"),
            "company": _text(lead, "company", "Needs verification"),
            "contact_name": _text(lead, "contact_name", "Needs verification"),
            "market": _text(
                lead,
                "market",
                _text(lead, "country", "Needs verification"),
            ),
            "product": _text(lead, "product", "Needs verification"),
        },
        "personalization_evidence": {
            "observation": _text(
                lead, "fit_observation", "Needs verification"
            ),
            "verified_for_draft": lead.get("fit_observation_verified") is True,
            "usage_rule": "Use the observation only when verified_for_draft is true.",
        },
        "sequence_status": "active_draft" if eligible else "not_recommended",
        "recommendation": recommendation,
        "followups": sequence,
        "summary": {
            "messages_drafted": len(sequence),
            "messages_sent": 0,
            "approval_required": len(sequence),
        },
        "approval_gate": {
            "external_message_allowed": False,
            "crm_write_allowed": False,
            "required_approver": "sales owner",
            "status": "draft_only",
        },
        "guardrails": [
            "Verify the company, contact, category fit, and observation before using any draft.",
            "Do not promise pricing, MOQ, samples, specifications, capacity, lead time, payment terms, or certifications.",
            "Review current conversation history before sending; stop the sequence if the buyer replies or opts out.",
            "Keep real lead inputs and follow-up plans out of the public repository.",
        ],
    }
