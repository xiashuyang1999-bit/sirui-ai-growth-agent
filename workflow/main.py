"""Command-line workflows for the SIRUI website growth agents."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from agents.analytics_agent import build_analytics_report
from agents.content_agent import build_content_plan
from agents.developer_agent import build_developer_plan
from agents.followup_agent import build_followup_plan
from agents.inquiry_agent import qualify_inquiry
from agents.pipeline_agent import build_pipeline_report
from agents.seo_agent import build_seo_plan
from agents.website_audit_agent import audit_site

GROWTH_WORKFLOW_VERSION = "0.1"


def _default_report_path(url: str) -> Path:
    host = urlparse(url).hostname or "website"
    safe_host = re.sub(r"[^a-zA-Z0-9]+", "_", host).strip("_")
    return Path("reports") / f"{safe_host}_audit.json"


def run_audit(url: str, max_pages: int = 8, output: Path | None = None) -> Path:
    """Run a site audit and save its JSON report."""

    report_path = output or _default_report_path(url)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = audit_site(url, max_pages=max_pages)
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report_path


def run_seo_plan(audit_report: Path, output: Path | None = None) -> Path:
    """Build and save an SEO plan from a structured website audit report."""

    source_report = json.loads(audit_report.read_text(encoding="utf-8"))
    plan = build_seo_plan(source_report)
    plan_path = output or audit_report.with_name(f"{audit_report.stem}_seo_plan.json")
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return plan_path


def run_developer_plan(seo_plan: Path, output: Path | None = None) -> Path:
    """Build and save a developer plan from a structured SEO plan."""

    source_plan = json.loads(seo_plan.read_text(encoding="utf-8"))
    developer_plan = build_developer_plan(source_plan)
    plan_path = output or seo_plan.with_name(f"{seo_plan.stem}_developer_plan.json")
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        json.dumps(developer_plan, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return plan_path


def run_content_plan(seo_plan: Path, output: Path | None = None) -> Path:
    """Build and save content briefs from a structured SEO plan."""

    source_plan = json.loads(seo_plan.read_text(encoding="utf-8"))
    content_plan = build_content_plan(source_plan)
    plan_path = output or seo_plan.with_name(f"{seo_plan.stem}_content_plan.json")
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        json.dumps(content_plan, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return plan_path


def _write_json(path: Path, data: dict) -> None:
    """Write structured output with consistent formatting."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def _measurement_framework() -> list[dict[str, str]]:
    """Return metric definitions without inventing current values."""

    return [
        {
            "metric": "website_sessions",
            "definition": "Visits to the website, segmented by source, market, landing page, and device.",
            "recommended_source": "GA4 or approved web analytics",
            "owner": "marketing",
            "integration_status": "Needs verification",
            "current_value": "Needs verification",
        },
        {
            "metric": "organic_search_clicks",
            "definition": "Clicks from unpaid search results, segmented by query, page, country, and device.",
            "recommended_source": "Google Search Console",
            "owner": "SEO",
            "integration_status": "Needs verification",
            "current_value": "Needs verification",
        },
        {
            "metric": "inquiry_submissions",
            "definition": "Successfully received website inquiry forms or approved direct-contact conversions.",
            "recommended_source": "Form backend plus analytics conversion event",
            "owner": "website and sales operations",
            "integration_status": "Needs verification",
            "current_value": "Needs verification",
        },
        {
            "metric": "qualified_inquiries",
            "definition": "Verified B2B inquiries with credible company identity and a relevant product or sourcing requirement.",
            "recommended_source": "Approved CRM or controlled sales tracker",
            "owner": "sales",
            "integration_status": "Needs verification",
            "current_value": "Needs verification",
        },
        {
            "metric": "sample_projects",
            "definition": "Qualified opportunities that progress to an approved sample discussion or shipment.",
            "recommended_source": "Approved CRM or controlled sales tracker",
            "owner": "sales",
            "integration_status": "Needs verification",
            "current_value": "Needs verification",
        },
        {
            "metric": "quotations",
            "definition": "Formal quotations issued after product, quantity, customization, packaging, and destination review.",
            "recommended_source": "Approved CRM or quotation register",
            "owner": "sales",
            "integration_status": "Needs verification",
            "current_value": "Needs verification",
        },
        {
            "metric": "orders",
            "definition": "Confirmed B2B orders linked to a traceable source and opportunity record.",
            "recommended_source": "Approved CRM and order system",
            "owner": "sales and operations",
            "integration_status": "Needs verification",
            "current_value": "Needs verification",
        },
    ]


