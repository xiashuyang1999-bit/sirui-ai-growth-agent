"""Tests for the website audit agent without making network requests."""

import unittest
from unittest.mock import patch

from agents.website_audit_agent import audit_site, audit_website


SAMPLE_HTML = """
<!doctype html>
<html lang="en">
<head>
  <title>Paint Roller Manufacturer in China</title>
  <meta name="description" content="Factory-direct painting tools for B2B buyers.">
  <link rel="canonical" href="https://example.com/">
</head>
<body>
  <h1>Paint Roller Manufacturer</h1>
  <p>OEM, ODM, private label and wholesale paint roller solutions.</p>
  <a href="/products/rollers">Paint rollers</a>
  <a href="/products/covers">Roller covers</a>
  <a href="/products/frames">Roller frames</a>
  <a href="mailto:sales@example.com">Request a quote</a>
</body>
</html>
"""

CRAWL_HOME_HTML = SAMPLE_HTML.replace(
    "</body>",
    """
  <a href="/about">About our factory</a>
  <a href="/contact">Contact us</a>
  <a href="https://outside.example/products">External product</a>
</body>
""",
)

PRODUCT_DETAIL_HTML = """
<!doctype html>
<html lang="en">
<head>
  <title>50mm Angled Sash Paint Brush | PB-ANGLE-050</title>
  <meta name="description" content="A private-label angled paint brush.">
  <link rel="canonical" href="https://example.com/products/angled-brush">
</head>
<body>
  <h1>50mm Angled Sash Paint Brush</h1>
  <a href="/products">View products</a>
  <a href="mailto:sales@example.com">Send inquiry</a>
</body>
</html>
"""

INQUIRY_HTML_WITHOUT_CANONICAL = """
<!doctype html>
<html lang="en">
<head>
  <title>Request a Quote | SIRUI</title>
  <meta name="description" content="Send a product inquiry to the sales team.">
</head>
<body>
  <h1>Send product inquiry</h1>
  <form><button>Send inquiry</button></form>
</body>
</html>
"""


def page(url: str, html: str = SAMPLE_HTML) -> dict[str, object]:
    return {"final_url": url, "http_status": 200, "html": html}


class WebsiteAuditAgentTests(unittest.TestCase):
    @patch("agents.website_audit_agent._fetch_page")
    def test_returns_all_audit_sections(self, fetch_page) -> None:
        fetch_page.return_value = {
            "final_url": "https://example.com/",
            "http_status": 200,
            "html": SAMPLE_HTML,
        }

        report = audit_website("https://example.com")

        self.assertEqual(report["summary"]["status"], "pass")
        self.assertEqual(
            set(report["sections"]),
            {
                "positioning",
                "seo_basics",
                "product_structure",
                "b2b_conversion_elements",
            },
        )
        self.assertEqual(report["errors"], [])

    def test_invalid_url_returns_structured_error(self) -> None:
        report = audit_website("example.com")

        self.assertEqual(report["summary"]["status"], "error")
        self.assertTrue(report["errors"])

    @patch("agents.website_audit_agent._fetch_page")
    def test_site_audit_follows_prioritized_same_domain_links(self, fetch_page) -> None:
        def fake_fetch(url: str) -> dict[str, object]:
            if url == "https://example.com/":
                return page("https://example.com/", CRAWL_HOME_HTML)
            return page(url)

        fetch_page.side_effect = fake_fetch

        report = audit_site("https://example.com", max_pages=3)

        self.assertEqual(report["summary"]["pages_audited"], 3)
        self.assertEqual(report["summary"]["pages_failed"], 0)
        self.assertEqual(
            report["summary"]["page_types"],
            {"homepage": 1, "about": 1, "product_detail": 1},
        )
        fetched_urls = [call.args[0] for call in fetch_page.call_args_list]
        self.assertNotIn("https://outside.example/products", fetched_urls)
        self.assertNotIn("https://example.com/contact", fetched_urls)

    def test_site_audit_validates_page_limit_without_network(self) -> None:
        report = audit_site("https://example.com", max_pages=0)

        self.assertEqual(report["summary"]["status"], "error")
        self.assertEqual(report["summary"]["pages_audited"], 0)
        self.assertIn("max_pages", report["errors"][0])

    @patch("agents.website_audit_agent._fetch_page")
    def test_product_detail_does_not_require_manufacturer_or_roller_terms(
        self, fetch_page
    ) -> None:
        fetch_page.return_value = page(
            "https://example.com/products/angled-brush", PRODUCT_DETAIL_HTML
        )

        report = audit_website("https://example.com/products/angled-brush")

        self.assertEqual(report["page_type"], "product_detail")
        self.assertEqual(report["summary"]["status"], "pass")
        issue_names = {
            check["name"]
            for section in report["sections"].values()
            for check in section["checks"]
            if check["status"] == "warning"
        }
        self.assertNotIn("Clear manufacturer positioning", issue_names)
        self.assertNotIn("Core product categories are stated", issue_names)

    @patch("agents.website_audit_agent._fetch_page")
    def test_site_report_prioritizes_missing_inquiry_canonical(
        self, fetch_page
    ) -> None:
        fetch_page.return_value = page(
            "https://example.com/inquiry", INQUIRY_HTML_WITHOUT_CANONICAL
        )

        report = audit_site("https://example.com/inquiry", max_pages=1)

        self.assertEqual(report["summary"]["issue_count"], 1)
        self.assertEqual(report["summary"]["issues_by_severity"]["medium"], 1)
        issue = report["prioritized_issues"][0]
        self.assertEqual(issue["name"], "Canonical URL present")
        self.assertEqual(issue["priority"], "P2")
        self.assertTrue(issue["recommendation"])


if __name__ == "__main__":
    unittest.main()
