# SIRUI AI Website Growth Agent 1.0

SIRUI AI Website Growth Agent is a multi-agent system for analyzing and improving [siruitool.com](https://www.siruitool.com) as an overseas B2B customer-acquisition channel. It acts as an evidence-based growth team beside the website: it inspects positioning, SEO, product discovery, and inquiry conversion, then turns findings into prioritized work for marketing, sales, and development.

The current v0.3 release provides a read-only, page-type-aware audit foundation. It applies different rules to homepages, product indexes, product details, factory pages, OEM/private-label pages, inquiry pages, and other pages. Findings include evidence, severity, P1/P2/P3 priority, and a recommended action. Nothing in this version changes the production website.

## Current capabilities

- Validate and fetch an authorized HTTP/HTTPS page without changing it.
- Discover and prioritize same-domain About, Product, Contact, Factory, OEM/ODM, private-label, and catalog paths.
- Limit the crawl to 1-25 pages and ignore external domains and common non-HTML files.
- Check page-specific positioning, SEO basics, product discovery, and B2B conversion routes.
- Detect titles, meta descriptions, canonical links, language, H1 headings, forms, product links, and direct contact links.
- Return page-level findings plus a site-wide prioritized issue list.
- Assign each issue evidence, severity, P1/P2/P3 priority, and a recommended action.
- Save a reusable JSON report for review, comparison, or downstream workflows.

## Application examples

- Launch review: check whether a newly published B2B website has the essential acquisition signals.
- Weekly website health check: compare recurring reports and identify new regressions.
- SEO backlog: convert missing metadata, canonical, heading, and navigation findings into development tasks.
- Conversion review: verify that target buyers can find OEM/private-label offers and reach an inquiry route.
- Product-content QA: check product titles, H1 alignment, related paths, and buyer actions before publishing.
- Agency or internal-team handoff: give marketing, sales, and developers one traceable priority list.

## Short description

> SIRUI AI Website Growth Agent is a read-only overseas B2B website growth system. It audits each page according to its business role, identifies SEO and inquiry-conversion issues with evidence, and produces a prioritized action list for marketing and development teams.

## Planned architecture

- `agents/` — specialized website audit, SEO, content, and developer agents.
- `prompts/` — prompt templates associated with the specialized agents and Codex workflows.
- `workflow/` — orchestration entry points for coordinating agent tasks.
- `docs/` — product requirements and delivery roadmap.
- `data/` — local input datasets and intermediate analysis data.
- `reports/` — generated audit and growth reports.

The intended workflow is to collect approved website inputs, analyze technical and commercial opportunities, generate recommendations, and produce reviewable reports. Any production change must remain a separate, explicitly approved action.

## Website audit usage

Run the offline test suite:

```bash
python3 -m unittest discover -s tests -v
```

Audit one page and print its JSON report:

```bash
python3 -m agents.website_audit_agent https://example.com
```

Audit up to eight prioritized, same-domain pages and automatically save a report:

```bash
python3 -m workflow.main audit https://example.com
```

Choose the page limit and output file when needed:

```bash
python3 -m workflow.main audit https://example.com \
  --max-pages 5 \
  --output reports/example_audit.json
```

The multi-page workflow prioritizes About, Product, Contact, Factory, OEM/ODM, private-label, and catalog paths. It ignores external-domain links and common non-HTML file types. Only run it against websites you are authorized to inspect.

## Current status

Website Audit Agent v0.3 is implemented with single-page and limited multi-page auditing, page-type-aware rules, and prioritized issues. The remaining specialized agents are placeholders.
