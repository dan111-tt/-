---
name: configurable-information-collector
description: Collect, verify, and organize public information for a user-defined industry, subject scope, date range, and geographic region. Use when the user asks for a targeted news, policy, market, company, technology, or other domain information scan.
---

# Configurable Information Collector

The user defines the research task at run time. Do not assume a fixed industry, source set, topic, date range, country, or region.

## Read the task configuration

If the user attaches a task configuration file, read it and use its fields. Otherwise collect or confirm the required inputs:

- `industry_fields`: one or more industries or fields.
- `collection_scope`: issues, questions, entities, or information types to collect.
- `start_date` and `end_date`: inclusive date range; by default filter on publication date.
- `regions`: countries, regions, markets, or geographic scope.

Optional fields: `keywords`, `source_domains`, `source_urls`, `exclude_terms`, `exclude_drafts`, and `limit` (candidate cap per region). Use `config/task_config.template.json` as the fill-in template. Do not silently replace a value the user supplied. Ask only for required values that are missing or ambiguous.

## Collection workflow

1. Restate the interpreted task briefly: industries, scope, publication-date window, regions, and exclusions. If all required fields are clear, proceed without asking for confirmation.
2. Build a coverage matrix across every requested region and each industry/scope item. Use user-provided domains and URLs first, then search additional public sources relevant to the task. Use local-language queries when useful.
3. If the `researchNews` API action is configured, map the task fields to `regions`, `industry_fields`, `collection_scope`, `start_date`, `end_date`, `keywords`, `source_domains`, `source_urls`, `exclude_terms`, and `limit`. Otherwise use the available search tools and state any source or coverage limits.
4. Inspect per-region query logs and coverage results. Distinguish “no candidate found” from “no search run,” “search failed,” and “no source configured.” Do not claim that an empty result proves nothing happened in that region.
5. Verify useful candidates at their original source. Record publication date separately from event, adoption, and effective dates. If the publication date is absent, conflicting, or outside the requested range, mark it for review or exclude it according to the task's date basis.
6. Apply `exclude_terms` and other user-defined filters. Exclude drafts only when requested. Treat automated labels as signals to verify, not as facts.
7. Remove duplicates, prioritize primary sources, and avoid excessive keyword filtering. Keep information that clearly matches the user's stated purpose even when wording differs.

## Candidate output

Group by region and industry or scope. For each item, include title, source/publisher, publication date and evidence, concise factual summary, relevance to the user's scope, source link, source quality, and unresolved checks. Label facts, analysis, and uncertainty separately. Keep links adjacent to the claims they support.

Report the coverage attempted, gaps, and search failures. Never claim exhaustive coverage unless the method supports that claim. Provide a sourced candidate list first; create a report or other deliverable only in the format requested by the user.

## Source and access limits

Use publicly accessible pages and user-provided links. Do not bypass logins, paywalls, anti-bot controls, or access restrictions. Treat social posts and other secondary sources as leads when a primary source is available. Do not expose API keys or other secrets from configuration files.

## Optional API service

The `app/` service provides candidate collection and report endpoints described in `openapi.yaml`. It requires deployment; automated web discovery also requires `TAVILY_API_KEY`. The skill and service do not run simply because this repository is uploaded to GitHub. See `README.md` for setup and `config/task_config.template.json` for the task input format.
