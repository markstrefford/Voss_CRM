# Voss CRM — Architecture & Information Flow

## System Overview

```
┌─────────────┐     ┌──────────────┐     ┌───────────────┐
│  React SPA  │────▶│  FastAPI      │────▶│ Google Sheets │
│  (Vite)     │◀────│  Backend      │◀────│ (Data Layer)  │
└─────────────┘     └──────┬───────┘     └───────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────────┐
        │ Telegram │ │ Scheduler│ │  MCP Server  │
        │   Bot    │ │(APSched) │ │(Claude Tools)│
        └──────────┘ └──────────┘ └──────────────┘
```

## Data Layer

All data lives in Google Sheets tabs, accessed via `SheetService` (generic CRUD with 30s TTL cache):

| Tab            | Purpose                        | Key Columns                              |
|----------------|--------------------------------|------------------------------------------|
| Contacts       | People in the CRM              | id, first_name, last_name, segment, ...  |
| Companies      | Organisations                  | id, name, industry, ...                  |
| Deals          | Pipeline items                 | id, contact_id, stage, value, ...        |
| Interactions   | Timeline events                | id, contact_id, type, direction, ...     |
| FollowUps      | Scheduled tasks                | id, contact_id, due_date, status, ...    |
| Users          | App users + Telegram chat IDs  | id, username, telegram_chat_id           |
| SchedulerLog   | Job dedup (survives reloads)   | id, job_name, last_run_date              |

## Shared Helpers (`backend/app/helpers.py`)

Three functions used everywhere to avoid duplication:

```
contact_display_name(contact_dict) → "First Last" | "Unknown"
group_follow_ups(follow_ups)       → {overdue, today, upcoming, completed}
today_str()                        → "YYYY-MM-DD" (UTC)
```

### Consumer Map

| Consumer                      | display_name | group_follow_ups | today_str |
|-------------------------------|:---:|:---:|:---:|
| scheduler.py                  | ✓   | ✓   | ✓   |
| telegram_service.py           | ✓   | ✓   | ✓   |
| routers/dashboard.py          | ✓   |     | ✓   |
| mcp_server/helpers.py         | ✓   |     |     |
| mcp_server/tools/follow_ups.py|    | ✓   | ✓   |
| mcp_server/tools/dashboard.py |    |     | ✓   |

## Request Flows

### 1. Frontend → API → Sheets

```
Browser                    FastAPI                   Google Sheets
  │                          │                           │
  │  GET /api/dashboard/     │                           │
  │  action-feed             │                           │
  │─────────────────────────▶│                           │
  │                          │  get_all_records()        │
  │                          │  (Contacts, Deals, ...)   │
  │                          │──────────────────────────▶│
  │                          │◀──────────────────────────│
  │                          │                           │
  │                          │  contact_display_name()   │
  │                          │  group_follow_ups()       │
  │                          │  (shared helpers)         │
  │                          │                           │
  │  JSON response           │                           │
  │◀─────────────────────────│                           │
```

### 2. Telegram Bot Commands

```
Telegram User              Telegram Bot              Google Sheets
  │                          │                           │
  │  /today                  │                           │
  │─────────────────────────▶│                           │
  │                          │  follow_ups_sheet         │
  │                          │  .get_all(pending)        │
  │                          │──────────────────────────▶│
  │                          │◀──────────────────────────│
  │                          │                           │
  │                          │  group_follow_ups()       │
  │                          │  contact_display_name()   │
  │                          │                           │
  │  Formatted message       │                           │
  │◀─────────────────────────│                           │
```

### 3. Scheduler Jobs (with dedup)

```
APScheduler                 Scheduler Logic           Google Sheets
  │                          │                           │
  │  cron trigger            │                           │
  │  (09:30 / 18:00)        │                           │
  │─────────────────────────▶│                           │
  │                          │  _already_ran_today()     │
  │                          │  (check SchedulerLog)     │
  │                          │──────────────────────────▶│
  │                          │◀──────────────────────────│
  │                          │                           │
  │                     [if not run]                     │
  │                          │  _mark_ran()              │
  │                          │──────────────────────────▶│
  │                          │                           │
  │                          │  fetch follow-ups/deals   │
  │                          │──────────────────────────▶│
  │                          │◀──────────────────────────│
  │                          │                           │
  │                          │  group_follow_ups()       │
  │                          │  contact_display_name()   │
  │                          │                           │
  │                          │  send_message() ──▶ Telegram
  │                          │                           │
```

**Startup catch-up**: When uvicorn starts, `_catch_up_missed_jobs()` checks the clock and calls `morning_digest()` / `stale_deal_alerts()`. The SchedulerLog dedup ensures these are no-ops if they already ran today.

### 4. MCP Server (Claude Desktop)

```
Claude Desktop              MCP Server               Google Sheets
  │                          │                           │
  │  get_follow_ups()        │                           │
  │─────────────────────────▶│                           │
  │                          │  follow_ups_sheet         │
  │                          │  .get_all()               │
  │                          │──────────────────────────▶│
  │                          │◀──────────────────────────│
  │                          │                           │
  │                          │  group_follow_ups()       │
  │                          │  resolve_contact_name()   │
  │                          │  → contact_display_name() │
  │                          │                           │
  │  Markdown response       │                           │
  │◀─────────────────────────│                           │
```

## Frontend Component Hierarchy

```
App
├── AppShell (layout)
│   ├── DashboardPage          → GET /api/dashboard/action-feed
│   ├── ContactsPage           → uses SEGMENTS, ENGAGEMENT_STAGES, INBOUND_CHANNELS from constants.ts
│   │   └── ContactFormDialog
│   ├── ContactDetailPage      → uses shared FollowUpSection, SnoozeDialog, constants
│   │   ├── InteractionFormDialog
│   │   ├── FollowUpFormDialog
│   │   ├── FollowUpSection    (from @/components/shared/)
│   │   └── SnoozeDialog       (from @/components/shared/)
│   ├── FollowUpsPage          → uses shared FollowUpSection, SnoozeDialog
│   │   ├── FollowUpSection    (from @/components/shared/)
│   │   └── SnoozeDialog       (from @/components/shared/)
│   ├── DealsPage
│   ├── PipelinePage
│   └── CompaniesPage
```

## Shared Frontend Components

| Component       | Location                                  | Used By                          |
|-----------------|-------------------------------------------|----------------------------------|
| FollowUpSection | `frontend/src/components/shared/`         | FollowUpsPage, ContactDetailPage |
| SnoozeDialog    | `frontend/src/components/shared/`         | FollowUpsPage, ContactDetailPage |
| SearchBar       | `frontend/src/components/shared/`         | ContactsPage                     |
| ConfirmDialog   | `frontend/src/components/shared/`         | ContactsPage                     |
| TagInput        | `frontend/src/components/shared/`         | ContactDetailPage                |

## Constants (`frontend/src/constants.ts`)

```ts
SEGMENTS           = ['', 'signal_strata', 'consulting', 'pe', 'other']
ENGAGEMENT_STAGES  = ['new', 'nurturing', 'active', 'client', 'churned']
INBOUND_CHANNELS   = ['', 'linkedin', 'referral', 'conference', 'cold_outbound', 'website', 'other']
```

Used by: ContactsPage, ContactDetailPage (both form dialogs).