def run_growth_plan(audit_report: Path, output_dir: Path | None = None) -> Path:
    """Build a complete local growth package from an existing audit report."""

    source_report = json.loads(audit_report.read_text(encoding="utf-8"))
    seo_plan = build_seo_plan(source_report)
    developer_plan = build_developer_plan(seo_plan)
    content_plan = build_content_plan(seo_plan)

    package_dir = output_dir or audit_report.with_name(
        f"{audit_report.stem}_growth_package"
    )
    seo_path = package_dir / "seo_plan.json"
    developer_path = package_dir / "developer_plan.json"
    content_path = package_dir / "content_plan.json"
    manifest_path = package_dir / "manifest.json"

    _write_json(seo_path, seo_plan)
    _write_json(developer_path, developer_plan)
    _write_json(content_path, content_plan)

    audit_summary = source_report.get("summary", {})
    manifest = {
        "growth_workflow_version": GROWTH_WORKFLOW_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "audit_report": str(audit_report),
            "audit_agent_version": source_report.get("agent_version", "unknown"),
            "website": source_report.get("requested_url", ""),
        },
        "artifacts": {
            "seo_plan": seo_path.name,
            "developer_plan": developer_path.name,
            "content_plan": content_path.name,
        },
        "summary": {
            "pages_audited": audit_summary.get("pages_audited", 0),
            "audit_issues": audit_summary.get("issue_count", 0),
            "seo_tasks": seo_plan["summary"]["technical_tasks"],
            "developer_tasks": developer_plan["summary"]["implementation_tasks"],
            "content_briefs": content_plan["summary"]["content_briefs"],
            "production_changes_authorized": 0,
            "production_pages_authorized": 0,
        },
        "measurement_framework": _measurement_framework(),
        "approval_state": {
            "analysis_and_planning_complete": True,
            "production_change_allowed": False,
            "content_publication_allowed": False,
            "external_messages_allowed": False,
            "human_approval_required": True,
        },
        "next_actions": [
            "Assign and verify every Needs verification input to a named owner.",
            "Review developer tasks and test approved changes in staging or preview.",
            "Review keyword demand and complete factual inputs before drafting page copy.",
            "Connect approved analytics, Search Console, form, and sales pipeline sources.",
            "Rerun the audit after approved production changes and compare results.",
        ],
    }
    _write_json(manifest_path, manifest)
    return manifest_path


def run_inquiry_qualification(
    inquiry_path: Path, output: Path | None = None
) -> Path:
    """Qualify one local inquiry and save a private review package."""

    inquiry = json.loads(inquiry_path.read_text(encoding="utf-8"))
    qualification = qualify_inquiry(inquiry)
    output_path = output or Path("reports/inquiries") / (
        f"{inquiry_path.stem}_qualification.json"
    )
    _write_json(output_path, qualification)
    return output_path


def run_pipeline_report(
    pipeline_path: Path, output: Path | None = None
) -> Path:
    """Build a private sales pipeline report from local records."""

    pipeline_data = json.loads(pipeline_path.read_text(encoding="utf-8"))
    report = build_pipeline_report(pipeline_data)
    output_path = output or Path("reports/pipeline") / (
        f"{pipeline_path.stem}_report.json"
    )
    _write_json(output_path, report)
    return output_path


def run_followup_plan(
    lead_path: Path, output: Path | None = None
) -> Path:
    """Build a private, unsent follow-up plan for one local record."""

    lead = json.loads(lead_path.read_text(encoding="utf-8"))
    plan = build_followup_plan(lead)
    output_path = output or Path("reports/followups") / (
        f"{lead_path.stem}_followup_plan.json"
    )
    _write_json(output_path, plan)
    return output_path


