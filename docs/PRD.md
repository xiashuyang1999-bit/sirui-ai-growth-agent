# Product Requirements Document

## Product

SIRUI AI Website Growth Agent 1.0

## Objective

Build an AI-assisted system that analyzes `https://www.siruitool.com` and recommends improvements for overseas B2B customer acquisition.

## Current scope

- Website Audit Agent v0.4 performs read-only, page-type-aware website and technical SEO checks.
- SEO Agent v0.1 converts audit evidence into a prioritized backlog and page-level SEO plans.
- Developer Agent v0.1 converts the backlog into implementation steps, inputs, acceptance criteria, risks, rollback plans, and approval gates.
- Content Agent v0.1 converts page plans into evidence-led content briefs, required input lists, CTA drafts, editorial checks, and publication gates.
- Growth Workflow v0.1 packages SEO, developer, content, approval, next-action, and measurement outputs from an existing audit report.
- Inquiry Qualification Agent v0.1 scores local buyer inquiries, identifies missing quotation inputs, and prepares unsent response drafts for sales approval.
- Sales Pipeline Report Agent v0.1 summarizes explicit lead, inquiry, outreach, reply, sample, quotation, order, blocker, and next-action records without modifying the source.
- Follow-up Agent v0.1 prepares approval-gated Day 3, 7, 14, 21, and final email drafts for eligible A/B records without sending or scheduling them.
- Analytics & Conversion Report Agent v0.1 calculates traffic, search, inquiry, qualification, sample, quotation, and order progression from approved local normalized exports without accessing external accounts.

## Success measures

- Audit findings remain traceable to a URL and evidence.
- Unknown keyword metrics and business facts are never invented.
- Development tasks can be assigned and independently accepted or rejected.
- Production changes remain disabled until explicit human approval.

## Guardrail

The system must not modify the production website without explicit human approval.
