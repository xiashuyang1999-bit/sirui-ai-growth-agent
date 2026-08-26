"""Tests for the content planning agent."""

import unittest

from agents.content_agent import build_content_plan


SAMPLE_SEO_PLAN = {
    "seo_agent_version": "0.1",
    "source_url": "https://example.com/",
    "page_plans": [
        {
            "url": "https://example.com/",
            "page_type": "homepage",
            "current_metadata": {
                "title": "Paint Roller Manufacturer in China | Example",
                "meta_description": "Example description.",
                "h1": ["Paint Roller Manufacturer in China"],
            },
            "target_markets": ["United States"],
            "target_audiences": ["importers", "distributors"],
            "search_intent": "commercial investigation",
            "keyword_themes": {
                "primary": ["paint roller manufacturer in china"],
                "secondary": ["private label paint rollers"],
                "validation_status": "needs_keyword_research",
            },
            "metadata_guidance": {
                "title_pattern": "Paint Roller Manufacturer in China | Example",
                "meta_description_should_cover": ["manufacturer positioning"],
            },
        },
        {
            "url": "https://example.com/products/roller-cover",
            "page_type": "product_detail",
            "current_metadata": {
                "title": "Paint Roller Cover | Example",
                "meta_description": "Example product description.",
                "h1": ["Paint Roller Cover"],
            },
            "target_markets": ["United Kingdom"],
            "target_audiences": ["private-label buyers"],
            "search_intent": "commercial product",
            "keyword_themes": {
                "primary": ["paint roller cover wholesale"],
                "secondary": ["private label paint roller cover"],
                "validation_status": "needs_keyword_research",
            },
            "metadata_guidance": {
                "title_pattern": "Paint Roller Cover | Specification | Example",
                "meta_description_should_cover": ["verified material and size"],
            },
        },
    ],
}


class ContentAgentTests(unittest.TestCase):
    def test_builds_page_type_specific_content_briefs(self) -> None:
        plan = build_content_plan(SAMPLE_SEO_PLAN)

        self.assertEqual(plan["content_agent_version"], "0.1")
        self.assertEqual(plan["summary"]["content_briefs"], 2)
        self.assertEqual(
            plan["summary"]["briefs_by_page_type"],
            {"homepage": 1, "product_detail": 1},
        )
        self.assertEqual(
            plan["content_briefs"][0]["content_brief_id"], "CONTENT-001"
        )

    def test_product_brief_requires_verified_specs(self) -> None:
        plan = build_content_plan(SAMPLE_SEO_PLAN)
        product_brief = plan["content_briefs"][1]

        self.assertTrue(
            any(
                "material, size" in item
                for item in product_brief["required_verified_inputs"]
            )
        )
        self.assertEqual(
            product_brief["keyword_assignment"]["validation_status"],
            "needs_keyword_research",
        )
        self.assertEqual(product_brief["cta_draft"]["status"], "approval_required")

    def test_every_brief_is_fact_checked_and_publication_gated(self) -> None:
        plan = build_content_plan(SAMPLE_SEO_PLAN)

        self.assertFalse(plan["content_policy"]["production_publish_allowed"])
        self.assertEqual(plan["summary"]["production_pages_authorized"], 0)
        for brief in plan["content_briefs"]:
            self.assertFalse(
                brief["publication_gate"]["production_publish_allowed"]
            )
            self.assertEqual(brief["publication_gate"]["status"], "brief_only")
            self.assertTrue(
                all(
                    section["evidence_status"] == "Needs verification"
                    for section in brief["recommended_sections"]
                )
            )

    def test_rejects_plan_without_page_plans(self) -> None:
        with self.assertRaisesRegex(ValueError, "page_plans list"):
            build_content_plan({"seo_agent_version": "0.1"})


if __name__ == "__main__":
    unittest.main()
