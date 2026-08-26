# SIRUI AI Website Growth Agent 1.0

SIRUI AI Website Growth Agent is a multi-agent system for analyzing and improving [siruitool.com](https://www.siruitool.com) as an overseas B2B customer-acquisition channel. It acts as an evidence-based growth team beside the website: it inspects positioning, SEO, product discovery, and inquiry conversion, then turns findings into prioritized work for marketing, sales, and development.

The current system combines Website Audit Agent v0.4 with SEO, Developer, and Content Agents v0.1. The audit agent provides a read-only, page-type-aware audit foundation. The SEO agent turns verified evidence into a technical backlog and page plans. The developer agent creates approval-gated implementation packages. The content agent creates page-specific, evidence-led content briefs and CTA drafts. Nothing in this version changes the production website.

## Current capabilities

- Validate and fetch an authorized HTTP/HTTPS page without changing it.
- Discover and prioritize same-domain About, Product, Contact, Factory, OEM/ODM, private-label, and catalog paths.
- Limit the crawl to 1-25 pages and ignore external domains and common non-HTML files.
- Check page-specific positioning, SEO basics, product discovery, and B2B conversion routes.
- Detect titles, meta descriptions, canonical links, language, H1 headings, forms, product links, and direct contact links.
- Inspect HTTP responses, robots.txt, XML sitemaps, audited-page sitemap coverage, JSON-LD schema, and canonical hostname consistency.
- Return page-level findings plus a site-wide prioritized issue list.
- Assign each issue evidence, severity, P1/P2/P3 priority, and a recommended action.
- Save a reusable JSON report for review, comparison, or downstream workflows.
- Convert audit findings into an SEO backlog while preserving URL, evidence, severity, and P1/P2/P3 priority.
- Create an SEO plan for every audited page, including target audience, search intent, seed keyword themes, and metadata guidance.
- Mark unavailable search volume, difficulty, and ranking data as `Needs verification` instead of inventing metrics.
- Convert SEO issues into specialized Schema, Canonical, hostname, or technical-review implementation tasks.
- Require staging review, regression checks, named production approvers, and a rollback plan for every developer task.
- Generate page-type-specific content briefs for home, product index, product detail, factory, OEM/ODM, and inquiry pages.
- Define content sections, required verified inputs, keyword assignments, CTA drafts, editorial checks, and publication gates.

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

## SEO plan usage

Generate a structured SEO plan from an existing audit report:

```bash
python3 -m workflow.main seo-plan reports/sirui_official_audit_v0_4.json \
  --output reports/sirui_seo_plan_v0_1.json
```

Review the output fields:

- `technical_backlog` — development and SEO tasks derived from verified audit issues.
- `page_plans` — one plan per audited page with search intent, audiences, keyword themes, and metadata guidance.
- `guardrails` — facts and metrics that require verification and changes that require human approval.

The keyword themes are planning seeds only. Validate search demand, competition, and current rankings with an approved SEO data source before publishing metadata or content.

## Developer plan usage

Generate a developer implementation package from an SEO plan:

```bash
python3 -m workflow.main dev-plan reports/sirui_seo_plan_v0_1.json \
  --output reports/sirui_developer_plan_v0_1.json
```

Review these output fields before assigning work:

- `implementation_tasks` — platform-neutral steps, inputs, acceptance criteria, risk, and rollback per task.
- `release_policy` — staging-first policy and the production approval state.
- `global_definition_of_done` — shared checks required before any task can be considered complete.

The developer plan is a proposal, not permission to change production. The website owner, SEO reviewer, and technical owner must confirm platform details and explicitly approve a release.

## Content plan usage

Generate approval-gated content briefs from an SEO plan:

```bash
python3 -m workflow.main content-plan reports/sirui_seo_plan_v0_1.json \
  --output reports/sirui_content_plan_v0_1.json
```

Review these fields before drafting or publishing page copy:

- `content_briefs` — one page-specific brief with goal, buyer, keywords, sections, evidence needs, CTA, and editorial checks.
- `content_policy` — the default brief-only state and production publication restriction.
- `global_definition_of_done` — fact, keyword, conversion, privacy, and approval requirements.

The CTA text is an approval-ready draft. Product specifications, certifications, pricing, MOQ, capacity, lead times, customization, and other claims must be verified before the copy is written or published.

## Unified growth package usage

Build the SEO, developer, content, and measurement package in one offline command from an existing audit report:

```bash
python3 -m workflow.main growth-plan reports/sirui_official_audit_v0_4.json \
  --output-dir reports/sirui_growth_package_v0_1
```

The package contains:

- `manifest.json` — source versions, artifact list, combined summary, approval state, next actions, and measurement framework.
- `seo_plan.json` — technical backlog and page-level SEO plans.
- `developer_plan.json` — implementation tasks, risks, acceptance criteria, and rollback plans.
- `content_plan.json` — page-specific content briefs and publication gates.

The measurement framework defines website sessions, organic clicks, inquiry submissions, qualified inquiries, sample projects, quotations, and orders. It does not invent current values; every unconnected source remains `Needs verification`.

## Inquiry qualification usage

Create a private inquiry file from the tracked blank template:

```bash
mkdir -p data/inquiries
cp data/inquiry_template.json data/inquiries/new_inquiry.json
```

Fill the local JSON with the information actually supplied by the buyer. Set `company_verified` to `true` only after a human or approved data source verifies the company. Then qualify it:

```bash
python3 -m workflow.main qualify-inquiry data/inquiries/new_inquiry.json
```

The private result is saved under `reports/inquiries/` and contains:

- A/B/C score, evidence, status, and next action.
- Missing identity and quotation fields.
- Up to five clarification questions.
- Quotation preparation checklist.
- English response draft requiring sales approval.

The inquiry input and output directories are ignored by Git because they may contain personal data. The agent never sends the draft, writes to a CRM, or issues a quotation.

## Sales pipeline report usage

Create a private weekly pipeline file from the tracked schema template:

```bash
mkdir -p data/pipeline
cp data/pipeline_template.json data/pipeline/weekly_pipeline.json
```

Set the reporting period and add records based only on confirmed sales activity. Then generate the report:

```bash
python3 -m workflow.main pipeline-report data/pipeline/weekly_pipeline.json
```

The private report is saved under `reports/pipeline/` and summarizes:

- New leads or inquiries and A/B/C counts.
- Outreach drafted and sent, replies, qualified inquiries, samples, quotations, and orders.
- Current sales stages, A/B priority queue, blockers, owners, and next actions.
- Missing record IDs or grades and other data-quality issues.

Milestones are counted only when their input value is explicitly `true`. A record at the `quotation` stage is not counted as an issued quotation unless `quotation_issued` is also `true`. Pipeline input and output directories are ignored by Git, and the agent never modifies the source records or writes to a CRM.

## Follow-up plan usage

Create a private follow-up input from the tracked template:

```bash
mkdir -p data/followups
cp data/followup_template.json data/followups/lead_001.json
```

Add the approved A/B grade, current stage, start date, company, contact, market, and product. Use a company-fit observation only when it is verified, and set `fit_observation_verified` accordingly. Then generate the sequence:

```bash
python3 -m workflow.main followup-plan data/followups/lead_001.json
```

Eligible A/B records receive unsent drafts for Day 3, 7, 14, 21, and the final close-the-loop message. The first question adapts to the current stage, each email stays under 120 words, and every draft requires sales-owner approval. C-grade or unverified-grade records do not receive a proactive sequence.

Follow-up inputs and outputs are ignored by Git. The agent does not send, schedule, or update messages and does not write to a CRM. The sequence must stop if the buyer replies, opts out, or the opportunity closes.

## Analytics and conversion report usage

Create a private normalized metrics file from the tracked template:

```bash
mkdir -p data/analytics
cp data/analytics_template.json data/analytics/monthly_metrics.json
```

Fill it only with values from approved GA4, Google Search Console, form, and sales-pipeline exports. Keep unavailable values as `null`. Set `sales.attribution_scope` to `website_only` only when the sales metrics are genuinely attributed to website inquiries. Then run:

```bash
python3 -m workflow.main analytics-report data/analytics/monthly_metrics.json
```

The report calculates engagement, search click-through, website inquiry, qualified-inquiry, sample, quotation, and order progression rates. Missing values remain `Needs verification`; an empty dataset is marked `insufficient_data`, not `pass`. Suspicious aggregate relationships are flagged for human review.

Analytics inputs and outputs are ignored by Git. This version reads local normalized exports only and never logs in to, modifies, or uploads data to GA4, Search Console, a CRM, or another external account.

## Current status

Website Audit Agent v0.4 plus SEO, Developer, Content, Inquiry Qualification, Sales Pipeline Report, Follow-up, local Analytics Report, and unified Growth Workflow v0.1 are implemented. The next phase is export adapters and recurring growth operations.