def run_analytics_report(
    metrics_path: Path, output: Path | None = None
) -> Path:
    """Build a private analytics report from approved local metrics."""

    metrics_data = json.loads(metrics_path.read_text(encoding="utf-8"))
    report = build_analytics_report(metrics_data)
    output_path = output or Path("reports/analytics") / (
        f"{metrics_path.stem}_report.json"
    )
    _write_json(output_path, report)
    return output_path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run SIRUI website growth workflows.")
    commands = parser.add_subparsers(dest="command", required=True)

    audit_parser = commands.add_parser("audit", help="Run a read-only site audit.")
    audit_parser.add_argument("url", help="Absolute http:// or https:// website URL.")
    audit_parser.add_argument(
        "--max-pages",
        type=int,
        default=8,
        help="Maximum same-domain pages to inspect (default: 8, maximum: 25).",
    )
    audit_parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON output path; defaults to reports/<domain>_audit.json.",
    )

    seo_parser = commands.add_parser(
        "seo-plan", help="Build an SEO plan from a website audit JSON report."
    )
    seo_parser.add_argument(
        "audit_report", type=Path, help="Path to a website audit JSON report."
    )
    seo_parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON output path; defaults beside the source audit report.",
    )

    developer_parser = commands.add_parser(
        "dev-plan", help="Build a developer implementation plan from an SEO plan."
    )
    developer_parser.add_argument(
        "seo_plan", type=Path, help="Path to a structured SEO plan JSON file."
    )
    developer_parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON output path; defaults beside the source SEO plan.",
    )

    content_parser = commands.add_parser(
        "content-plan", help="Build page-level content briefs from an SEO plan."
    )
    content_parser.add_argument(
        "seo_plan", type=Path, help="Path to a structured SEO plan JSON file."
    )
    content_parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON output path; defaults beside the source SEO plan.",
    )

    growth_parser = commands.add_parser(
        "growth-plan",
        help="Build SEO, developer, content, and measurement plans from an audit.",
    )
    growth_parser.add_argument(
        "audit_report", type=Path, help="Path to a website audit JSON report."
    )
    growth_parser.add_argument(
        "--output-dir",
        type=Path,
        help="Optional package directory; defaults beside the audit report.",
    )

    inquiry_parser = commands.add_parser(
        "qualify-inquiry",
        help="Qualify one local B2B inquiry and prepare a reply draft.",
    )
    inquiry_parser.add_argument(
        "inquiry", type=Path, help="Path to a local inquiry JSON file."
    )
    inquiry_parser.add_argument(
        "--output",
        type=Path,
        help="Optional private output path; defaults under reports/inquiries/.",
    )

    pipeline_parser = commands.add_parser(
        "pipeline-report",
        help="Build a private sales pipeline report from local JSON records.",
    )
    pipeline_parser.add_argument(
        "pipeline", type=Path, help="Path to a local pipeline JSON file."
    )
    pipeline_parser.add_argument(
        "--output",
        type=Path,
        help="Optional private output path; defaults under reports/pipeline/.",
    )

    followup_parser = commands.add_parser(
        "followup-plan",
        help="Build an unsent Day 3/7/14/21/final follow-up sequence.",
    )
    followup_parser.add_argument(
        "lead", type=Path, help="Path to a local lead or inquiry JSON file."
    )
    followup_parser.add_argument(
        "--output",
        type=Path,
        help="Optional private output path; defaults under reports/followups/.",
    )

    analytics_parser = commands.add_parser(
        "analytics-report",
        help="Build a private conversion report from approved local metrics.",
    )
    analytics_parser.add_argument(
        "metrics", type=Path, help="Path to a normalized local metrics JSON file."
    )
    analytics_parser.add_argument(
        "--output",
        type=Path,
        help="Optional private output path; defaults under reports/analytics/.",
    )
    return parser


