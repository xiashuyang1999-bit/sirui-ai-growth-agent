"""Tests for the website audit agent without making network requests."""

import unittest
import xml.etree.ElementTree as ET
from unittest.mock import patch

from agents.website_audit_agent import (
    _parse_sitemap_document,
    audit_site,
    audit_website,
)


SAMPLE_HTML = """
<!doctype html>
<html lang="en">
<head>
  <title>Paint Roller Manufacturer in China</title>
  <meta name="description" content="Factory-direct painting tools for B2B buyers.">
  <link rel="canonical" href="https://example.com/">
  <script type="application/ld+json">{"@type": "Organization"}</script>
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
  <script type="application/ld+json">{"@type": "Product"}</script>
</head>
<body>
  <h1>50mm Angled Sash Paint Brush</h1>
  <a href="/products">View products</a>
  <a href="mailto:sales@example.com">Send inquiry</a>
</body>
</html>
"""

ROBOTS_TEXT = """User-agent: *
Disallow:
Sitemap: https://example.com/sitemap.xml
"""

SITEMAP_TEXT = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/</loc></url>
  <url><loc>https://example.com/about</loc></url>
  <url><loc>https://example.com/products</loc></url>
  <url><loc>https://example.com/products/angled-brush</loc></url>
  <url><loc>https://example.com/products/covers</loc></url>
  <url><loc>https://example.com/products/frames</loc></url>
  <url><loc>https://example.com/products/rollers</loc></url>
</urlset>
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


def technical_resource(url: str, robots_text: str = ROBOTS_TEXT) -> dict[str, object]:
    if url.endswith("robots.txt"):
        text = robots_text
        content_type = "text/plain"
    else:
        text = SITEMAP_TEXT
        content_type = "application/xml"
    return {
        "final_url": url,
        "http_status": 200,
        "content_type": content_type,
        "text": text,
    }


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
                "technical_basics",
            },
        )
        self.assertEqual(report["errors"], [])

    def test_invalid_url_returns_structured_error(self) -> None:
        report = audit_website("example.com")

        self.assertEqual(report["summary"]["status"], "error")
        self.assertTrue(report["errors"])

    @patch("agents.website_audit_agent._fetch_text_resource")
    @patch("agents.website_audit_agent._fetch_page")
    def test_site_audit_follows_prioritized_same_domain_links(
        self, fetch_page, fetch_text_resource
    ) -> None:
        def fake_fetch(url: str) -> dict[str, object]:
            if url == "https://example.com/":
                return page("https://example.com/", CRAWL_HOME_HTML)
            if "/products/" in url:
                return page(url, PRODUCT_DETAIL_HTML)
            return page(url)

        fetch_page.side_effect = fake_fetch
        fetch_text_resource.side_effect = technical_resource

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

    @patch("agents.website_audit_agent._fetch_text_resource")
    @patch("agents.website_audit_agent._fetch_page")
    def test_site_report_prioritizes_missing_inquiry_canonical(
        self, fetch_page, fetch_text_resource
    ) -> None:
        fetch_page.return_value = page(
            "https://example.com/inquiry", INQUIRY_HTML_WITHOUT_CANONICAL
        )
        fetch_text_resource.side_effect = technical_resource

        report = audit_site("https://example.com/inquiry", max_pages=1)

        self.assertEqual(report["summary"]["issue_count"], 1)
        self.assertEqual(report["summary"]["issues_by_severity"]["medium"], 1)
        issue = report["prioritized_issues"][0]
        self.assertEqual(issue["name"], "Canonical URL present")
        self.assertEqual(issue["priority"], "P2")
        self.assertTrue(issue["recommendation"])

    @patch("agents.website_audit_agent._fetch_text_resource")
    @patch("agents.website_audit_agent._fetch_page")
    def test_robots_disallow_all_is_a_p1_issue(
        self, fetch_page, fetch_text_resource
    ) -> None:
        fetch_page.return_value = page("https://example.com/", SAMPLE_HTML)
        fetch_text_resource.side_effect = lambda url: technical_resource(
            url,
            "User-agent: *\nDisallow: /\nSitemap: https://example.com/sitemap.xml\n",
        )

        report = audit_site("https://example.com", max_pages=1)

        issue = next(
            item
            for item in report["prioritized_issues"]
            if item["name"] == "Production crawl is allowed"
        )
        self.assertEqual(issue["priority"], "P1")
        self.assertEqual(issue["severity"], "high")

    @patch("agents.website_audit_agent._fetch_page")
    def test_product_detail_without_product_schema_is_p2(self, fetch_page) -> None:
        html_without_schema = PRODUCT_DETAIL_HTML.replace(
            '<script type="application/ld+json">{"@type": "Product"}</script>', ""
        )
        fetch_page.return_value = page(
            "https://example.com/products/angled-brush", html_without_schema
        )

        report = audit_website("https://example.com/products/angled-brush")

        issue = next(
            check
            for check in report["sections"]["technical_basics"]["checks"]
            if check["name"] == "Relevant structured data is present"
        )
        self.assertEqual(issue["status"], "warning")
        self.assertEqual(issue["priority"], "P2")

    def test_sitemap_parser_rejects_entity_declarations(self) -> None:
        unsafe_xml = "<!DOCTYPE urlset [<!ENTITY x 'value'>]><urlset></urlset>"

        with self.assertRaises(ET.ParseError):
            _parse_sitemap_document(unsafe_xml)


if __name__ == "__main__":
    unittest.main()
