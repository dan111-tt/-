# Configurable Information Collector

A reusable skill and optional API service for collecting public information based on the user's **industry, collection scope, date range, and region**. It has no fixed industry or geography. Each run can use a short JSON task profile or values from the user's request.

## Repository structure

```text
SKILL.md                       Generic agent skill instructions
GPT_INSTRUCTIONS.md            Instructions for a Custom GPT using the API action
config/task_config.template.json  Fill-in task profile
config/sources.json            Optional seed source catalog
config/search_terms.json       Search phrase catalog retained for domain-specific profiles
app/                           FastAPI collection and report service
openapi.yaml                   API Action schema
tests/                         Search-rule and regression tests
```

## Set up a collection task

Copy `config/task_config.template.json` to `task_config.json`, then fill in the four required task dimensions:

- `industry_fields`: industries or fields, such as telecommunications or renewable energy.
- `collection_scope`: topics, questions, entities, or types of information to collect.
- `start_date` / `end_date`: inclusive dates; the initial implementation filters on publication date.
- `regions`: countries, regions, markets, or geographic scope.

Optionally set `keywords`, source hostnames in `source_domains`, seed pages in `source_urls`, `exclude_terms`, `exclude_drafts`, and `limit` (maximum candidates per region). Upload `task_config.json` alongside the skill or paste its values in the request. The assistant maps these values to the action API. For a direct API request, pass the same fields as JSON in `POST /research`.

Example configuration:

```json
{
  "task_name": "新能源政策动态",
  "industry_fields": ["新能源", "储能"],
  "collection_scope": ["正式政策", "监管动态", "补贴规则"],
  "start_date": "2026-09-01",
  "end_date": "2026-09-30",
  "regions": ["日本", "韩国"],
  "keywords": ["battery storage", "renewable energy policy"],
  "source_domains": [],
  "source_urls": [],
  "exclude_terms": ["job posting", "event announcement"],
  "exclude_drafts": true,
  "limit": 10
}
```

## Run the optional API service

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
```

Set `API_KEY` and `TAVILY_API_KEY`, then run:

```bash
uvicorn app.main:app --reload
```

Open `/docs` to try the API. Automated search requires Tavily. Without a Tavily key, `/research` can process user-provided source URLs and reports that network search was not run. `source_domains` restricts search results to the selected hosts; `source_urls` are fetched as seed pages and do not restrict broader discovery. If no domains are supplied, the service searches public HTTPS pages and checks that destinations resolve to public IP addresses. It does not log in or bypass anti-bot restrictions.

The API returns candidates and per-region query/coverage logs. It does not certify complete coverage or legal conclusions. Configure `PUBLIC_BASE_URL` when serving downloadable reports.

## Connect to a ChatGPT Custom GPT

1. Deploy the API service to a public HTTPS host and set `API_KEY`, `TAVILY_API_KEY`, and `PUBLIC_BASE_URL`.
2. Replace `YOUR-PUBLIC-HOST` in `openapi.yaml` with the deployed host.
3. In GPT Builder, add the OpenAPI schema under **Configure → Actions** and configure API-key authentication with the `X-API-Key` header.
4. Add the instructions from `GPT_INSTRUCTIONS.md`.

Uploading this repository to GitHub stores the skill and code; it does not deploy or run the collector.

## Verify

```bash
python -m unittest discover -s tests -v
python -m compileall -q app
```
