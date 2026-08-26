"""SEO planning agent built on structured website audit reports."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

SEO_AGENT_VERSION = "0.1"
DEFAULT_MARKETS = ["United States", "United Kingdom", "Australia"]
DEFAULT_AUDIENCES = ["importers", "distributors", "private-label buyers"]


PAGE_TYPE_STRATEGIES: dict[str, dict[str, Any]] = {
    "homepage": {
        "search_intent": "commercial investigation",
        "primary_keywords": [
            "paint roller manufacturer in china",
            "paint brush manufacturer in china",
        ],
        "secondary_keywords": [
            "OEM paint roller manufacturer",
            "private label painting tools",
            "wholesale paint brushes and rollers",
        ],
        "title_pattern": "Paint Brush & Paint Roller Manufacturer in China | SIRUI",
        "description_points": [
            "manufacturer positioning",
            "paint brushes and paint rollers",
            "OEM/ODM and private label",
            "importer and distributor audience",
        ],
    },
    "product_index": {
        "search_intent": "commercial category",
        "primary_keywords": [
            "wholesale paint brushes",
            "wholesale paint rollers",
        ],
        "secondary_keywords": [
            "OEM painting tools",
            "private label paint brushes",
            "paint roller supplier",
        ],
        "title_pattern": "Wholesale Paint Brushes & Paint Rollers | OEM Manufacturer | SIRUI",
        "description_points": [
            "product range",
            "wholesale and OEM availability",
            "distributor sourcing",
            "inquiry action",
        ],
    },
    "about": {
        "search_intent": "supplier validation",
        "primary_keywords": [
            "paint roller factory china",
            "paint brush factory china",
        ],
        "secondary_keywords": [
            "painting tool manufacturer",
            "paint tool quality control",
            "OEM painting tool factory",
        ],
        "title_pattern": "Paint Brush & Paint Roller Factory in China | SIRUI",
        "description_points": [
            "factory role",
            "production workflow",
            "quality-control evidence",
            "OEM sourcing support",
        ],
    },
    "b2b_service": {
        "search_intent": "commercial service",
        "primary_keywords": [
            "OEM paint roller manufacturer",
            "private label paint brushes",
        ],
        "secondary_keywords": [
            "ODM painting tools",
            "custom paint roller packaging",
            "private label painting tools supplier",
        ],
        "title_pattern": "OEM & Private Label Paint Brushes and Rollers | SIRUI",
        "description_points": [
            "OEM/ODM and private-label scope",
            "product categories",
            "custom packaging subject to verification",
            "project inquiry action",
        ],
    },
    "contact": {
        "search_intent": "conversion",
        "primary_keywords": ["SIRUI product inquiry", "painting tools request a quote"],
        "secondary_keywords": ["OEM paint roller inquiry", "paint brush quotation"],
        "title_pattern": "Request a Quote for Paint Brushes & Paint Rollers | SIRUI",
        "description_points": [
            "paint brush and paint roller inquiries",
            "OEM/private-label project context",
            "required buyer specifications",
            "sales contact action",
        ],
    },
}


def _product_detail_strategy(page: dict[str, Any]) -> dict[str, Any]:
    title = page.get("page", {}).get("title", "Product")
    product_name = title.split("|")[0].strip() or "Painting Tool Product"
    lower_name = product_name.lower()
    return {
        "search_intent": "commercial product",
        "primary_keywords": [lower_name, f"{lower_name} wholesale"],
        "secondary_keywords": [
            f"{lower_name} manufacturer",
            f"private label {lower_name}",
            f"OEM {lower_name}",
        ],
        "title_pattern": f"{product_name} | Product Code or Key Specification | SIRUI",
        "description_points": [
            "verified material and size",
            "buyer application",
            "verified customization options",
            "inquiry action",
        ],
    }


def _strategy_for_page(page: dict[str, Any]) -> dict[str, Any]:
    page_type = page.get("page_type", "other")
    if page_type == "product_detail":
        return _product_detail_strategy(page)
    return PAGE_TYPE_STRATEGIES.get(
        page_type,
        {
            "search_intent": "informational",
            "primary_keywords": ["SIRUI painting tools"],
            "secondary_keywords": ["paint brush and paint roller supplier"],
            "title_pattern": "Describe the page topic clearly | SIRUI",
            "description_points": ["page purpose", "buyer value", "next action"],
        },
    )


def _technical_tasks(audit_report: dict[str, Any]) -> list[dict[str, Any]]:
    tasks = []
    for index, issue in enumerate(audit_report.get("prioritized_issues", []), start=1):
        tasks.append(
            {
                "task_id": f"SEO-{index:03d}",
                "priority": issue.get("priority", "P3"),
                "severity": issue.get("severity", "low"),
                "url": issue.get("url", ""),
                "page_type": issue.get("page_type", "other"),
                "issue": issue.get("name", "SEO issue"),
                "evidence": issue.get("evidence", "Needs verification"),
                "recommended_action": issue.get(
                    "recommendation", "Review and define an approved action."
                ),
                "owner": "SEO and development review",
                "status": "open",
            }
        )
    return tasks


def _page_plan(page: dict[str, Any]) -> dict[str, Any]:
    strategy = _strategy_for_page(page)
    page_details = page.get("page", {})
    return {
        "url": page_details.get("final_url", page.get("requested_url", "")),
        "page_type": page.get("page_type", "other"),
        "current_metadata": {
            "title": page_details.get("title", ""),
            "meta_description": page_details.get("meta_description", ""),
            "h1": page_details.get("h1", []),
        },
        "target_markets": DEFAULT_MARKETS,
        "target_audiences": DEFAULT_AUDIENCES,
        "search_intent": strategy["search_intent"],
        "keyword_themes": {
            "primary": strategy["primary_keywords"],
            "secondary": strategy["secondary_keywords"],
            "validation_status": "needs_keyword_research",
            "metrics": {
                "search_volume": "Needs verification",
                "ranking_difficulty": "Needs verification",
                "current_position": "Needs verification",
            },
        },
        "metadata_guidance": {
            "title_pattern": strategy["title_pattern"],
            "meta_description_should_cover": strategy["description_points"],
            "approval_required": True,
        },
    }


def build_seo_plan(audit_report: dict[str, Any]) -> dict[str, Any]:
    """Convert a website audit report into a structured SEO action plan."""

    if not isinstance(audit_report, dict):
        raise ValueError("audit_report must be a dictionary.")
    pages = audit_report.get("pages")
    if not isinstance(pages, list):
        raise ValueError("audit_report must contain a pages list.")

    page_plans = [
        _page_plan(page)
        for page in pages
        if page.get("summary", {}).get("status") != "error"
    ]
    technical_tasks = _technical_tasks(audit_report)
    priority_counts = {
        priority: sum(task["priority"] == priority for task in technical_tasks)
        for priority in ("P1", "P2", "P3")
    }
    return {
        "seo_agent_version": SEO_AGENT_VERSION,
        "source_audit_version": audit_report.get("agent_version", "unknown"),
        "source_url": audit_report.get("requested_url", ""),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": {
            "markets": DEFAULT_MARKETS,
            "audiences": DEFAULT_AUDIENCES,
            "keyword_data_status": "Seed themes only; validate before publishing.",
        },
        "summary": {
            "pages_planned": len(page_plans),
            "technical_tasks": len(technical_tasks),
            "tasks_by_priority": priority_counts,
        },
        "technical_backlog": technical_tasks,
        "page_plans": page_plans,
        "guardrails": [
            "Do not invent search volume, rankings, product facts, certifications, pricing, MOQ, or lead times.",
            "Validate keyword demand with approved data sources before changing production metadata.",
            "Require human approval before publishing any SEO or content change.",
        ],
    }
