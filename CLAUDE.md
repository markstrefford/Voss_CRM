# Claude Code Configuration - Voss CRM

## Project Structure

- **Backend**: FastAPI + Google Sheets (`backend/`)
- **Frontend**: React + Vite + shadcn/ui (`frontend/`)
- **MCP Server**: Claude Desktop tools (`backend/mcp_server/`)
- **Telegram Bot**: Integrated into backend (`backend/app/services/telegram_service.py`)

## Code Principles

- **DRY:** Shared backend logic goes in `backend/app/helpers.py`
  - `contact_display_name()` for "First Last" formatting (never inline)
  - `group_follow_ups()` for overdue/today/upcoming/completed filtering
  - `today_str()` for date strings
- **Leverage existing data:** Don't re-fetch data that's already available from parent components
- **Fallbacks:** Missing contacts → "Unknown" (consistent everywhere)
- **Emojis:** Use literal characters (☀️ ✅ ❗) not unicode escapes (\u2600) in Telegram messages
- **Frontend constants:** Shared enums in `frontend/src/constants.ts`
- **Frontend shared components:** Reusable UI in `frontend/src/components/shared/`

## Scheduler

- Runs inside FastAPI via APScheduler (in-process)
- Uses `SchedulerLog` Google Sheet tab for dedup (survives reloads)
- On startup, catches up any missed scheduled jobs for the current day