def main() -> None:
    """Parse command-line arguments and execute the selected workflow."""

    args = _build_parser().parse_args()
    if args.command == "audit":
        report_path = run_audit(args.url, max_pages=args.max_pages, output=args.output)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        summary = report["summary"]
        print(f"Audit status: {summary['status']}")
        print(
            f"Pages audited: {summary['pages_audited']}; "
            f"pages failed: {summary['pages_failed']}"
        )
        print(
            f"Issues: {summary.get('issue_count', 0)} "
            f"(P1/high: {summary.get('issues_by_severity', {}).get('high', 0)}, "
            f"P2/medium: {summary.get('issues_by_severity', {}).get('medium', 0)}, "
            f"P3/low: {summary.get('issues_by_severity', {}).get('low', 0)})"
        )
        print(f"Report saved to: {report_path.resolve()}")
    elif args.command == "seo-plan":
        plan_path = run_seo_plan(args.audit_report, output=args.output)
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        summary = plan["summary"]
        print(f"Pages planned: {summary['pages_planned']}")
        print(
            f"SEO tasks: {summary['technical_tasks']} "
            f"(P1: {summary['tasks_by_priority']['P1']}, "
            f"P2: {summary['tasks_by_priority']['P2']}, "
            f"P3: {summary['tasks_by_priority']['P3']})"
        )
        print(f"SEO plan saved to: {plan_path.resolve()}")
    elif args.command == "dev-plan":
        plan_path = run_developer_plan(args.seo_plan, output=args.output)
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        summary = plan["summary"]
        print(f"Implementation tasks: {summary['implementation_tasks']}")
        print(
            "Production changes authorized: "
            f"{summary['production_changes_authorized']}"
        )
        print(f"Developer plan saved to: {plan_path.resolve()}")
    elif args.command == "content-plan":
        plan_path = run_content_plan(args.seo_plan, output=args.output)
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        summary = plan["summary"]
        print(f"Content briefs: {summary['content_briefs']}")
        print(
            "Production pages authorized: "
            f"{summary['production_pages_authorized']}"
        )
        print(f"Content plan saved to: {plan_path.resolve()}")
    elif args.command == "growth-plan":
        manifest_path = run_growth_plan(
            args.audit_report, output_dir=args.output_dir
        )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        summary = manifest["summary"]
        print(f"Pages audited: {summary['pages_audited']}")
        print(
            f"SEO tasks: {summary['seo_tasks']}; "
            f"developer tasks: {summary['developer_tasks']}; "
            f"content briefs: {summary['content_briefs']}"
        )
        print("Production changes authorized: 0")
        print(f"Growth package saved to: {manifest_path.parent.resolve()}")
    elif args.command == "qualify-inquiry":
        output_path = run_inquiry_qualification(args.inquiry, output=args.output)
        qualification = json.loads(output_path.read_text(encoding="utf-8"))
        result = qualification["qualification"]
        print(
            f"Inquiry grade: {result['grade']} "
            f"(score: {result['score']}; status: {result['status']})"
        )
        print("External message sent: no")
        print(f"Private review saved to: {output_path.resolve()}")
    elif args.command == "pipeline-report":
        output_path = run_pipeline_report(args.pipeline, output=args.output)
        report = json.loads(output_path.read_text(encoding="utf-8"))
        summary = report["summary"]
        grades = summary["grade_counts"]
        print(
            f"New leads or inquiries: {summary['new_leads_or_inquiries']} "
            f"(A: {grades['A']}, B: {grades['B']}, C: {grades['C']})"
        )
        print(
            f"Samples: {summary['samples']}; quotations: "
            f"{summary['quotations']}; orders: {summary['orders']}"
        )
        print("External records changed: no")
        print(f"Private pipeline report saved to: {output_path.resolve()}")
    elif args.command == "followup-plan":
        output_path = run_followup_plan(args.lead, output=args.output)
        plan = json.loads(output_path.read_text(encoding="utf-8"))
        summary = plan["summary"]
        print(
            f"Follow-up status: {plan['sequence_status']}; "
            f"drafts: {summary['messages_drafted']}"
        )
        print("External messages sent: 0")
        print(f"Private follow-up plan saved to: {output_path.resolve()}")
    elif args.command == "analytics-report":
        output_path = run_analytics_report(args.metrics, output=args.output)
        report = json.loads(output_path.read_text(encoding="utf-8"))
        metrics = report["metrics"]
        print(
            f"Sessions: {metrics['sessions']}; inquiries: "
            f"{metrics['inquiry_submissions']}; orders: {metrics['orders']}"
        )
        print(f"Validation status: {report['validation']['status']}")
        print("External accounts accessed: no")
        print(f"Private analytics report saved to: {output_path.resolve()}")


if __name__ == "__main__":
    main()
