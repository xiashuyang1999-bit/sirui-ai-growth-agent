"""Local analytics and conversion reporting for approved exported metrics."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

ANALYTICS_AGENT_VERSION = "0.1"
NEEDS_VERIFICATION = "Needs verification"


def _metric(data: dict[str, Any], section: str, field: str) -> int | float | None:
    section_data = data.get(section)
    if not isinstance(section_data, dict):
        return None
    value = section_data.get(field)
    if value in (None, ""):
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{section}.{field} must be a non-negative number or null.")
    if value < 0:
        raise ValueError(f"{section}.{field} must be a non-negative number or null.")
    return value


def _reported(value: int | float | None) -> int | float | str:
    return value if value is not None else NEEDS_VERIFICATION


def _rate(numerator: int | float | None, denominator: int | float | None) -> float | str:
    if numerator is None or denominator is None or denominator <= 0:
        return NEEDS_VERIFICATION
    return round((numerator / denominator) * 100, 2)


def _validation_issues(metrics: dict[str, int | float | None]) -> list[str]:
    issues = []
    comparisons = [
        ("engaged_sessions", "sessions", "Engaged sessions exceed sessions."),
        ("search_clicks", "search_impressions", "Search clicks exceed impressions."),
        ("sample_projects", "qualified_inquiries", "Sample projects exceed qualified inquiries."),
        ("quotations", "qualified_inquiries", "Quotations exceed qualified inquiries."),
        ("orders", "quotations", "Orders exceed quotations."),
    ]
    for numerator_name, denominator_name, message in comparisons:
        numerator = metrics[numerator_name]
        denominator = metrics[denominator_name]
        if (
            numerator is not None
            and denominator is not None
            and numerator > denominator
        ):
            issues.append(message)
    average_position = metrics["average_position"]
    if average_position is not None and average_position <= 0:
        issues.append("Average search position must be greater than zero when supplied.")
    return issues


def _opportunities(
    metrics: dict[str, int | float | None], attribution_scope: str
) -> list[dict[str, str]]:
    opportunities = []
    if all(value is None for value in metrics.values()):
        opportunities.append(
            {
                "area": "data",
                "evidence": "No approved metric values were supplied.",
                "next_action": "Export and normalize approved GA4, Search Console, form, and sales-pipeline data.",
            }
        )
        return opportunities

    if metrics["search_impressions"] and metrics["search_clicks"] == 0:
        opportunities.append(
            {
                "area": "search_clicks",
                "evidence": "Search impressions are recorded but search clicks are zero.",
                "next_action": "Review query relevance, page titles, descriptions, indexability, and reporting filters.",
            }
        )
    if metrics["sessions"] and metrics["inquiry_submissions"] == 0:
        opportunities.append(
            {
                "area": "website_conversion",
                "evidence": "Website sessions are recorded but inquiry submissions are zero.",
                "next_action": "Verify form tracking, inquiry delivery, CTA visibility, and landing-page buyer fit.",
            }
        )
    if (
        attribution_scope == "website_only"
        and metrics["inquiry_submissions"]
        and metrics["qualified_inquiries"] == 0
    ):
        opportunities.append(
            {
                "area": "inquiry_quality",
                "evidence": "Website inquiries are recorded but no website-attributed qualified inquiry is recorded.",
                "next_action": "Review traffic targeting, form fields, qualification rules, and source attribution.",
            }
        )
    if metrics["qualified_inquiries"] and metrics["quotations"] == 0:
        opportunities.append(
            {
                "area": "sales_progression",
                "evidence": "Qualified inquiries are recorded but no quotation is recorded.",
                "next_action": "Review missing specifications, response time, quotation readiness, and opportunity blockers.",
            }
        )
    if metrics["quotations"] and metrics["orders"] == 0:
        opportunities.append(
            {
                "area": "quotation_followup",
                "evidence": "Quotations are recorded but no confirmed order is recorded.",
                "next_action": "Review quotation follow-up, buyer objections, specification fit, and decision timing.",
            }
        )
    if not opportunities:
        opportunities.append(
            {
                "area": "monitoring",
                "evidence": "No zero-progression gap was detected in the supplied aggregate values.",
                "next_action": "Review market, source, landing-page, query, and product breakdowns before selecting an improvement.",
            }
        )
    return opportunities


def build_analytics_report(metrics_data: dict[str, Any]) -> dict[str, Any]:
    """Build a conversion report from local, explicitly supplied metrics."""

    if not isinstance(metrics_data, dict):
        raise ValueError("metrics_data must be a dictionary.")

    metrics = {
        "sessions": _metric(metrics_data, "website", "sessions"),
        "engaged_sessions": _metric(
            metrics_data, "website", "engaged_sessions"
        ),
        "inquiry_submissions": _metric(
            metrics_data, "website", "inquiry_submissions"
        ),
        "search_clicks": _metric(metrics_data, "search", "clicks"),
        "search_impressions": _metric(metrics_data, "search", "impressions"),
        "average_position": _metric(
            metrics_data, "search", "average_position"
        ),
        "qualified_inquiries": _metric(
            metrics_data, "sales", "qualified_inquiries"
        ),
        "sample_projects": _metric(metrics_data, "sales", "sample_projects"),
        "quotations": _metric(metrics_data, "sales", "quotations"),
        "orders": _metric(metrics_data, "sales", "orders"),
    }
    sales_data = metrics_data.get("sales")
    attribution_scope = (
        str(sales_data.get("attribution_scope") or NEEDS_VERIFICATION)
        if isinstance(sales_data, dict)
        else NEEDS_VERIFICATION
    )
    website_qualified_rate = (
        _rate(metrics["qualified_inquiries"], metrics["inquiry_submissions"])
        if attribution_scope == "website_only"
        else NEEDS_VERIFICATION
    )
    period_data = metrics_data.get("period")
    period = period_data if isinstance(period_data, dict) else {}
    validation_issues = _validation_issues(metrics)
    has_any_metric = any(value is not None for value in metrics.values())
    if not has_any_metric:
        validation_status = "insufficient_data"
    elif validation_issues:
        validation_status = "needs_review"
    else:
        validation_status = "pass"

    return {
        "analytics_agent_version": ANALYTICS_AGENT_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "period": {
            "start": period.get("start") or NEEDS_VERIFICATION,
            "end": period.get("end") or NEEDS_VERIFICATION,
        },
        "data_scope": {
            "sales_attribution_scope": attribution_scope,
            "input_mode": "local_approved_export",
            "external_accounts_accessed": False,
        },
        "metrics": {name: _reported(value) for name, value in metrics.items()},
        "rates_percent": {
            "engagement_rate": _rate(
                metrics["engaged_sessions"], metrics["sessions"]
            ),
            "search_click_through_rate": _rate(
                metrics["search_clicks"], metrics["search_impressions"]
            ),
            "website_inquiry_rate": _rate(
                metrics["inquiry_submissions"], metrics["sessions"]
            ),
            "website_inquiry_to_qualified_rate": website_qualified_rate,
            "qualified_to_sample_rate": _rate(
                metrics["sample_projects"], metrics["qualified_inquiries"]
            ),
            "qualified_to_quotation_rate": _rate(
                metrics["quotations"], metrics["qualified_inquiries"]
            ),
            "quotation_to_order_rate": _rate(
                metrics["orders"], metrics["quotations"]
            ),
        },
        "validation": {
            "status": validation_status,
            "issues": validation_issues,
            "rule": "Missing values remain Needs verification and are never converted to zero.",
        },
        "opportunities": _opportunities(metrics, attribution_scope),
        "breakdowns": metrics_data.get("breakdowns", {}),
        "approval_gate": {
            "external_account_access_allowed": False,
            "analytics_write_allowed": False,
            "crm_write_allowed": False,
            "status": "report_only",
        },
        "privacy": {
            "may_contain_commercial_data": True,
            "storage_rule": "Keep real analytics inputs and reports out of the public repository.",
        },
    }
