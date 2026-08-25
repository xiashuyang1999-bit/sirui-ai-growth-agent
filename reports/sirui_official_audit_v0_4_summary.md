# SIRUI Website Technical SEO Audit v0.4

- Audit time: 2026-08-25 18:25 (Asia/Shanghai)
- Website: `https://www.siruitool.com/`
- Scope: 8 prioritized pages, robots.txt, XML Sitemap, Schema, and canonical consistency
- Access: read-only; no forms submitted and no production content changed

## Result

- Pages audited: 8
- Page failures: 0
- Checks passed: 82/87
- P1/high issues: 0
- P2/medium issues: 5
- P3/low issues: 1

## Technical SEO strengths

- `robots.txt` returns HTTP 200, contains crawler directives, and does not block all crawlers.
- `robots.txt` references `https://siruitool.com/sitemap.xml`.
- The XML Sitemap returns HTTP 200 and contains 13 same-domain URLs.
- All 7 audited pages considered indexable by v0.4 were represented in the Sitemap.
- All 8 audited pages returned successfully.
- Seven audited pages use one consistent canonical hostname: `siruitool.com`.

## P2 issues

### Homepage structured data

No JSON-LD schema type was detected on the homepage. Add valid `Organization` and/or `WebSite` structured data using verified company information only.

### Product structured data

No `Product` JSON-LD was detected on the three audited product detail pages:

- `/products/angled-sash-paint-brush-50mm`
- `/products/flat-wall-paint-brush-25mm`
- `/products/microfiber-paint-roller-kit`

Add valid `Product` structured data. Do not invent price, availability, ratings, certifications, SKU details, or other properties; include only values verified in the product system.

### Inquiry-page canonical

No canonical link was detected on `/inquiry`. Add a self-referencing canonical after the preferred hostname and English-language URL convention are confirmed.

## P3 verification item

The audited pages were served from `www.siruitool.com`, while seven canonical links use `siruitool.com` with `?lang=en`. Header checks found both hostnames responding successfully instead of showing an obvious hostname redirect.

Choose one preferred hostname, then align redirects, internal links, Sitemap URLs, and canonical URLs. Treat this as a verification task before changing production behavior.

## Suggested implementation order

1. Confirm the preferred hostname and English-language URL convention.
2. Add the missing inquiry-page canonical using that convention.
3. Add verified `Organization`/`WebSite` JSON-LD to the homepage.
4. Add verified `Product` JSON-LD to product detail templates.
5. Rerun v0.4 and confirm the prioritized issue list is empty or contains only accepted exceptions.
