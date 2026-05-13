# Multi-Agent Office System — Implementation Plan

## Overview

An autonomous office assistant built on **CrewAI**, powered by **OpenAI** LLMs, managed with **uv** (Python package manager). The system orchestrates multiple specialized agents to handle email automation, document summarization, and scheduled background jobs.

---

## Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| Agent Framework | [CrewAI](https://crewai.com/) | Multi-agent orchestration with roles, tasks, and crews |
| LLM | OpenAI (GPT-4o) | Strong reasoning, tool-use, and summarization |
| Package Manager | uv | Fast, reproducible Python environments |
| Email Client | Outlook (via Microsoft Graph API or `exchangelib`) | Enterprise email integration |
| Scheduling | CrewAI cron / APScheduler | In-process scheduled task execution |
| Config / Secrets | `.env` + `python-dotenv` | Local secret management |

---

## Project Structure

```
agent_office_system/
├── .env                        # API keys and credentials (never committed)
├── .env.example                # Template for required env vars
├── pyproject.toml              # uv project definition
├── uv.lock                     # Locked dependencies
├── doc/
│   └── multi_agent_system_plan.md
├── src/
│   └── agent_office/
│       ├── __init__.py
│       ├── main.py             # Entry point
│       ├── config/
│       │   ├── agents.yaml     # Agent role definitions
│       │   └── tasks.yaml      # Task definitions
│       ├── agents/
│       │   ├── email_agent.py
│       │   ├── doc_agent.py
│       │   └── scheduler_agent.py
│       ├── tools/
│       │   ├── outlook_tool.py      # Send/read Outlook emails
│       │   ├── doc_reader_tool.py   # Read and parse documents
│       │   └── cron_tool.py         # Trigger scheduled jobs
│       └── crews/
│           ├── email_crew.py
│           ├── doc_summary_crew.py
│           └── scheduler_crew.py
└── tests/
```

---

## Environment Variables (`.env`)

```dotenv
# OpenAI
OPENAI_API_KEY=sk-...

# Outlook / Microsoft Graph
OUTLOOK_CLIENT_ID=...
OUTLOOK_CLIENT_SECRET=...
OUTLOOK_TENANT_ID=...
OUTLOOK_USER_EMAIL=you@company.com

# (Alternative: exchangelib basic auth)
OUTLOOK_USERNAME=you@company.com
OUTLOOK_PASSWORD=...
OUTLOOK_SERVER=outlook.office365.com
```

---

## Agents

### 1. Email Agent
- **Role**: Outlook Email Sender
- **Goal**: Compose and send emails via Outlook on behalf of the user
- **Backstory**: An office assistant with full access to the corporate email system
- **Tools**: `OutlookSendTool`, `OutlookReadTool`
- **LLM**: GPT-4o

**Capabilities**:
- Draft email body from a natural language request
- Send to one or multiple recipients
- Attach files if provided
- Read inbox and reply to threads

---

### 2. Document Summary Agent
- **Role**: Document Analyst
- **Goal**: Read documents (PDF, DOCX, TXT), summarize content, and distribute via email
- **Backstory**: A diligent analyst that reads long documents and distills key insights
- **Tools**: `DocReaderTool`, `OutlookSendTool`
- **LLM**: GPT-4o

**Capabilities**:
- Load documents from local path or URL
- Produce structured summaries (executive summary, key points, action items)
- Automatically email the summary to specified recipients

---

### 3. Scheduler Agent
- **Role**: Task Scheduler
- **Goal**: Trigger other agents or crews on a defined cron schedule
- **Backstory**: A reliable automation controller that ensures recurring tasks run on time
- **Tools**: `CronTriggerTool`
- **LLM**: GPT-4o (minimal — mostly orchestration)

**Capabilities**:
- Register cron expressions for recurring tasks
- Trigger `EmailCrew` or `DocSummaryCrew` on schedule
- Log execution status and surface failures

---

## Crews

### EmailCrew
- **Agents**: Email Agent
- **Trigger**: On-demand user request
- **Flow**:
  1. Receive request (recipient, subject, intent)
  2. Agent drafts email
  3. Agent sends via Outlook tool
  4. Return confirmation

### DocSummaryCrew
- **Agents**: Document Summary Agent → Email Agent
- **Trigger**: On-demand or scheduled
- **Flow**:
  1. Receive doc path/URL and recipient list
  2. Doc agent reads and summarizes
  3. Email agent sends summary to recipients
  4. Return confirmation

### SchedulerCrew
- **Agents**: Scheduler Agent
- **Trigger**: On startup; reads cron config
- **Flow**:
  1. Load schedule from `config/schedule.yaml`
  2. Register jobs with APScheduler
  3. On each tick, delegate to the appropriate Crew

---

## Cron Job Configuration

Define recurring tasks in `config/schedule.yaml`:

```yaml
jobs:
  - id: weekly_report_summary
    cron: "0 8 * * MON"          # Every Monday at 8 AM
    crew: DocSummaryCrew
    params:
      doc_path: "/reports/weekly.pdf"
      recipients:
        - manager@company.com

  - id: daily_inbox_digest
    cron: "0 9 * * *"            # Every day at 9 AM
    crew: EmailCrew
    params:
      task: "Summarize unread emails from the last 24 hours and send digest to me"
```

---

## Outlook Integration Options

| Option | Library | Auth Method | Best For |
|---|---|---|---|
| Microsoft Graph API | `msgraph-sdk` / `httpx` | OAuth2 (client credentials or delegated) | Modern, recommended |
| Exchange Web Services | `exchangelib` | Basic auth or NTLM | On-prem Exchange |

**Recommended**: Microsoft Graph API with OAuth2 client credentials flow — credentials stored in `.env`.

---

## Setup Steps (when implementing)

1. `uv init agent_office_system` — bootstrap project
2. `uv add crewai openai python-dotenv exchangelib apscheduler` — add deps
3. Create `.env` from `.env.example` and fill credentials
4. Define agent roles in `config/agents.yaml`
5. Define tasks in `config/tasks.yaml`
6. Implement tools (`OutlookSendTool`, `DocReaderTool`, `CronTriggerTool`)
7. Wire crews in `crews/`
8. Test each crew independently before enabling scheduler
9. Run: `uv run python src/agent_office/main.py`

---

## Key Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Outlook OAuth token expiry | Implement token refresh logic; store refresh token in `.env` |
| LLM hallucinating email content | Add a human-in-the-loop confirmation step for critical emails |
| Cron job overlap (long-running task) | Use APScheduler `coalesce=True` and `max_instances=1` |
| Secrets leaking via logs | Mask credentials in logging; never log `.env` values |
| Doc parsing failures | Validate file type and size before passing to agent; handle errors gracefully |

---

## Open Questions

- [ ] Should email sending require explicit user approval, or fully autonomous?
- [ ] Which Outlook auth flow is available — delegated (user login) or app-only (service account)?
- [ ] Are documents stored locally, on SharePoint, or another source?
- [ ] Should the scheduler persist job state across restarts (e.g., using a SQLite backend)?
