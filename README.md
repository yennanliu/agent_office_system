# Agent Office System

Multi-agent office automation built on **CrewAI**, **OpenAI GPT-4o**, and **Gmail**. Managed with **uv** (Python). All runs are tracked in SQLite and visible in a Streamlit dashboard.


<p align="center"><img src ="./doc/pic/demo_3.png" ></p>
<p align="center"><img src ="./doc/pic/demo_2.png" ></p>


---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              main.py (CLI)                                  │
│  email │ summarize │ stock │ inbox-summary │ scheduler │ ui  subcommands    │
└───┬──────────┬──────────┬──────────┬───────────┬────────────┬───────────────┘
    │          │          │          │           │            │
    ▼          ▼          ▼          ▼           ▼            ▼
EmailCrew  DocSummary  StockSummary  Inbox    Scheduler   Streamlit
           Crew        Crew          Summary  Crew        Dashboard
    │          │          │          Crew     │
    └──────┬───┘          │            │  APScheduler
           │              │            │  + schedule.yaml
           ▼              ▼            ▼
     CrewAI Agents
┌──────────────────────────────────────────────────────┐
│ Gmail Email Assistant  │ GmailSendTool               │
│                        │ GmailReadTool               │
├──────────────────────────────────────────────────────┤
│ Document Analyst       │ DocReaderTool               │
│                        │ GmailSendTool               │
├──────────────────────────────────────────────────────┤
│ US Stock Analyst       │ StockDataTool (yfinance)    │
│                        │ GmailSendTool               │
├──────────────────────────────────────────────────────┤
│ Inbox Summarizer       │ GmailReadTool               │
│                        │ ReportSaverTool             │
└──────────────────────────────────────────────────────┘
           │
           ▼
     LLM: OpenAI GPT-4o
           │
           ▼
┌──────────────────────────────────────────────────────┐
│ SQLite  runs.db  (token cost, status, timing)        │
└──────────────────────────────────────────────────────┘
```

**EmailCrew** — agent drafts body from natural language intent, sends via Gmail SMTP.

**DocSummaryCrew** — doc agent reads PDF/DOCX/TXT → structured summary → email agent sends it.

**StockSummaryCrew** — stock agent fetches live data via yfinance, produces Buy/Hold/Sell analysis per ticker → email agent sends the investment summary.

**InboxSummaryCrew** — inbox summarizer agent reads recent Gmail messages, clusters them by topic, flags action items, saves a plain-text report to `output/`, and optionally emails the report.

**SchedulerCrew** — loads `config/schedule.yaml` on startup, registers APScheduler cron jobs (`coalesce=True`, `max_instances=1`), dispatches to any crew on each tick.

**Run tracking** — every `crew.kickoff()` is wrapped by `tracker.py`: records name, job type, agents, status, token counts, and estimated GPT-4o cost into `runs.db`.

---

## Key Functions

| Module | Class / Function | What it does |
|---|---|---|
| `crews/email_crew.py` | `EmailCrew.run(to, subject, intent, attachments?)` | Draft + send a Gmail email, optionally with file attachments |
| `crews/doc_summary_crew.py` | `DocSummaryCrew.run(doc_path, recipients, notes?)` | Summarize a document and email the result |
| `crews/stock_summary_crew.py` | `StockSummaryCrew.run(tickers, recipients)` | Analyze US stocks and email an investment summary |
| `crews/inbox_summary_crew.py` | `InboxSummaryCrew.run(recipients?, output_dir?, max_emails?)` | Read recent Gmail messages, save a structured summary to `output/`, optionally email it |
| `crews/scheduler_crew.py` | `SchedulerCrew.start()` | Load `schedule.yaml` and start background cron jobs |
| `tools/gmail_tool.py` | `GmailSendTool` | Send email via Gmail SMTP (supports attachments) |
| `tools/gmail_tool.py` | `GmailReadTool` | Read inbox messages via Gmail IMAP |
| `tools/stock_tool.py` | `StockDataTool` | Fetch live price, valuation, growth, analyst data via yfinance |
| `tools/doc_reader_tool.py` | `DocReaderTool` | Extract text from PDF, DOCX, TXT (local path or URL) |
| `tools/report_saver_tool.py` | `ReportSaverTool` | Save a text report to a local `.txt` file with an auto-timestamped filename |
| `tools/cron_tool.py` | `register_job`, `start_scheduler` | APScheduler wrappers used by `SchedulerCrew` |
| `db/database.py` | `init_db`, `insert_run`, `update_run`, `get_all_runs` | SQLite CRUD for run tracking |
| `db/tracker.py` | `track_crew_run(name, job_type, agents, crew)` | Wrap any crew run with automatic DB tracking |
| `ui/dashboard.py` | Streamlit app | Live dashboard: metrics, filterable run table, token/cost charts |

---

## How to Run

### 1. Prerequisites

- Python 3.11–3.13 (3.14 not yet supported by chromadb)
- [uv](https://docs.astral.sh/uv/) installed
- OpenAI API key
- Gmail account with an App Password (see Config section)

### 2. Install

```bash
uv sync
```

### 3. Configure secrets

```bash
cp .env.example .env
# Fill in OPENAI_API_KEY, GMAIL_ADDRESS, GMAIL_APP_PASSWORD
```

### 4. Commands

**Send an email**
```bash
uv run agent-office email \
  --to "colleague@gmail.com" \
  --subject "Project Update" \
  --intent "Write a brief update saying the Q2 report is ready for review"
