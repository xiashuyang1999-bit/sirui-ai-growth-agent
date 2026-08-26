"""Developer planning agent for approval-gated website changes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

DEVELOPER_AGENT_VERSION = "0.1"


def _schema_task(task: dict[str, Any]) -> dict[str, Any]:
    recommendation = task.get("recommended_action", "")
    return {
        "change_type": "structured_data",
        "implementation_risk": "medium",
        "implementation_scope": "Relevant page or page-type template head markup.",
        "implementation_steps": [
            "Identify the CMS, framework, template owner, and current JSON-LD rendering path.",
            f"Use the schema type named in the approved recommendation: {recommendation}",
            "Populate only fields supported by verified page content or approved business data.",
            "Render valid JSON-LD in the server response or approved page template.",
            "Deploy to a staging or preview environment before production approval.",
        ],
        "required_inputs": [
            "CMS or framework and template location: Needs verification",
            "Approved business or product fields for schema: Needs verification",
            "Preferred canonical page URL: Needs verification",
        ],
        "acceptance_criteria": [
            "The affected URL returns HTTP 200 in the staging or preview environment.",
            "Every JSON-LD block parses as valid JSON.",
            "The audit detects the schema type required for this page type.",
            "Schema values agree with visible, verified page content.",
            "No page layout, navigation, inquiry, or JavaScript regression is introduced.",
        ],
        "rollback_plan": "Revert the template change and remove the new JSON-LD block, then rerun the page audit.",
    }


def _canonical_task(task: dict[str, Any]) -> dict[str, Any]:
    return {
        "change_type": "canonical",
        "implementation_risk": "medium",
        "implementation_scope": "Head markup for the affected page or its template.",
        "implementation_steps": [
            "Confirm the preferred production hostname and language URL convention.",
            "Add exactly one absolute HTTPS canonical URL for the affected page.",
            "Ensure the canonical target is indexable and returns HTTP 200.",
            "Deploy to a staging or preview environment and inspect the rendered HTML.",
            "Request SEO approval before production release.",
        ],
        "required_inputs": [
            "Chosen preferred hostname: Needs verification",
            "Approved language and query-string convention: Needs verification",
            "CMS or template location: Needs verification",
        ],
        "acceptance_criteria": [
            "The rendered page contains exactly one canonical link.",
            "The canonical is an absolute HTTPS URL using the approved hostname.",
            "The canonical target returns HTTP 200 and is not blocked by robots.txt.",
            "The Website Audit Agent canonical check passes after deployment.",
            "The inquiry form and all conversion routes continue to work.",
        ],
        "rollback_plan": "Revert the canonical template or page-field change and restore the previously approved head markup.",
    }


def _hostname_task(task: dict[str, Any]) -> dict[str, Any]:
    return {
        "change_type": "hostname_consolidation",
        "implementation_risk": "high",
        "implementation_scope": "CDN or web-server redirects, canonicals, internal links, and XML sitemap URLs.",
        "implementation_steps": [
            "Choose either the www or non-www hostname as the single production standard.",
            "Inventory redirects, internal links, canonicals, sitemap URLs, analytics settings, and Search Console properties.",
            "Configure permanent 301 or 308 redirects from the non-preferred hostname while preserving path and query data.",
            "Update canonicals, internal links, and XML sitemap entries to the preferred hostname.",
            "Test on staging where possible, then schedule a monitored production release after approval.",
        ],
        "required_inputs": [
            "Approved preferred hostname: Needs verification",
            "CDN, DNS, reverse-proxy, or web-server owner: Needs verification",
            "Analytics and Google Search Console ownership: Needs verification",
            "Rollback contact and maintenance window: Needs verification",
        ],
        "acceptance_criteria": [
            "Every tested non-preferred URL redirects once to the matching preferred URL.",
            "Redirects preserve paths and required query parameters without loops or chains.",
            "All audited canonicals, internal links, and sitemap URLs use the preferred hostname.",
            "Key pages return HTTP 200 after the redirect and pass the Website Audit Agent checks.",
            "Analytics, inquiry forms, and conversion tracking continue to operate.",
        ],
        "rollback_plan": "Restore the previous redirect configuration and URL settings from the approved backup, then verify every key page and inquiry path.",
    }


def _generic_task(task: dict[str, Any]) -> dict[str, Any]:
    return {
        "change_type": "technical_review",
        "implementation_risk": "Needs verification",
        "implementation_scope": "Affected URL and owning template or configuration.",
        "implementation_steps": [
            "Confirm the issue evidence against the current staging or production response.",
            f"Translate the approved recommendation into a platform-specific change: {task.get('recommended_action', 'Needs verification')}",
            "Document the files, templates, or settings that will change.",
            "Implement and test in a staging or preview environment.",
            "Request approval before production release.",
        ],
        "required_inputs": [
            "CMS or framework: Needs verification",
            "Owning template or configuration: Needs verification",
            "Expected business behavior: Needs verification",
        ],
        "acceptance_criteria": [
            "The original audit evidence is no longer present.",
            "The relevant Website Audit Agent check passes.",
            "No navigation, content, inquiry, analytics, or layout regression is introduced.",
        ],
        "rollback_plan": "Revert the scoped change using the approved source-control or configuration backup, then rerun the relevant checks.",
    }


def _implementation_details(task: dict[str, Any]) -> dict[str, Any]:
    issue = str(task.get("issue", "")).lower()
    evidence = str(task.get("evidence", "")).lower()
    issue_text = " ".join(
        str(task.get(field, ""))
        for field in ("issue", "evidence", "recommended_action")
    ).lower()
    if "hostnames are aligned" in issue or "hostname consistency" in issue:
        return _hostname_task(task)
    if "canonical url" in issue or "no canonical link" in evidence:
        return _canonical_task(task)
    if "schema" in issue_text or "json-ld" in issue_text or "structured data" in issue_text:
        return _schema_task(task)
    if "hostname" in issue_text or "hostnames" in issue_text:
        return _hostname_task(task)
    return _generic_task(task)


def _build_task(task: dict[str, Any], index: int) -> dict[str, Any]:
    details = _implementation_details(task)
    return {
        "dev_task_id": f"DEV-{index:03d}",
        "source_task_id": task.get("task_id", "Needs verification"),
        "priority": task.get("priority", "P3"),
        "url": task.get("url", ""),
        "page_type": task.get("page_type", "other"),
        "issue": task.get("issue", "Technical SEO issue"),
        "evidence": task.get("evidence", "Needs verification"),
        "recommended_action": task.get(
            "recommended_action", "Needs verification"
        ),
        **details,
        "environment_sequence": ["local", "staging_or_preview", "production"],
        "approval_gate": {
            "production_change_allowed": False,
            "required_approvers": [
                "website owner",
                "SEO reviewer",
                "technical owner",
            ],
            "release_status": "proposal_only",
        },
    }


def build_developer_plan(seo_plan: dict[str, Any]) -> dict[str, Any]:
    """Convert an SEO plan into an approval-gated implementation package."""

    if not isinstance(seo_plan, dict):
        raise ValueError("seo_plan must be a dictionary.")
    backlog = seo_plan.get("technical_backlog")
    if not isinstance(backlog, list):
        raise ValueError("seo_plan must contain a technical_backlog list.")

    tasks = [_build_task(task, index) for index, task in enumerate(backlog, start=1)]
    change_type_counts: dict[str, int] = {}
    risk_counts: dict[str, int] = {}
    for task in tasks:
        change_type = task["change_type"]
        risk = task["implementation_risk"]
        change_type_counts[change_type] = change_type_counts.get(change_type, 0) + 1
        risk_counts[risk] = risk_counts.get(risk, 0) + 1

    return {
        "developer_agent_version": DEVELOPER_AGENT_VERSION,
        "source_seo_agent_version": seo_plan.get("seo_agent_version", "unknown"),
        "source_url": seo_plan.get("source_url", ""),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "implementation_tasks": len(tasks),
            "tasks_by_change_type": change_type_counts,
            "tasks_by_risk": risk_counts,
            "production_changes_authorized": 0,
        },
        "release_policy": {
            "default_environment": "staging_or_preview",
            "production_changes_allowed": False,
            "human_approval_required": True,
            "platform_status": "Needs verification",
        },
        "implementation_tasks": tasks,
        "global_definition_of_done": [
            "Required inputs and factual values are verified by their owners.",
            "The change is reviewed in staging or an equivalent preview environment.",
            "Relevant automated tests and Website Audit Agent checks pass.",
            "Critical inquiry, analytics, navigation, and mobile paths are manually checked.",
            "A named approver authorizes the production release and rollback owner.",
        ],
    }
