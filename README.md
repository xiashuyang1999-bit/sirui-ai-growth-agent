# SIRUI AI Website Growth Agent 1.0

SIRUI AI Website Growth Agent is a planned multi-agent system for analyzing and improving [siruitool.com](https://www.siruitool.com) as an overseas B2B customer-acquisition channel.

This repository currently contains only the initial project scaffold. AI integrations, website analysis, recommendations, approval flows, and publishing capabilities will be added in later phases. Nothing in this version changes the production website.

## Planned architecture

- `agents/` — specialized website audit, SEO, content, and developer agents.
- `prompts/` — prompt templates associated with the specialized agents and Codex workflows.
- `workflow/` — orchestration entry points for coordinating agent tasks.
- `docs/` — product requirements and delivery roadmap.
- `data/` — local input datasets and intermediate analysis data.
- `reports/` — generated audit and growth reports.

The intended workflow is to collect approved website inputs, analyze technical and commercial opportunities, generate recommendations, and produce reviewable reports. Any production change must remain a separate, explicitly approved action.

## Current status

Project structure initialized; implementation has not started.

