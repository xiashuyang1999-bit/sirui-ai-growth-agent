"""Tests for the sales pipeline reporting agent."""

import unittest

from agents.pipeline_agent import build_pipeline_report


SAMPLE_PIPELINE = {
    "period": {"start": "2026-08-18", "end": "2026-08-24"},
    "records": [
        {
            "record_id": "INQ-001",
            "qualification": {"grade": "A", "score": 88},
            "stage": "quotation",
            "country": "United Kingdom",
            "segment": "distributor",
            "next_action": "Confirm packaging inputs.",
            "blocker": "Packaging artwork not supplied.",
            "owner": "sales",
            "milestones": {
                "reply_received": True,
                "sample_started": True,
                "quotation_issued": False,
                "order_confirmed": False,
            },
        },
        {
            "record_id": "LEAD-002",
            "grade": "B",
            "score": 60,
            "stage": "clarification",
            "country": "United States",
            "segment": "importer",
            "next_action": "Verify the company and quantity.",
            "milestones": {
                "outreach_drafted": True,
                "outreach_sent": True,
            },
        },
        {
            "record_id": "INQ-003",
            "grade": "C",
            "score": 20,
            "stage": "new",
            "milestones": {},
        },
    ],
}


class PipelineAgentTests(unittest.TestCase):
    def test_summarizes_grades_stages_and_priority_queue(self) -> None:
        report = build_pipeline_report(SAMPLE_PIPELINE)

        self.assertEqual(report["pipeline_agent_version"], "0.1")
        self.assertEqual(report["summary"]["new_leads_or_inquiries"], 3)
        self.assertEqual(
            report["summary"]["grade_counts"],
            {"A": 1, "B": 1, "C": 1, "Needs verification": 0},
        )
        self.assertEqual(report["stage_counts"]["quotation"], 1)
        self.assertEqual(
            [item["record_id"] for item in report["priority_queue"]],
            ["INQ-001", "LEAD-002"],
        )

    def test_counts_only_explicit_milestones(self) -> None:
        report = build_pipeline_report(SAMPLE_PIPELINE)

        self.assertEqual(report["summary"]["samples"], 1)
        self.assertEqual(report["summary"]["quotations"], 0)
        self.assertEqual(report["summary"]["orders"], 0)
        self.assertEqual(report["summary"]["outreach_sent"], 1)
        self.assertEqual(
            report["data_quality"]["milestone_rule"],
            "Counts include only fields explicitly set to true.",
        )

    def test_reports_blockers_without_changing_records(self) -> None:
        report = build_pipeline_report(SAMPLE_PIPELINE)

        self.assertEqual(report["summary"]["active_blockers"], 1)
        self.assertEqual(report["blockers"][0]["record_id"], "INQ-001")
        self.assertFalse(report["approval_gate"]["crm_write_allowed"])
        self.assertFalse(report["approval_gate"]["record_updates_allowed"])

    def test_empty_period_values_are_marked_for_verification(self) -> None:
        report = build_pipeline_report({"period": {"start": "", "end": ""}, "records": []})

        self.assertEqual(report["period"]["start"], "Needs verification")
        self.assertEqual(report["period"]["end"], "Needs verification")

    def test_rejects_invalid_records(self) -> None:
        with self.assertRaisesRegex(ValueError, "records list"):
            build_pipeline_report({"records": ["not-a-record"]})


if __name__ == "__main__":
    unittest.main()
