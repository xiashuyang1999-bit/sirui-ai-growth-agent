"""Tests for local analytics and conversion reporting."""

import unittest

from agents.analytics_agent import build_analytics_report


COMPLETE_METRICS = {
    "period": {"start": "2026-08-01", "end": "2026-08-31"},
    "website": {
        "sessions": 100,
        "engaged_sessions": 60,
        "inquiry_submissions": 10,
    },
    "search": {"clicks": 20, "impressions": 1000, "average_position": 18.5},
    "sales": {
        "attribution_scope": "website_only",
        "qualified_inquiries": 5,
        "sample_projects": 2,
        "quotations": 3,
        "orders": 1,
    },
}


class AnalyticsAgentTests(unittest.TestCase):
    def test_calculates_conversion_rates_from_supplied_values(self) -> None:
        report = build_analytics_report(COMPLETE_METRICS)

        self.assertEqual(report["analytics_agent_version"], "0.1")
        self.assertEqual(report["rates_percent"]["engagement_rate"], 60.0)
        self.assertEqual(
            report["rates_percent"]["search_click_through_rate"], 2.0
        )
        self.assertEqual(report["rates_percent"]["website_inquiry_rate"], 10.0)
        self.assertEqual(
            report["rates_percent"]["website_inquiry_to_qualified_rate"], 50.0
        )
        self.assertEqual(
            report["rates_percent"]["qualified_to_quotation_rate"], 60.0
        )
        self.assertEqual(
            report["rates_percent"]["quotation_to_order_rate"], 33.33
        )

    def test_missing_values_are_not_converted_to_zero(self) -> None:
        report = build_analytics_report(
            {"website": {}, "search": {}, "sales": {}}
        )

        self.assertEqual(report["metrics"]["sessions"], "Needs verification")
        self.assertEqual(
            report["rates_percent"]["website_inquiry_rate"],
            "Needs verification",
        )
        self.assertEqual(report["validation"]["status"], "insufficient_data")
        self.assertEqual(report["opportunities"][0]["area"], "data")

    def test_website_qualified_rate_requires_website_attribution(self) -> None:
        metrics = {
            **COMPLETE_METRICS,
            "sales": {**COMPLETE_METRICS["sales"], "attribution_scope": "all_sources"},
        }

        report = build_analytics_report(metrics)

        self.assertEqual(
            report["rates_percent"]["website_inquiry_to_qualified_rate"],
            "Needs verification",
        )

    def test_flags_suspicious_aggregate_relationships(self) -> None:
        report = build_analytics_report(
            {
                "website": {"sessions": 10, "engaged_sessions": 12},
                "search": {"clicks": 11, "impressions": 10, "average_position": 0},
                "sales": {
                    "qualified_inquiries": 2,
                    "sample_projects": 3,
                    "quotations": 4,
                    "orders": 5,
                },
            }
        )

        self.assertEqual(report["validation"]["status"], "needs_review")
        self.assertGreaterEqual(len(report["validation"]["issues"]), 5)

    def test_rejects_negative_or_non_numeric_metrics(self) -> None:
        with self.assertRaisesRegex(ValueError, "non-negative"):
            build_analytics_report({"website": {"sessions": -1}})
        with self.assertRaisesRegex(ValueError, "non-negative"):
            build_analytics_report({"website": {"sessions": "100"}})

    def test_report_never_writes_external_systems(self) -> None:
        report = build_analytics_report(COMPLETE_METRICS)

        self.assertFalse(report["data_scope"]["external_accounts_accessed"])
        self.assertFalse(report["approval_gate"]["analytics_write_allowed"])
        self.assertFalse(report["approval_gate"]["crm_write_allowed"])


if __name__ == "__main__":
    unittest.main()
