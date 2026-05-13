# Agent Office System

Multi-agent office automation built on **CrewAI**, **OpenAI GPT-4o**, and **Microsoft Graph API (Outlook)**. Managed with **uv** (Python).

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      main.py (CLI)                      │
│         email │ summarize │ scheduler subcommands        │
└────────┬──────────────┬──────────────┬──────────────────┘
         │              │              │
         ▼              ▼              ▼
   EmailCrew     DocSummaryCrew   SchedulerCrew
   (1 agent)     (2 agents,       (APScheduler
                  sequential)      + YAML config)
         │              │
         └──────┬────────┘
                ▼
          CrewAI Agents
     ┌────────────────────────┐
     │ Email Agent            │  tools: OutlookSendTool
     │                        │          OutlookReadTool
     ├────────────────────────┤
     │ Document Summary Agent │  tools: DocReaderTool
     │                        │          OutlookSendTool
     ├────────────────────────┤
     │ Scheduler Agent        │  (orchestration only)
     └────────────────────────┘
                ▼
          Tools (API wrappers)
     ┌────────────────────────────────────────┐
     │ OutlookSendTool   Microsoft Graph API  │
     │ OutlookReadTool   (OAuth2 client cred) │
     │ DocReaderTool     PDF / DOCX / TXT     │
     │ CronTool          APScheduler          │
     └────────────────────────────────────────┘
                ▼
          LLM: OpenAI GPT-4o
```

**Data flow for DocSummaryCrew:**
1. `DocReaderTool` extracts text from the document
2. `Document Summary Agent` produces a structured summary via GPT-4o
3. `Email Agent` formats and sends the summary via Outlook

**Scheduling flow:**
1. `SchedulerCrew` loads `config/schedule.yaml` on startup
2. Registers each job with APScheduler (`coalesce=True`, `max_instances=1`)
3. At each cron tick, dispatches to `EmailCrew` or `DocSummaryCrew`

---

## Key Functions

| Module | Class / Function | What it does |
|---|---|---|
| `crews/email_crew.py` | `EmailCrew.run(to, subject, intent)` | Draft + send an Outlook email from a natural language intent |
| `crews/doc_summary_crew.py` | `DocSummaryCrew.run(doc_path, recipients, notes)` | Read a document, summarize it, and email the summary |
| `crews/scheduler_crew.py` | `SchedulerCrew.start()` | Load `schedule.yaml` and start background cron jobs |
| `tools/outlook_tool.py` | `OutlookSendTool` | Send email via Microsoft Graph API |
| `tools/outlook_tool.py` | `OutlookReadTool` | Read inbox messages via Microsoft Graph API |
| `tools/doc_reader_tool.py` | `DocReaderTool` | Extract text from PDF, DOCX, TXT (local path or URL) |
| `tools/cron_tool.py` | `register_job`, `start_scheduler` | APScheduler wrappers used by `SchedulerCrew` |

---

## How to Run

### 1. Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) installed
- An Azure AD app registration with `Mail.Send` and `Mail.Read` permissions (Graph API)
- An OpenAI API key

### 2. Install

```bash
uv sync
```

### 3. Configure secrets

```bash
cp .env.example .env
# Fill in your keys — see Config section below
```

### 4. Commands

**Send an email**
```bash
uv run agent-office email \
  --to "colleague@company.com" \
  --subject "Project Update" \
  --intent "Write a brief update saying the Q2 report is ready for review"
```

**Summarize a document and email it**
```bash
uv run agent-office summarize \
  --doc "/path/to/report.pdf" \
  --to "manager@company.com,team@company.com" \
  --notes "Focus on the financial section"
```

**Start the cron scheduler** (runs until Ctrl+C)
```bash
uv run agent-office scheduler

# Custom schedule file:
uv run agent-office scheduler --config /path/to/my_schedule.yaml
```

### 5. Run tests

```bash
uv run pytest tests/ -v
```

---

## Config

### `.env` — secrets

```dotenv
# OpenAI
OPENAI_API_KEY=sk-...

# Microsoft Graph API (OAuth2 — client credentials flow)
OUTLOOK_CLIENT_ID=<Azure app client ID>
OUTLOOK_CLIENT_SECRET=<Azure app client secret>
OUTLOOK_TENANT_ID=<Azure AD tenant ID>
OUTLOOK_USER_EMAIL=you@company.com
```

> `.env` is never committed. Add it to `.gitignore`.

### `src/agent_office/config/schedule.yaml` — cron jobs

```yaml
jobs:
  - id: weekly_report_summary
    cron: "0 8 * * MON"        # Every Monday 8 AM
    crew: DocSummaryCrew
    params:
      doc_path: "/reports/weekly.pdf"
      recipients:
        - manager@company.com
      notes: "Highlight any KPI misses"

  - id: daily_inbox_digest
    cron: "0 9 * * *"          # Every day 9 AM
    crew: EmailCrew
    params:
      to: "me@company.com"
      subject: "Daily Inbox Digest"
      task: "Summarize unread emails from the last 24 hours"
```

**Cron format:** `minute hour day month day_of_week`

**Supported crew values:** `EmailCrew`, `DocSummaryCrew`

### Outlook API setup (Azure)

1. Register an app in [Azure Portal](https://portal.azure.com) → **App registrations**
2. Add **Microsoft Graph** API permissions: `Mail.Send`, `Mail.Read` (Application type)
3. Grant admin consent
4. Create a client secret → copy to `.env`
5. Note the **Application (client) ID** and **Directory (tenant) ID** → copy to `.env`
