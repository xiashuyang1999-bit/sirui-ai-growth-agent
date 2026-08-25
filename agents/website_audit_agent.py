"""Read-only website audit agent for overseas B2B acquisition."""

from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urldefrag, urljoin, urlparse, urlunparse
from urllib.request import Request, urlopen

AGENT_VERSION = "0.4"
USER_AGENT = f"SIRUI-Website-Audit-Agent/{AGENT_VERSION}"
MAX_RESPONSE_BYTES = 2_000_000
MAX_PAGES = 25
MAX_DISCOVERED_LINKS = 200
MAX_SITEMAP_FILES = 3
AUDIT_ERRORS = (HTTPError, URLError, TimeoutError, UnicodeError, ValueError)
SKIPPED_FILE_SUFFIXES = {
    ".css",
    ".gif",
    ".ico",
    ".jpeg",
    ".jpg",
    ".js",
    ".json",
    ".pdf",
    ".png",
    ".svg",
    ".webp",
    ".xml",
    ".zip",
}
PRIORITY_PATH_TERMS = (
    "about",
    "product",
    "contact",
    "factory",
    "oem",
    "odm",
    "private-label",
    "catalog",
)
SEVERITY_PRIORITY = {"high": "P1", "medium": "P2", "low": "P3"}


class _PageParser(HTMLParser):
    """Collect the small set of HTML signals needed by the audit."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.description = ""
        self.canonical = ""
        self.language = ""
        self.h1: list[str] = []
        self.links: list[dict[str, str]] = []
        self.forms = 0
        self.json_ld_scripts: list[str] = []
        self._text: list[str] = []
        self._current_tag = ""
        self._ignored_depth = 0
        self._json_ld_buffer: list[str] | None = None

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        attributes = {key.lower(): value or "" for key, value in attrs}
        self._current_tag = tag.lower()

        if self._current_tag in {"script", "style", "noscript"}:
            self._ignored_depth += 1
            if (
                self._current_tag == "script"
                and attributes.get("type", "").lower().split(";", 1)[0].strip()
                == "application/ld+json"
            ):
                self._json_ld_buffer = []
        elif self._current_tag == "html":
            self.language = attributes.get("lang", "")
        elif self._current_tag == "meta":
            if attributes.get("name", "").lower() == "description":
                self.description = attributes.get("content", "").strip()
        elif self._current_tag == "link":
            if "canonical" in attributes.get("rel", "").lower().split():
                self.canonical = attributes.get("href", "").strip()
        elif self._current_tag == "a":
            self.links.append({"href": attributes.get("href", ""), "text": ""})
        elif self._current_tag == "form":
            self.forms += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self._json_ld_buffer is not None:
            script = "".join(self._json_ld_buffer).strip()
            if script:
                self.json_ld_scripts.append(script)
            self._json_ld_buffer = None
        if tag.lower() in {"script", "style", "noscript"} and self._ignored_depth:
            self._ignored_depth -= 1
        self._current_tag = ""

    def handle_data(self, data: str) -> None:
        if self._json_ld_buffer is not None:
            self._json_ld_buffer.append(data)
            return
        if self._ignored_depth:
            return

        text = " ".join(data.split())
        if not text:
            return

        self._text.append(text)
        if self._current_tag == "title":
            self.title = f"{self.title} {text}".strip()
        elif self._current_tag == "h1":
            self.h1.append(text)
        elif self._current_tag == "a" and self.links:
            self.links[-1]["text"] = f"{self.links[-1]['text']} {text}".strip()

    @property
    def visible_text(self) -> str:
        return " ".join(self._text)


def _check(
    name: str,
    passed: bool,
    evidence: str,
    severity: str,
    recommendation: str,
) -> dict[str, Any]:
    return {
        "name": name,
        "status": "pass" if passed else "warning",
        "evidence": evidence,
        "severity": None if passed else severity,
        "priority": None if passed else SEVERITY_PRIORITY[severity],
        "recommendation": None if passed else recommendation,
    }


def _section(checks: list[dict[str, Any]]) -> dict[str, Any]:
    if not checks:
        return {"status": "not_applicable", "checks": []}
    warnings = sum(check["status"] == "warning" for check in checks)
    return {"status": "pass" if warnings == 0 else "needs_review", "checks": checks}


def _contains_any(text: str, phrases: tuple[str, ...]) -> list[str]:
    lowered = text.lower()
    return [phrase for phrase in phrases if phrase in lowered]


def _title_h1_aligned(title: str, headings: list[str]) -> bool:
    if not title or not headings:
        return False
    ignored = {"and", "china", "for", "in", "sirui", "the", "with"}
    title_words = {
        word for word in re.findall(r"[a-z0-9]+", title.lower()) if word not in ignored
    }
    h1_words = {
        word
        for word in re.findall(r"[a-z0-9]+", " ".join(headings).lower())
        if word not in ignored
    }
    return bool(h1_words) and len(title_words & h1_words) / len(h1_words) >= 0.6


def _extract_schema_types(scripts: list[str]) -> tuple[list[str], int]:
    schema_types: set[str] = set()
    invalid_blocks = 0

    def collect(value: Any) -> None:
        if isinstance(value, dict):
            schema_type = value.get("@type")
            if isinstance(schema_type, str):
                schema_types.add(schema_type)
            elif isinstance(schema_type, list):
                schema_types.update(
                    item for item in schema_type if isinstance(item, str)
                )
            for child in value.values():
                if isinstance(child, (dict, list)):
                    collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)

    for script in scripts:
        try:
            collect(json.loads(script))
        except (json.JSONDecodeError, TypeError):
            invalid_blocks += 1
    return sorted(schema_types), invalid_blocks


def _validate_url(url: str) -> str:
    normalized = url.strip()
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("URL must be an absolute http:// or https:// address.")
    if parsed.username or parsed.password:
        raise ValueError("URLs containing credentials are not supported.")
    path = parsed.path or "/"
    return urlunparse((parsed.scheme, parsed.netloc, path, "", parsed.query, ""))


def _site_host(url: str) -> str:
    return (urlparse(url).hostname or "").lower().removeprefix("www.")


def _normalize_discovered_url(base_url: str, href: str, host: str) -> str | None:
    if not href or href.lower().startswith(("mailto:", "tel:", "javascript:")):
        return None

    absolute_url, _ = urldefrag(urljoin(base_url, href))
    parsed = urlparse(absolute_url)
    if parsed.scheme not in {"http", "https"} or _site_host(absolute_url) != host:
        return None
    if any(parsed.path.lower().endswith(suffix) for suffix in SKIPPED_FILE_SUFFIXES):
        return None

    normalized_path = parsed.path or "/"
    if normalized_path != "/":
        normalized_path = normalized_path.rstrip("/")
    return urlunparse((parsed.scheme, parsed.netloc, normalized_path, "", "", ""))


def _link_priority(url: str) -> tuple[int, int, int, str]:
    path = urlparse(url).path.lower()
    matched_positions = [
        index for index, term in enumerate(PRIORITY_PATH_TERMS) if term in path
    ]
    is_priority = 0 if matched_positions else 1
    term_position = min(matched_positions, default=len(PRIORITY_PATH_TERMS))
    depth = len([part for part in path.split("/") if part])
    return is_priority, term_position, depth, path


def _discover_same_domain_links(page: dict[str, Any], host: str) -> list[str]:
    parser = _PageParser()
    parser.feed(page["html"])

    discovered: set[str] = set()
    for link in parser.links[:MAX_DISCOVERED_LINKS]:
        normalized = _normalize_discovered_url(
            page["final_url"], link["href"], host
        )
        if normalized:
            discovered.add(normalized)
    return sorted(discovered, key=_link_priority)


def _classify_page(url: str) -> str:
    path = urlparse(url).path.lower().strip("/")
    if not path:
        return "homepage"
    if path == "products":
        return "product_index"
    if path.startswith("products/"):
        return "product_detail"
    for page_type, terms in (
        ("about", ("about", "company", "factory")),
        ("contact", ("contact", "inquiry", "quote")),
        ("product_index", ("product", "category", "paint-roller", "roller-cover")),
        ("b2b_service", ("oem", "odm", "private-label", "wholesale")),
    ):
        if any(term in path for term in terms):
            return page_type
    return "other"


def _fetch_page(url: str, timeout: float = 15.0) -> dict[str, Any]:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:  # noqa: S310
        content_type = response.headers.get_content_type()
        if content_type not in {"text/html", "application/xhtml+xml"}:
            raise ValueError(f"Expected an HTML page, received {content_type}.")

        body = response.read(MAX_RESPONSE_BYTES + 1)
        if len(body) > MAX_RESPONSE_BYTES:
            raise ValueError("Page response is larger than the 2 MB audit limit.")

        charset = response.headers.get_content_charset() or "utf-8"
        return {
            "final_url": response.geturl(),
            "http_status": response.status,
            "html": body.decode(charset, errors="replace"),
        }


def _fetch_text_resource(url: str, timeout: float = 15.0) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(2):
        request = Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urlopen(request, timeout=timeout) as response:  # noqa: S310
                body = response.read(MAX_RESPONSE_BYTES + 1)
                if len(body) > MAX_RESPONSE_BYTES:
                    raise ValueError(
                        "Technical SEO resource exceeds the 2 MB audit limit."
                    )
                charset = response.headers.get_content_charset() or "utf-8"
                return {
                    "final_url": response.geturl(),
                    "http_status": response.status,
                    "content_type": response.headers.get_content_type(),
                    "text": body.decode(charset, errors="replace"),
                }
        except HTTPError:
            raise
        except (URLError, TimeoutError) as error:
            last_error = error
            if attempt == 1:
                raise
    raise URLError(str(last_error))


def _positioning_checks(
    page_type: str,
    parser: _PageParser,
    positioning_text: str,
    visible_text: str,
) -> list[dict[str, Any]]:
    manufacturer_terms = _contains_any(
        positioning_text, ("manufacturer", "factory", "supplier")
    )
    product_terms = _contains_any(
        positioning_text,
        (
            "paint brush",
            "paint brushes",
            "paint roller",
            "paint rollers",
            "roller cover",
            "roller frame",
            "painting tool",
        ),
    )
    single_h1 = _check(
        "Single focused H1",
        len(parser.h1) == 1,
        f"Found {len(parser.h1)} H1 heading(s).",
        "high",
        "Use one descriptive H1 that matches the page's primary purpose.",
    )

    if page_type == "homepage":
        return [
            _check(
                "Clear manufacturer positioning",
                bool(manufacturer_terms),
                f"Signals found: {', '.join(manufacturer_terms)}"
                if manufacturer_terms
                else "No manufacturer, factory, or supplier signal in the title/H1.",
                "high",
                "State the manufacturer or factory role clearly in the homepage title or H1.",
            ),
            _check(
                "Core product categories are stated",
                bool(product_terms),
                f"Product terms found: {', '.join(product_terms)}"
                if product_terms
                else "No paint-brush, paint-roller, cover, frame, or painting-tool term in the title/H1.",
                "high",
                "Name the primary paint-brush or paint-roller categories in the homepage title or H1.",
            ),
            single_h1,
        ]
    if page_type == "product_index":
        return [
            _check(
                "Product category purpose is clear",
                bool(product_terms),
                f"Product terms found: {', '.join(product_terms)}"
                if product_terms
                else "No primary product category found in the title/H1.",
                "high",
                "Name the primary product categories in the product-index title or H1.",
            ),
            single_h1,
        ]
    if page_type == "product_detail":
        return [
            _check(
                "Product identity is present",
                bool(parser.title and parser.h1),
                f"Title: {parser.title or 'missing'}; H1 count: {len(parser.h1)}.",
                "high",
                "Give the product a specific title and one product-name H1.",
            ),
            _check(
                "Product title and H1 are aligned",
                _title_h1_aligned(parser.title, parser.h1),
                "The title and H1 share the product's key terms."
                if _title_h1_aligned(parser.title, parser.h1)
                else "The title and H1 do not share enough product terms.",
                "low",
                "Align the product title and H1 around the same product name and specification.",
            ),
        ]
    if page_type == "about":
        factory_terms = _contains_any(
            f"{positioning_text} {visible_text}",
            ("factory", "manufacturer", "production", "quality control"),
        )
        return [
            _check(
                "Factory purpose is clear",
                bool(factory_terms),
                f"Factory signals found: {', '.join(factory_terms)}"
                if factory_terms
                else "No factory, manufacturing, production, or quality-control signal found.",
                "medium",
                "Explain the factory, production, or quality-control purpose clearly.",
            ),
            single_h1,
        ]
    if page_type == "b2b_service":
        service_terms = _contains_any(
            positioning_text, ("oem", "odm", "private label", "private-label")
        )
        return [
            _check(
                "OEM/private-label purpose is clear",
                bool(service_terms),
                f"Service signals found: {', '.join(service_terms)}"
                if service_terms
                else "No OEM, ODM, or private-label signal in the title/H1.",
                "high",
                "State OEM, ODM, or private-label capability in the title or H1.",
            ),
            _check(
                "Relevant product categories are stated",
                bool(product_terms),
                f"Product terms found: {', '.join(product_terms)}"
                if product_terms
                else "No paint-brush or paint-roller category in the title/H1.",
                "medium",
                "Connect the OEM/private-label offer to the relevant product categories.",
            ),
            single_h1,
        ]
    if page_type == "contact":
        inquiry_terms = _contains_any(
            positioning_text, ("contact", "inquiry", "quote", "request")
        )
        return [
            _check(
                "Inquiry purpose is clear",
                bool(inquiry_terms),
                f"Inquiry signals found: {', '.join(inquiry_terms)}"
                if inquiry_terms
                else "No contact, inquiry, quote, or request signal in the title/H1.",
                "high",
                "Use a title or H1 that clearly tells buyers how to inquire or request a quote.",
            ),
            single_h1,
        ]
    return [single_h1]


def _product_structure_checks(
    page_type: str, product_links: list[dict[str, str]]
) -> list[dict[str, Any]]:
    count = len(product_links)
    if page_type == "homepage":
        return [
            _check(
                "Product navigation is discoverable",
                count > 0,
                f"Found {count} product-related link(s).",
                "high",
                "Add a clear route from the homepage to the product catalog.",
            ),
            _check(
                "Multiple product paths are available",
                count >= 3,
                f"Found {count} product-related link(s); target is at least 3.",
                "medium",
                "Expose at least three useful product or category paths on the homepage.",
            ),
        ]
    if page_type == "product_index":
        return [
            _check(
                "Product range is discoverable",
                count >= 3,
                f"Found {count} product-related link(s); target is at least 3.",
                "high",
                "Expose at least three product or category paths on the product index.",
            )
        ]
    if page_type == "product_detail":
        return [
            _check(
                "Related product path is available",
                count > 0,
                f"Found {count} product-related link(s).",
                "low",
                "Add a route to the product category or related products.",
            )
        ]
    return []


def _conversion_checks(
    page_type: str,
    b2b_terms: list[str],
    conversion_terms: list[str],
    contact_links: list[str],
    form_count: int,
) -> list[dict[str, Any]]:
    has_conversion_action = bool(conversion_terms or form_count)
    has_contact_route = bool(contact_links or form_count)
    checks: list[dict[str, Any]] = []

    if page_type in {"homepage", "product_index", "b2b_service"}:
        checks.append(
            _check(
                "B2B offer is visible",
                bool(b2b_terms),
                f"Signals found: {', '.join(b2b_terms)}"
                if b2b_terms
                else "No OEM/ODM, private-label, wholesale, distributor, or bulk signal found.",
                "high",
                "State the OEM/ODM, private-label, wholesale, or distributor offer clearly.",
            )
        )
    checks.extend(
        [
            _check(
                "Conversion action is visible",
                has_conversion_action,
                f"Calls to action found: {', '.join(conversion_terms)}; forms: {form_count}."
                if has_conversion_action
                else "No quote, inquiry, contact, catalog call to action, or form found.",
                "high",
                "Add a clear inquiry, quote, contact, or catalog action.",
            ),
            _check(
                "Direct contact route is available",
                has_contact_route,
                f"Found {len(contact_links)} email, phone, or WhatsApp link(s) and {form_count} form(s).",
                "medium",
                "Provide a visible inquiry form, email, phone, or WhatsApp route.",
            ),
        ]
    )
    return checks


def _technical_page_checks(
    page_type: str,
    page: dict[str, Any],
    schema_types: list[str],
    invalid_json_ld: int,
    json_ld_blocks: int,
) -> list[dict[str, Any]]:
    checks = [
        _check(
            "Successful HTTP response",
            200 <= page["http_status"] < 300,
            f"HTTP status: {page['http_status']}.",
            "high",
            "Return a successful 2xx response for this indexable page.",
        )
    ]

    expected_schema: tuple[str, ...] = ()
    if page_type == "homepage":
        expected_schema = ("Organization", "WebSite")
    elif page_type == "product_detail":
        expected_schema = ("Product",)

    if expected_schema:
        matching_types = sorted(set(schema_types) & set(expected_schema))
        checks.append(
            _check(
                "Relevant structured data is present",
                bool(matching_types),
                f"Schema types found: {', '.join(schema_types)}"
                if schema_types
                else "No JSON-LD schema types found.",
                "medium",
                f"Add valid {' or '.join(expected_schema)} JSON-LD for this page type.",
            )
        )
    if json_ld_blocks:
        checks.append(
            _check(
                "JSON-LD blocks are valid JSON",
                invalid_json_ld == 0,
                f"Found {json_ld_blocks} JSON-LD block(s); {invalid_json_ld} invalid.",
                "medium",
                "Correct invalid JSON-LD so search engines can parse the structured data.",
            )
        )
    return checks


def _analyze_page(page: dict[str, Any], page_type: str) -> dict[str, Any]:
    parser = _PageParser()
    parser.feed(page["html"])
    schema_types, invalid_json_ld = _extract_schema_types(parser.json_ld_scripts)

    visible_text = parser.visible_text
    positioning_text = " ".join([parser.title, *parser.h1])
    product_links = [
        link
        for link in parser.links
        if _contains_any(
            f"{link['text']} {link['href']}",
            ("product", "paint-roller", "roller-cover", "roller-frame", "category"),
        )
    ]
    b2b_terms = _contains_any(
        visible_text,
        ("oem", "odm", "private label", "wholesale", "distributor", "bulk"),
    )
    conversion_terms = _contains_any(
        visible_text,
        ("request a quote", "get a quote", "send inquiry", "contact us", "catalog"),
    )
    contact_links = [
        link["href"]
        for link in parser.links
        if link["href"].lower().startswith(("mailto:", "tel:", "https://wa.me/"))
    ]

    sections = {
        "positioning": _section(
            _positioning_checks(page_type, parser, positioning_text, visible_text)
        ),
        "seo_basics": _section(
            [
                _check(
                    "Page title present",
                    bool(parser.title),
                    parser.title or "No title element found.",
                    "high",
                    "Add a unique, descriptive page title.",
                ),
                _check(
                    "Meta description present",
                    bool(parser.description),
                    parser.description or "No meta description found.",
                    "medium",
                    "Add a buyer-focused meta description for this page.",
                ),
                _check(
                    "Canonical URL present",
                    bool(parser.canonical),
                    urljoin(page["final_url"], parser.canonical)
                    if parser.canonical
                    else "No canonical link found.",
                    "medium",
                    "Add a self-referencing canonical that follows the site's chosen hostname and language convention.",
                ),
                _check(
                    "HTML language declared",
                    bool(parser.language),
                    parser.language or "No lang attribute found on the html element.",
                    "low",
                    "Declare the page language on the html element.",
                ),
            ]
        ),
        "product_structure": _section(
            _product_structure_checks(page_type, product_links)
        ),
        "b2b_conversion_elements": _section(
            _conversion_checks(
                page_type,
                b2b_terms,
                conversion_terms,
                contact_links,
                parser.forms,
            )
        ),
        "technical_basics": _section(
            _technical_page_checks(
                page_type,
                page,
                schema_types,
                invalid_json_ld,
                len(parser.json_ld_scripts),
            )
        ),
    }

    checks = [check for section in sections.values() for check in section["checks"]]
    passed = sum(check["status"] == "pass" for check in checks)
    issue_counts = {
        severity: sum(
            check["status"] == "warning" and check["severity"] == severity
            for check in checks
        )
        for severity in ("high", "medium", "low")
    }
    return {
        "page": {
            "final_url": page["final_url"],
            "http_status": page["http_status"],
            "title": parser.title,
            "meta_description": parser.description,
            "h1": parser.h1,
            "forms": parser.forms,
            "canonical": urljoin(page["final_url"], parser.canonical)
            if parser.canonical
            else "",
            "schema_types": schema_types,
            "json_ld_blocks": len(parser.json_ld_scripts),
            "invalid_json_ld_blocks": invalid_json_ld,
        },
        "summary": {
            "status": "pass" if passed == len(checks) else "needs_review",
            "checks_passed": passed,
            "checks_total": len(checks),
            "issue_count": len(checks) - passed,
            "issues_by_severity": issue_counts,
        },
        "sections": sections,
    }


def _error_report(url: str, audited_at: str, error: Exception) -> dict[str, Any]:
    return {
        "requested_url": url,
        "audited_at": audited_at,
        "page_type": _classify_page(url),
        "summary": {
            "status": "error",
            "checks_passed": 0,
            "checks_total": 0,
            "issue_count": 0,
            "issues_by_severity": {"high": 0, "medium": 0, "low": 0},
        },
        "sections": {},
        "errors": [str(error)],
    }


def _audit_fetched_page(
    requested_url: str, page: dict[str, Any], audited_at: str
) -> dict[str, Any]:
    page_type = _classify_page(page["final_url"])
    return {
        "requested_url": requested_url,
        "audited_at": audited_at,
        "page_type": page_type,
        **_analyze_page(page, page_type),
        "errors": [],
    }


def audit_website(url: str) -> dict[str, Any]:
    """Fetch one page and return a structured, evidence-based audit report."""

    audited_at = datetime.now(timezone.utc).isoformat()
    try:
        normalized_url = _validate_url(url)
        return {
            "agent_version": AGENT_VERSION,
            **_audit_fetched_page(
                normalized_url, _fetch_page(normalized_url), audited_at
            ),
        }
    except AUDIT_ERRORS as error:
        return {
            "agent_version": AGENT_VERSION,
            **_error_report(url, audited_at, error),
        }


def _site_issue(
    url: str,
    name: str,
    evidence: str,
    severity: str,
    recommendation: str,
) -> dict[str, Any]:
    return {
        "url": url,
        "page_type": "site",
        "section": "technical_seo",
        **_check(name, False, evidence, severity, recommendation),
    }


def _url_identity(url: str) -> tuple[str, str]:
    parsed = urlparse(url)
    path = parsed.path.rstrip("/") or "/"
    return _site_host(url), path.lower()


def _parse_sitemap_document(text: str) -> tuple[list[str], list[str]]:
    lowered = text.lower()
    if "<!doctype" in lowered or "<!entity" in lowered:
        raise ET.ParseError("DOCTYPE and entity declarations are not supported.")
    root = ET.fromstring(text)
    page_urls: list[str] = []
    child_sitemaps: list[str] = []
    root_name = root.tag.rsplit("}", 1)[-1].lower()

    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1].lower() != "loc" or not element.text:
            continue
        location = element.text.strip()
        if root_name == "sitemapindex":
            child_sitemaps.append(location)
        elif root_name == "urlset":
            page_urls.append(location)
    if root_name not in {"sitemapindex", "urlset"}:
        raise ET.ParseError(f"Unsupported sitemap root element: {root_name}")
    return page_urls, child_sitemaps


def _audit_technical_seo(
    root_url: str, page_reports: list[dict[str, Any]]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    root = urlunparse((*urlparse(root_url)[:2], "/", "", "", ""))
    host = _site_host(root_url)
    issues: list[dict[str, Any]] = []

    robots_url = urljoin(root, "robots.txt")
    robots_report: dict[str, Any] = {
        "url": robots_url,
        "accessible": False,
        "http_status": None,
        "has_user_agent": False,
        "blocks_all_crawlers": False,
        "sitemap_directives": [],
        "error": "",
    }
    sitemap_candidates: list[str] = []
    try:
        robots_resource = _fetch_text_resource(robots_url)
        robots_text = robots_resource["text"]
        lines = [line.strip() for line in robots_text.splitlines()]
        sitemap_candidates = [
            urljoin(root, line.split(":", 1)[1].strip())
            for line in lines
            if line.lower().startswith("sitemap:") and ":" in line
        ]
        has_user_agent = any(
            line.lower().startswith("user-agent:") for line in lines
        )
        applies_to_all = False
        blocks_all = False
        for line in lines:
            lowered = line.lower()
            if lowered.startswith("user-agent:"):
                applies_to_all = lowered.split(":", 1)[1].strip() == "*"
            elif applies_to_all and lowered.startswith("disallow:"):
                if lowered.split(":", 1)[1].strip() == "/":
                    blocks_all = True
        robots_report.update(
            {
                "url": robots_resource["final_url"],
                "accessible": True,
                "http_status": robots_resource["http_status"],
                "has_user_agent": has_user_agent,
                "blocks_all_crawlers": blocks_all,
                "sitemap_directives": sitemap_candidates,
            }
        )
        if not has_user_agent:
            issues.append(
                _site_issue(
                    robots_url,
                    "robots.txt contains crawler directives",
                    "robots.txt is accessible but has no User-agent directive.",
                    "low",
                    "Add explicit User-agent rules so crawl policy is clear.",
                )
            )
        if blocks_all:
            issues.append(
                _site_issue(
                    robots_url,
                    "Production crawl is allowed",
                    "User-agent: * includes Disallow: /.",
                    "high",
                    "Remove the site-wide disallow rule from the production robots.txt.",
                )
            )
    except AUDIT_ERRORS as error:
        robots_report["error"] = str(error)
        issues.append(
            _site_issue(
                robots_url,
                "robots.txt is accessible",
                f"robots.txt could not be fetched: {error}",
                "low",
                "Publish a readable robots.txt with the intended crawl policy and sitemap location.",
            )
        )

    same_domain_sitemaps = [
        sitemap_url
        for sitemap_url in sitemap_candidates
        if _site_host(sitemap_url) == host
    ]
    sitemap_queue = same_domain_sitemaps or [urljoin(root, "sitemap.xml")]
    sitemap_queue = list(dict.fromkeys(sitemap_queue))
    sitemap_files: list[dict[str, Any]] = []
    sitemap_urls: set[str] = set()
    visited_sitemaps: set[str] = set()

    while sitemap_queue and len(visited_sitemaps) < MAX_SITEMAP_FILES:
        sitemap_url = sitemap_queue.pop(0)
        if sitemap_url in visited_sitemaps or _site_host(sitemap_url) != host:
            continue
        visited_sitemaps.add(sitemap_url)
        try:
            resource = _fetch_text_resource(sitemap_url)
            page_urls, child_sitemaps = _parse_sitemap_document(resource["text"])
            same_domain_pages = [url for url in page_urls if _site_host(url) == host]
            sitemap_urls.update(same_domain_pages)
            sitemap_files.append(
                {
                    "url": resource["final_url"],
                    "http_status": resource["http_status"],
                    "valid": True,
                    "page_urls": len(page_urls),
                    "child_sitemaps": len(child_sitemaps),
                    "error": "",
                }
            )
            for child_url in child_sitemaps:
                if _site_host(child_url) == host and child_url not in visited_sitemaps:
                    sitemap_queue.append(child_url)
        except (*AUDIT_ERRORS, ET.ParseError) as error:
            sitemap_files.append(
                {
                    "url": sitemap_url,
                    "http_status": None,
                    "valid": False,
                    "page_urls": 0,
                    "child_sitemaps": 0,
                    "error": str(error),
                }
            )

    valid_sitemaps = [item for item in sitemap_files if item["valid"]]
    sitemap_report: dict[str, Any] = {
        "files_checked": sitemap_files,
        "valid_files": len(valid_sitemaps),
        "urls_found": len(sitemap_urls),
        "same_domain_urls": len(sitemap_urls),
        "audited_indexable_pages": 0,
        "audited_pages_covered": 0,
        "missing_audited_pages": [],
    }
    if not valid_sitemaps:
        failed_sitemap_url = (
            sitemap_files[0]["url"]
            if sitemap_files
            else urljoin(root, "sitemap.xml")
        )
        issues.append(
            _site_issue(
                failed_sitemap_url,
                "XML sitemap is accessible and valid",
                "No valid same-domain sitemap was found within the file limit.",
                "medium",
                "Publish a valid XML sitemap and reference it from robots.txt.",
            )
        )
    else:
        indexable_types = {
            "homepage",
            "product_index",
            "product_detail",
            "about",
            "b2b_service",
        }
        indexable_pages = [
            report["page"]["final_url"]
            for report in page_reports
            if report["page_type"] in indexable_types
        ]
        sitemap_identities = {_url_identity(url) for url in sitemap_urls}
        missing_pages = [
            url for url in indexable_pages if _url_identity(url) not in sitemap_identities
        ]
        sitemap_report.update(
            {
                "audited_indexable_pages": len(indexable_pages),
                "audited_pages_covered": len(indexable_pages) - len(missing_pages),
                "missing_audited_pages": missing_pages,
            }
        )
        if missing_pages:
            issues.append(
                _site_issue(
                    valid_sitemaps[0]["url"],
                    "Audited indexable pages are represented in the sitemap",
                    f"{len(missing_pages)} audited indexable page(s) were not found in the checked sitemap files.",
                    "low",
                    "Add intended indexable pages to the XML sitemap or document why they should be excluded.",
                )
            )

    canonical_pages = [
        {
            "url": report["page"]["final_url"],
            "canonical": report["page"]["canonical"],
        }
        for report in page_reports
        if report["page"]["canonical"]
    ]
    canonical_hosts = sorted(
        {urlparse(item["canonical"]).hostname or "" for item in canonical_pages}
    )
    host_mismatches = [
        item
        for item in canonical_pages
        if (urlparse(item["url"]).hostname or "").lower()
        != (urlparse(item["canonical"]).hostname or "").lower()
    ]
    canonical_report = {
        "canonical_pages": len(canonical_pages),
        "canonical_hosts": canonical_hosts,
        "served_to_canonical_host_mismatches": host_mismatches,
    }
    if len(canonical_hosts) > 1:
        issues.append(
            _site_issue(
                root_url,
                "Canonical hostname is consistent",
                f"Multiple canonical hostnames found: {', '.join(canonical_hosts)}.",
                "medium",
                "Choose one preferred hostname and use it consistently in canonical links.",
            )
        )
    if host_mismatches:
        issues.append(
            _site_issue(
                root_url,
                "Served and canonical hostnames are aligned",
                f"{len(host_mismatches)} audited page(s) use a canonical hostname different from the served hostname.",
                "low",
                "Verify redirects, internal links, sitemap URLs, and canonicals all use the chosen preferred hostname.",
            )
        )

    return (
        {
            "robots": robots_report,
            "sitemap": sitemap_report,
            "canonical_consistency": canonical_report,
        },
        issues,
    )


def audit_site(url: str, max_pages: int = 8) -> dict[str, Any]:
    """Audit a limited set of same-domain pages and return a site-wide report."""

    audited_at = datetime.now(timezone.utc).isoformat()
    try:
        normalized_url = _validate_url(url)
        if not 1 <= max_pages <= MAX_PAGES:
            raise ValueError(f"max_pages must be between 1 and {MAX_PAGES}.")
    except ValueError as error:
        return {
            "agent_version": AGENT_VERSION,
            "requested_url": url,
            "audited_at": audited_at,
            "summary": {
                "status": "error",
                "pages_audited": 0,
                "pages_failed": 0,
                "checks_passed": 0,
                "checks_total": 0,
                "issue_count": 0,
                "issues_by_severity": {"high": 0, "medium": 0, "low": 0},
                "page_types": {},
            },
            "pages": [],
            "prioritized_issues": [],
            "errors": [str(error)],
        }

    host = _site_host(normalized_url)
    queue = [normalized_url]
    queued = {normalized_url}
    visited: set[str] = set()
    page_reports: list[dict[str, Any]] = []

    while queue and len(visited) < max_pages:
        current_url = queue.pop(0)
        queued.discard(current_url)
        if current_url in visited:
            continue
        visited.add(current_url)

        try:
            page = _fetch_page(current_url)
            page_reports.append(_audit_fetched_page(current_url, page, audited_at))
            for discovered_url in _discover_same_domain_links(page, host):
                if discovered_url not in visited and discovered_url not in queued:
                    queue.append(discovered_url)
                    queued.add(discovered_url)
            queue.sort(key=_link_priority)
        except AUDIT_ERRORS as error:
            page_reports.append(_error_report(current_url, audited_at, error))

    successful_pages = [
        report for report in page_reports if report["summary"]["status"] != "error"
    ]
    failed_pages = len(page_reports) - len(successful_pages)
    checks_passed = sum(
        report["summary"]["checks_passed"] for report in successful_pages
    )
    checks_total = sum(
        report["summary"]["checks_total"] for report in successful_pages
    )
    prioritized_issues = [
        {
            "url": report["requested_url"],
            "page_type": report["page_type"],
            "section": section_name,
            **check,
        }
        for report in successful_pages
        for section_name, section in report["sections"].items()
        for check in section["checks"]
        if check["status"] == "warning"
    ]
    technical_seo, technical_issues = _audit_technical_seo(
        normalized_url, successful_pages
    )
    prioritized_issues.extend(technical_issues)
    priority_order = {"P1": 0, "P2": 1, "P3": 2}
    prioritized_issues.sort(
        key=lambda issue: (
            priority_order[issue["priority"]],
            issue["url"],
            issue["name"],
        )
    )
    issues_by_severity = {
        severity: sum(issue["severity"] == severity for issue in prioritized_issues)
        for severity in ("high", "medium", "low")
    }
    if not successful_pages:
        status = "error"
    elif failed_pages or prioritized_issues:
        status = "needs_review"
    else:
        status = "pass"

    page_type_counts: dict[str, int] = {}
    for report in successful_pages:
        page_type = report["page_type"]
        page_type_counts[page_type] = page_type_counts.get(page_type, 0) + 1

    errors = [
        f"{report['requested_url']}: {message}"
        for report in page_reports
        for message in report["errors"]
    ]
    return {
        "agent_version": AGENT_VERSION,
        "requested_url": normalized_url,
        "audited_at": audited_at,
        "crawl": {
            "same_domain_only": True,
            "max_pages": max_pages,
            "urls_discovered": len(visited | queued),
        },
        "summary": {
            "status": status,
            "pages_audited": len(successful_pages),
            "pages_failed": failed_pages,
            "checks_passed": checks_passed,
            "checks_total": checks_total,
            "issue_count": len(prioritized_issues),
            "issues_by_severity": issues_by_severity,
            "page_types": page_type_counts,
        },
        "pages": page_reports,
        "technical_seo": technical_seo,
        "prioritized_issues": prioritized_issues,
        "errors": errors,
    }


def main() -> None:
    """Run the audit agent from the command line and print JSON."""

    if len(sys.argv) != 2:
        raise SystemExit("Usage: python -m agents.website_audit_agent <website-url>")
    print(json.dumps(audit_website(sys.argv[1]), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
