"""Tests for the SEO planning agent."""

import unittest

from agents.seo_agent import build_seo_plan


SAMPLE_AUDIT = {
    "agent_version": "0.4",
    "requested_url": "https://example.com/",
    "prioritized_issues": [
        {
            "url": "https://example.com/",
            "page_type": "homepage",
            "name": "Relevant structured data is present",
            "evidence": "No JSON-LD schema types found.",
            "severity": "medium",
            "priority": "P2",
            "recommendation": "Add valid Organization or WebSite JSON-LD.",
        }
    ],
    "pages": [
        {
            "requested_url": "https://example.com/",
            "page_type": "homepage",
            "page": {
                "final_url": "https://example.com/",
                "title": "Paint Brush & Paint Roller Manufacturer | Example",
                "meta_description": "Painting tools for overseas B2B buyers.",
                "h1": ["Paint Brush & Paint Roller Manufacturer"],
            },
            "summary": {"status": "needs_review"},
        },
        {
            "requested_url": "https://example.com/products/angled-brush",
            "page_type": "product_detail",
            "page": {
                "final_url": "https://example.com/products/angled-brush",
                "title": "50mm Angled Sash Paint Brush | PB-ANGLE-050",
                "meta_description": "A private-label angled paint brush.",
                "h1": ["50mm Angled Sash Paint Brush"],
            },
            "summary": {"status": "pass"},
        },
    ],
}


class SeoAgentTests(unittest.TestCase):
    def test_builds_page_plans_and_preserves_issue_evidence(self) -> None:
        plan = build_seo_plan(SAMPLE_AUDIT)

        self.assertEqual(plan["seo_agent_version"], "0.1")
        self.assertEqual(plan["source_audit_version"], "0.4")
        self.assertEqual(plan["summary"]["pages_planned"], 2)
        self.assertEqual(plan["summary"]["technical_tasks"], 1)
        self.assertEqual(plan["summary"]["tasks_by_priority"]["P2"], 1)
        task = plan["technical_backlog"][0]
        self.assertEqual(task["priority"], "P2")
        self.assertEqual(task["evidence"], "No JSON-LD schema types found.")

    def test_keyword_metrics_are_never_invented(self) -> None:
        plan = build_seo_plan(SAMPLE_AUDIT)

        for page_plan in plan["page_plans"]:
            keyword_themes = page_plan["keyword_themes"]
            self.assertEqual(
                keyword_themes["validation_status"], "needs_keyword_research"
            )
            self.assertEqual(
                set(keyword_themes["metrics"].values()), {"Needs verification"}
            )

    def test_product_keywords_are_derived_from_page_title(self) -> None:
        plan = build_seo_plan(SAMPLE_AUDIT)
        product_plan = plan["page_plans"][1]

        self.assertEqual(product_plan["page_type"], "product_detail")
        self.assertIn(
            "50mm angled sash paint brush",
            product_plan["keyword_themes"]["primary"],
        )
        self.assertTrue(product_plan["metadata_guidance"]["approval_required"])

    def test_rejects_report_without_pages(self) -> None:
        with self.assertRaisesRegex(ValueError, "pages list"):
            build_seo_plan({"agent_version": "0.4"})


if __name__ == "__main__":
    unittest.main()
