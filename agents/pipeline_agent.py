"""Sales pipeline reporting agent for explicit, locally stored milestones."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

PIPELINE_AGENT_VERSION = "0.1"
VALID_GRADES = ("A", "B", "C")
VALID_STAGES = (
    "new",
    "clarification",
    "qualified",
    "sample",
    "quotation",
    "order",
    "closed",
    "lost",
)
MILESTONES = (
    "outreach_drafted",
    "outreach_sent",
    "reply_received",
    "sample_started",
    "quotation_issued",
    "order_confirmed",
)


def _qualification(record: dict[str, Any]) -> dict[str, Any]:
    nested = record.get("qualification")
    return nested if isinstance(nested, dict) else {}


def _grade(record: dict[str, Any]) -> str:
    value = record.get("grade", _qualification(record).get("grade", ""))
    grade = str(value).strip().upper()
    return grade if grade in VALID_GRADES else "Needs verification"


def _score(record: dict[str, Any]) -> Any:
    value = record.get("score", _qualification(record).get("score"))
    return value if isinstance(value, (int, float)) else "Needs verification"


def _stage(record: dict[str, Any]) -> str:
    stage = str(record.get("stage", "")).strip().lower()
    return stage if stage in VALID_STAGES else "Needs verification"


def _milestone(record: dict[str, Any], name: str) -> bool:
    milestones = record.get("milestones")
    return isinstance(milestones, dict) and milestones.get(name) is True


def _next_action(record: dict[str, Any]) -> str:
    value = record.get("next_action", _qualification(record).get("next_action"))
    return str(value).strip() if value else "Needs verification"


def _blocker(record: dict[str, Any]) -> str:
    value = record.get("blocker")
    return str(value).strip() if value else ""


def _priority_queue(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grade_order = {"A": 0, "B": 1, "C": 2, "Needs verification": 3}
    items = []
    for index, record in enumerate(records, start=1):
        grade = _grade(record)
        if grade not in ("A", "B"):
            continue
        items.append(
            {
                "record_id": record.get("record_id") or f"ROW-{index:03d}",
                "grade": grade,
                "score": _score(record),
                "stage": _stage(record),
                "country": record.get("country", "Needs verification"),
                "segment": record.get("segment", "Needs verification"),
                "next_action": _next_action(record),
                "blocker": _blocker(record) or "None recorded",
            }
        )

    def sort_key(item: dict[str, Any]) -> tuple[int, float]:
        score = item["score"]
        numeric_score = float(score) if isinstance(score, (int, float)) else -1.0
        return grade_order[item["grade"]], -numeric_score

    return sorted(items, key=sort_key)


def build_pipeline_report(pipeline_data: dict[str, Any]) -> dict[str, Any]:
    """Summarize explicit B2B pipeline records without inferring milestones."""

    if not isinstance(pipeline_data, dict):
        raise ValueError("pipeline_data must be a dictionary.")
    records = pipeline_data.get("records")
    if not isinstance(records, list) or any(
        not isinstance(record, dict) for record in records
    ):
        raise ValueError("pipeline_data must contain a records list of dictionaries.")

    grade_counts = {
        grade: sum(_grade(record) == grade for record in records)
        for grade in (*VALID_GRADES, "Needs verification")
    }
    stage_counts = {
        stage: sum(_stage(record) == stage for record in records)
        for stage in (*VALID_STAGES, "Needs verification")
    }
    milestone_counts = {
        milestone: sum(_milestone(record, milestone) for record in records)
        for milestone in MILESTONES
    }
    blockers = []
    for index, record in enumerate(records, start=1):
        blocker = _blocker(record)
        if blocker:
            blockers.append(
                {
                    "record_id": record.get("record_id") or f"ROW-{index:03d}",
                    "grade": _grade(record),
                    "blocker": blocker,
                    "owner": record.get("owner", "Needs verification"),
                }
            )

    missing_ids = sum(not record.get("record_id") for record in records)
    unverified_grades = grade_counts["Needs verification"]
    return {
        "pipeline_agent_version": PIPELINE_AGENT_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "period": {
            "start": (
                pipeline_data.get("period", {}).get("start")
                or "Needs verification"
            )
            if isinstance(pipeline_data.get("period"), dict)
            else "Needs verification",
            "end": (
                pipeline_data.get("period", {}).get("end")
                or "Needs verification"
            )
            if isinstance(pipeline_data.get("period"), dict)
            else "Needs verification",
        },
        "summary": {
            "new_leads_or_inquiries": len(records),
            "grade_counts": grade_counts,
            "outreach_drafted": milestone_counts["outreach_drafted"],
            "outreach_sent": milestone_counts["outreach_sent"],
            "replies_received": milestone_counts["reply_received"],
            "qualified_inquiries": grade_counts["A"],
            "samples": milestone_counts["sample_started"],
            "quotations": milestone_counts["quotation_issued"],
            "orders": milestone_counts["order_confirmed"],
            "active_blockers": len(blockers),
        },
        "stage_counts": stage_counts,
        "milestone_counts": milestone_counts,
        "priority_queue": _priority_queue(records),
        "blockers": blockers,
        "data_quality": {
            "records_missing_id": missing_ids,
            "records_missing_verified_grade": unverified_grades,
            "milestone_rule": "Counts include only fields explicitly set to true.",
        },
        "recommended_improvement": {
            "status": "Needs review",
            "action": "Review the highest-priority blocker and one evidence-based targeting, landing-page, messaging, or follow-up improvement.",
        },
        "approval_gate": {
            "external_messages_allowed": False,
            "crm_write_allowed": False,
            "record_updates_allowed": False,
            "status": "report_only",
        },
        "privacy": {
            "contains_or_summarizes_personal_data": True,
            "storage_rule": "Keep real pipeline inputs and reports out of the public repository.",
        },
    }