```

**Send an email with attachments**
```bash
# Single file
uv run agent-office email \
  --to "colleague@gmail.com" \
  --subject "Q2 Report" \
  --intent "Q2 report is ready for review" \
  --attach "/path/to/q2.pdf"

# Multiple files (repeat --attach)
uv run agent-office email \
  --to "colleague@gmail.com" \
  --subject "Q2 Report" \
  --intent "Q2 report is ready for review" \
  --attach "/path/to/q2.pdf" \
  --attach "/path/to/appendix.xlsx"
```

**Summarize a document and email it**
```bash
uv run agent-office summarize \
  --doc "/path/to/report.pdf" \
  --to "manager@gmail.com,team@gmail.com" \
  --notes "Focus on the financial section"
```

**Analyze US stocks and email an investment summary**
```bash
# Single ticker
uv run agent-office stock \
  --ticker AAPL \
  --to "investor@gmail.com"

# Multiple tickers
uv run agent-office stock \
  --ticker AAPL --ticker NVDA --ticker MSFT \
  --to "investor@gmail.com"
```

**Read and summarize recent Gmail inbox messages**
```bash
# Save report to output/ (default) — no email sent
uv run agent-office inbox-summary

# Read 20 emails, save to a custom folder
uv run agent-office inbox-summary --max-emails 20 --output-dir ./reports

# Save locally AND email the report
uv run agent-office inbox-summary --to "you@gmail.com"

# All options combined
uv run agent-office inbox-summary \
  --to "you@gmail.com,team@gmail.com" \
  --max-emails 15 \
  --output-dir ./reports
```

The report is always saved as a `.txt` file under `--output-dir` with a timestamped filename (`inbox_summary_YYYYMMDD_HHMMSS.txt`). The structured report contains:

1. **Overview** — total emails, date range, top senders
2. **By-Topic Groups** — emails clustered into themes (Finance, HR, Engineering, etc.)
3. **Action Items** — emails requiring a reply or follow-up
4. **FYI Only** — informational emails with no action needed

**Start the cron scheduler** (runs until Ctrl+C)
```bash
uv run agent-office scheduler

# Custom schedule config:
uv run agent-office scheduler --config /path/to/my_schedule.yaml
```

**Launch the run-tracking dashboard**
```bash
uv run agent-office ui
# Opens Streamlit at http://localhost:8501
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
GMAIL_APP_PASSWORD=xxxxxxxxxxxxxxxx   # 16 chars, no spaces
```

> `.env` is never committed. Add it to `.gitignore`.

### Gmail App Password setup

1. Enable **2-Step Verification** on your Google account
2. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Create an App Password — Google shows it as `xxxx xxxx xxxx xxxx`
4. Copy into `.env` **without spaces**: `GMAIL_APP_PASSWORD=xxxxxxxxxxxxxxxx`

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
        - manager@gmail.com
      notes: "Highlight any KPI misses"

  - id: daily_stock_digest
    cron: "0 7 * * MON-FRI"    # Weekdays at 7 AM
    crew: StockSummaryCrew
    params:
      tickers:
        - AAPL
        - NVDA
        - MSFT
      recipients:
        - investor@gmail.com

  - id: daily_inbox_digest
    cron: "0 9 * * *"          # Every day at 9 AM
    crew: EmailCrew
    params:
      to: "me@gmail.com"
      subject: "Daily Inbox Digest"
      task: "Summarize unread emails from the last 24 hours"
```

**Cron format:** `minute hour day month day_of_week`

**Supported crew values:** `EmailCrew`, `DocSummaryCrew`, `StockSummaryCrew`, `InboxSummaryCrew`

### Run database

All runs are saved to `runs.db` at the project root. Each record stores:

| Field | Description |
|---|---|
| `name` | Human-readable run label |
| `job_type` | Crew class name |
| `agents` | Comma-separated agent roles |
| `started_at` / `finished_at` | UTC timestamps |
| `status` | `running` / `success` / `failed` |
| `total_tokens` | Combined prompt + completion tokens |
| `estimated_cost_usd` | Calculated at GPT-4o rates ($2.50/1M input, $10/1M output) |
| `error` | Exception message if failed |
