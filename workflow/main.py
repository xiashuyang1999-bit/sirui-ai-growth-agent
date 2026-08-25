"""Command-line workflows for the SIRUI website growth agents."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse

from agents.website_audit_agent import audit_site


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


if __name__ == "__main__":
    main()
