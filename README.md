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
     │ GmailSendTool     Gmail SMTP           │
     │ GmailReadTool     Gmail IMAP           │
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
| `tools/gmail_tool.py` | `GmailSendTool` | Send email via Gmail SMTP |
| `tools/gmail_tool.py` | `GmailReadTool` | Read inbox messages via Gmail IMAP |
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

**Attatch files with Email**
```bash
# Single attachment
uv run agent-office email \
  --to "xxx@hotmail.com" \
  --subject "Q2 Report" \
  --intent "Q2 report is ready for review" \
  --attach "/Users/jliu/reports/q2.pdf"


# Multiple attachments
uv run agent-office email \
  --to "xxx@hotmail.com" \
  --subject "Q2 Report" \
  --intent "Q2 report is ready for review" \
  --attach "/Users/jliu/reports/q2.pdf" \
  --attach "/Users/jliu/reports/appendix.xlsx"
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

# Gmail (SMTP + IMAP via App Password)
GMAIL_ADDRESS=you@gmail.com
GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
```

> `.env` is never committed. Add it to `.gitignore`.

### Gmail App Password setup

1. Enable **2-Step Verification** on your Google account
2. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Create an App Password (select app: **Mail**, device: **Other**)
4. Copy the 16-character password into `.env` as `GMAIL_APP_PASSWORD`

```
The only setup needed: enable 2-Step Verification on your Google account, then generate an App Password at
myaccount.google.com/apppasswords — no Azure portal, no OAuth2 consent flow.
```


> No OAuth2 flow or API console required — App Password works with standard SMTP/IMAP.

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

