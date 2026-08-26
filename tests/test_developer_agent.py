"""Tests for the developer planning agent."""

import unittest

from agents.developer_agent import build_developer_plan


SAMPLE_SEO_PLAN = {
    "seo_agent_version": "0.1",
    "source_url": "https://example.com/",
    "technical_backlog": [
        {
            "task_id": "SEO-001",
            "priority": "P2",
            "url": "https://example.com/product",
            "page_type": "product_detail",
            "issue": "Relevant structured data is present",
            "evidence": "No JSON-LD schema types found.",
            "recommended_action": "Add valid Product JSON-LD for this page type.",
        },
        {
            "task_id": "SEO-002",
            "priority": "P2",
            "url": "https://example.com/inquiry",
            "page_type": "contact",
            "issue": "Canonical URL present",
            "evidence": "No canonical link found.",
            "recommended_action": "Add a self-referencing canonical using the chosen hostname.",
        },
        {
            "task_id": "SEO-003",
            "priority": "P3",
            "url": "https://example.com/",
            "page_type": "site",
            "issue": "Served and canonical hostnames are aligned",
            "evidence": "Canonical host differs from served hostname.",
            "recommended_action": "Use one preferred hostname.",
        },
    ],
}


class DeveloperAgentTests(unittest.TestCase):
    def test_builds_specialized_implementation_tasks(self) -> None:
        plan = build_developer_plan(SAMPLE_SEO_PLAN)

        self.assertEqual(plan["developer_agent_version"], "0.1")
        self.assertEqual(plan["summary"]["implementation_tasks"], 3)
        self.assertEqual(
            plan["summary"]["tasks_by_change_type"],
            {"structured_data": 1, "canonical": 1, "hostname_consolidation": 1},
        )
        self.assertEqual(
            [task["source_task_id"] for task in plan["implementation_tasks"]],
            ["SEO-001", "SEO-002", "SEO-003"],
        )

    def test_every_task_is_approval_gated_and_reversible(self) -> None:
        plan = build_developer_plan(SAMPLE_SEO_PLAN)

        self.assertFalse(plan["release_policy"]["production_changes_allowed"])
        self.assertEqual(plan["summary"]["production_changes_authorized"], 0)
        for task in plan["implementation_tasks"]:
            self.assertFalse(task["approval_gate"]["production_change_allowed"])
            self.assertEqual(
                task["approval_gate"]["release_status"], "proposal_only"
            )
            self.assertTrue(task["acceptance_criteria"])
            self.assertTrue(task["rollback_plan"])

    def test_hostname_change_is_marked_high_risk(self) -> None:
        plan = build_developer_plan(SAMPLE_SEO_PLAN)
        hostname_task = plan["implementation_tasks"][2]

        self.assertEqual(hostname_task["change_type"], "hostname_consolidation")
        self.assertEqual(hostname_task["implementation_risk"], "high")
        self.assertTrue(
            any("Needs verification" in item for item in hostname_task["required_inputs"])
        )

    def test_rejects_plan_without_technical_backlog(self) -> None:
        with self.assertRaisesRegex(ValueError, "technical_backlog list"):
            build_developer_plan({"seo_agent_version": "0.1"})


if __name__ == "__main__":
    unittest.main()
