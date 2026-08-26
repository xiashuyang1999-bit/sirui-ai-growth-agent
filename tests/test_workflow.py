"""Tests for the command-line workflow without making network requests."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from workflow.main import (
    run_audit,
    run_analytics_report,
    run_content_plan,
    run_developer_plan,
    run_followup_plan,
    run_growth_plan,
    run_inquiry_qualification,
    run_pipeline_report,
    run_seo_plan,
)


class AuditWorkflowTests(unittest.TestCase):
    @patch("workflow.main.audit_site")
    def test_run_audit_saves_json_report(self, audit_site) -> None:
        audit_site.return_value = {
            "agent_version": "0.4",
            "summary": {
                "status": "pass",
                "pages_audited": 1,
                "pages_failed": 0,
            },
            "pages": [],
            "errors": [],
        }

        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "audit.json"
            result_path = run_audit(
                "https://example.com", max_pages=1, output=output
            )
            saved_report = json.loads(result_path.read_text(encoding="utf-8"))

        self.assertEqual(saved_report["agent_version"], "0.4")
        self.assertEqual(saved_report["summary"]["status"], "pass")
        audit_site.assert_called_once_with("https://example.com", max_pages=1)

    def test_run_seo_plan_saves_json_plan(self) -> None:
        audit_report = {
            "agent_version": "0.4",
            "requested_url": "https://example.com/",
            "prioritized_issues": [],
            "pages": [
                {
                    "requested_url": "https://example.com/",
                    "page_type": "homepage",
                    "page": {
                        "final_url": "https://example.com/",
                        "title": "Example Manufacturer",
                        "meta_description": "Example description.",
                        "h1": ["Example Manufacturer"],
                    },
                    "summary": {"status": "pass"},
                }
            ],
        }

        with tempfile.TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "audit.json"
            output = Path(temporary_directory) / "seo_plan.json"
            source.write_text(json.dumps(audit_report), encoding="utf-8")

            result_path = run_seo_plan(source, output=output)
            saved_plan = json.loads(result_path.read_text(encoding="utf-8"))

        self.assertEqual(result_path, output)
        self.assertEqual(saved_plan["seo_agent_version"], "0.1")
        self.assertEqual(saved_plan["summary"]["pages_planned"], 1)

    def test_run_developer_plan_saves_json_plan(self) -> None:
        seo_plan = {
            "seo_agent_version": "0.1",
            "source_url": "https://example.com/",
            "technical_backlog": [],
        }

        with tempfile.TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "seo_plan.json"
            output = Path(temporary_directory) / "developer_plan.json"
            source.write_text(json.dumps(seo_plan), encoding="utf-8")

            result_path = run_developer_plan(source, output=output)
            saved_plan = json.loads(result_path.read_text(encoding="utf-8"))

        self.assertEqual(result_path, output)
        self.assertEqual(saved_plan["developer_agent_version"], "0.1")
        self.assertEqual(saved_plan["summary"]["implementation_tasks"], 0)

    def test_run_content_plan_saves_json_plan(self) -> None:
        seo_plan = {
            "seo_agent_version": "0.1",
            "source_url": "https://example.com/",
            "page_plans": [],
        }

        with tempfile.TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "seo_plan.json"
            output = Path(temporary_directory) / "content_plan.json"
            source.write_text(json.dumps(seo_plan), encoding="utf-8")

            result_path = run_content_plan(source, output=output)
            saved_plan = json.loads(result_path.read_text(encoding="utf-8"))

        self.assertEqual(result_path, output)
        self.assertEqual(saved_plan["content_agent_version"], "0.1")
        self.assertEqual(saved_plan["summary"]["content_briefs"], 0)

    def test_run_growth_plan_builds_complete_offline_package(self) -> None:
        audit_report = {
            "agent_version": "0.4",
            "requested_url": "https://example.com/",
            "summary": {
                "pages_audited": 1,
                "issue_count": 1,
            },
            "prioritized_issues": [
                {
                    "url": "https://example.com/",
                    "page_type": "homepage",
                    "name": "Relevant structured data is present",
                    "evidence": "No JSON-LD schema types found.",
                    "severity": "medium",
                    "priority": "P2",
                    "recommendation": "Add Organization JSON-LD.",
                }
            ],
            "pages": [
                {
                    "requested_url": "https://example.com/",
                    "page_type": "homepage",
                    "page": {
                        "final_url": "https://example.com/",
                        "title": "Example Manufacturer",
                        "meta_description": "Example description.",
                        "h1": ["Example Manufacturer"],
                    },
                    "summary": {"status": "needs_review"},
                }
            ],
        }

        with tempfile.TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "audit.json"
            package_dir = Path(temporary_directory) / "growth_package"
            source.write_text(json.dumps(audit_report), encoding="utf-8")

            manifest_path = run_growth_plan(source, output_dir=package_dir)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            artifact_names = set(manifest["artifacts"].values())
            saved_names = {path.name for path in package_dir.glob("*.json")}

        self.assertEqual(manifest["growth_workflow_version"], "0.1")
        self.assertEqual(manifest["summary"]["seo_tasks"], 1)
        self.assertEqual(manifest["summary"]["developer_tasks"], 1)
        self.assertEqual(manifest["summary"]["content_briefs"], 1)
        self.assertFalse(manifest["approval_state"]["production_change_allowed"])
        self.assertEqual(len(manifest["measurement_framework"]), 7)
        self.assertEqual(
            saved_names, artifact_names | {"manifest.json"}
        )

    def test_run_inquiry_qualification_saves_private_review(self) -> None:
        inquiry = {
            "contact_name": "Alex",
            "company": "Example Buyer",
            "product": "paint roller covers",
        }

        with tempfile.TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "inquiry.json"
            output = Path(temporary_directory) / "qualification.json"
            source.write_text(json.dumps(inquiry), encoding="utf-8")

            result_path = run_inquiry_qualification(source, output=output)
            saved_result = json.loads(result_path.read_text(encoding="utf-8"))

        self.assertEqual(result_path, output)
        self.assertEqual(saved_result["inquiry_agent_version"], "0.1")
        self.assertFalse(saved_result["reply_draft"]["sent"])
        self.assertFalse(
            saved_result["approval_gate"]["external_message_allowed"]
        )

    def test_run_pipeline_report_saves_private_report(self) -> None:
        pipeline = {
            "period": {"start": "2026-08-18", "end": "2026-08-24"},
            "records": [],
        }

        with tempfile.TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "pipeline.json"
            output = Path(temporary_directory) / "pipeline_report.json"
            source.write_text(json.dumps(pipeline), encoding="utf-8")

            result_path = run_pipeline_report(source, output=output)
            saved_report = json.loads(result_path.read_text(encoding="utf-8"))

        self.assertEqual(result_path, output)
        self.assertEqual(saved_report["pipeline_agent_version"], "0.1")
        self.assertEqual(saved_report["summary"]["new_leads_or_inquiries"], 0)
        self.assertFalse(saved_report["approval_gate"]["crm_write_allowed"])

    def test_run_followup_plan_saves_private_unsent_plan(self) -> None:
        lead = {
            "record_id": "LEAD-001",
            "grade": "A",
            "start_date": "2026-08-26",
            "product": "paint roller covers",
        }

        with tempfile.TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "lead.json"
            output = Path(temporary_directory) / "followup.json"
            source.write_text(json.dumps(lead), encoding="utf-8")

            result_path = run_followup_plan(source, output=output)
            saved_plan = json.loads(result_path.read_text(encoding="utf-8"))

        self.assertEqual(result_path, output)
        self.assertEqual(saved_plan["followup_agent_version"], "0.1")
        self.assertEqual(saved_plan["summary"]["messages_drafted"], 5)
        self.assertEqual(saved_plan["summary"]["messages_sent"], 0)
        self.assertFalse(saved_plan["approval_gate"]["external_message_allowed"])

    def test_run_analytics_report_saves_private_report(self) -> None:
        metrics = {
            "period": {"start": "2026-08-01", "end": "2026-08-31"},
            "website": {"sessions": 100, "inquiry_submissions": 5},
            "search": {"clicks": 10, "impressions": 500},
            "sales": {
                "attribution_scope": "website_only",
                "qualified_inquiries": 2,
                "quotations": 1,
                "orders": 0,
            },
        }

        with tempfile.TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "metrics.json"
            output = Path(temporary_directory) / "analytics_report.json"
            source.write_text(json.dumps(metrics), encoding="utf-8")

            result_path = run_analytics_report(source, output=output)
            saved_report = json.loads(result_path.read_text(encoding="utf-8"))

        self.assertEqual(result_path, output)
        self.assertEqual(saved_report["analytics_agent_version"], "0.1")
        self.assertEqual(saved_report["rates_percent"]["website_inquiry_rate"], 5.0)
        self.assertFalse(saved_report["approval_gate"]["analytics_write_allowed"])


if __name__ == "__main__":
    unittest.main()
