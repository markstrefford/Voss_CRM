# VOSS → Modal Migration + North Integration

**Date:** 20 March 2026
**Status:** Spec for Claude Code

---

## Current State

- VOSS runs locally on Mark's Mac
- Telegram bot polls constantly, burns CPU/battery
- MCP works on desktop, drops on mobile
- VOSS API only accessible when Mac is running
- North needs to call VOSS API at 7:30am regardless of whether Mac is on

---

## Target State

- VOSS API hosted on Modal (serverless, scales to zero automatically)
- VOSS repo stays public/open source — the value is in the data and relationships, not the code
- VOSS repo includes CHANGELOG.md — release notes for every meaningful change
- Google Sheets backend migrated from personal Google account to reimagined.industries company workspace
- North (NanoClaw) is the single Telegram front door — handles briefings AND VOSS interactions
- North calls VOSS via MCP/API endpoints on Modal
- VOSS Telegram bot code kept in repo but not deployed (fallback only)
- MCP still works from Claude Code on Mac (points at Modal URL instead of localhost)

---

## Why Modal

- Pay per use, scales to zero automatically when not called
- Spins up in seconds, shuts down after ~5 minutes of inactivity
- Mark already has Modal startup credits deposited
- No Docker management, no always-on Render service
- Python-native, same stack as VOSS
- `modal deploy` gives stable persistent URLs (unlike `modal run` which generates ephemeral URLs per invocation — that's why CONSTELLATION runs look different each time)

---

## What Changes

### 1. VOSS API → Modal Web Endpoints

**Current:** Flask/FastAPI app running on Mac (localhost)
**Target:** Same logic deployed as Modal web endpoints with stable URLs

```python
# modal_app.py
import modal

app = modal.App("voss-crm")

# Google Sheets credentials stored as Modal secret
sheets_secret = modal.Secret.from_name("google-sheets-credentials")

@app.function(secrets=[sheets_secret])
@modal.web_endpoint()
def search_contacts(query: str):
    # Same logic as current VOSS API
    # Reads from Google Sheets
    # Returns JSON
    pass

@app.function(secrets=[sheets_secret])
@modal.web_endpoint()
def get_follow_ups(status: str, due_date: str = None, overdue: bool = False):
    pass

@app.function(secrets=[sheets_secret])
@modal.web_endpoint()
def log_interaction(contact_id: str, data: dict):
    pass

@app.function(secrets=[sheets_secret])
@modal.web_endpoint()
def get_contact_details(contact_id: str):
    pass
```

**Key points:**
- `modal deploy` (not `modal run`) gives persistent URLs: `https://your-username--voss-crm-search-contacts.modal.run`
- URLs stay the same across deployments — safe to hardcode in North and MCP config
- Functions scale to zero automatically. No config needed. If nobody calls for ~5 minutes, they sleep. Next call wakes them (2-3 second cold start).
- Google Sheets credentials stored as Modal secrets, not in code

**Migration steps:**
1. Extract VOSS route logic into standalone functions (no Flask app context dependency)
2. Create `modal_app.py` with web endpoints wrapping those functions
3. Add Google Sheets credentials as Modal secret: `modal secret create google-sheets-credentials GOOGLE_CREDENTIALS_JSON=@credentials.json`
4. Deploy: `modal deploy modal_app.py`
5. Test each endpoint via curl
6. Update MCP config to point at Modal URLs instead of localhost

### 2. Telegram: NanoClaw Handles Everything

**Current:** Separate VOSS Telegram bot polling on Mac, burns CPU/battery
**Target:** NanoClaw runs the North Telegram bot on Mac. All Telegram interaction goes through NanoClaw. Modal is never involved in Telegram.

**Architecture:**

```
Telegram ←→ NanoClaw (Mac)
                  │
                  ├── Morning briefing → calls Gmail, Calendar, VOSS API (Modal)
                  ├── Interactive commands → calls VOSS API (Modal)
                  └── Button presses (inline keyboards) → calls VOSS API (Modal)
```

**Inline keyboards for follow-up alerts** (NanoClaw sends these, not Modal):

When NanoClaw sends a follow-up alert, it includes action buttons. Button press callbacks come back to NanoClaw, which calls the VOSS API on Modal to update the data.

```
⏰ Follow-up due: Jared Mattera
   PE DD automation concept (3 days overdue)

[✅ Done]  [⏭ 3 days]  [⏭ 7 days]
```

```
📊 Deal: IDS Apex
   Stage change: Proposal → Negotiation

[📝 Add note]  [⏭ Next action]  [👁 View]
```

Tapping a button → NanoClaw receives callback → calls VOSS API on Modal → confirms action back in Telegram.

**VOSS Telegram code:** Keep in the repo but don't deploy. Fallback if NanoClaw approach doesn't work.

### 3. North Morning Briefing → NanoClaw Scheduled Task

**NanoClaw drives the schedule, not Modal.** NanoClaw runs on Mac with a scheduled task at 7:30am. It calls Gmail and Calendar directly (built-in connectors), calls VOSS API on Modal for CRM data, then Claude reasons about what's important, filters the noise, and writes the briefing. Sends to Telegram.

This means the briefing only fires when Mac is on. Accepted trade-off for now — migrate NanoClaw to always-on hosting when revenue justifies it.

**NanoClaw CLAUDE.md for North group:**

```markdown
You are North, Mark's chief of staff.

Every morning at 7:30am, prepare a daily briefing:

1. Check Google Calendar for today's events
2. Check Gmail for unread emails (ignore promotions, social, newsletters, automated notifications)
3. Call VOSS API at {VOSS_API_URL} for:
   - Follow-ups due today
   - Overdue follow-ups
   - Contacts going stale (no interaction 14+ days with active deal)
4. Decide what matters. Not everything is worth surfacing. Prioritise:
   - 🔴 Emails waiting for a reply more than 48 hours
   - 🔴 Calls/meetings today that need prep
   - 🔴 Overdue VOSS follow-ups
   - 🟡 New inbound from warm contacts
   - 🟢 Confirmations and good news (one line each, max 3)
5. Suggest focus for deep work blocks based on what's on the calendar
6. Send the briefing to Telegram

Keep it under 2 minutes to read. No fluff. No motivational quotes.
Flag if the day is all development and no outreach — that pattern needs watching.

Monday and Thursday mornings before 9am are offline. Prayer at 12:30-1pm is protected.
```

**No custom code.** NanoClaw handles the scheduling, Claude handles the reasoning, VOSS on Modal provides the CRM data. The CLAUDE.md file IS the agent.

**Modal's role:** VOSS API endpoints only. Modal does not run the briefing cron. NanoClaw does.

### 4. MCP Config Update

```json
{
  "voss-crm": {
    "url": "https://your-username--voss-crm.modal.run"
  }
}
```

Same MCP interface. Same tools. Different host. Claude Code doesn't know the difference. Works whether your Mac's VOSS process is running or not.

---

## Cost Estimate

| Component | Usage | Estimated Cost |
|-----------|-------|---------------|
| VOSS API endpoints | ~50 calls/day (NanoClaw + MCP + manual) | ~$0.50/month |
| Telegram webhook | ~20 messages/day | ~$0.30/month |
| NanoClaw (Mac) | Claude API calls for briefing + reasoning | ~$2-3/month in tokens |
| Modal startup credits | Already deposited | Free for months |

**Total: under $4/month.** Zero battery drain from VOSS polling on Mac.

---

## What Stays on Mac

- Claude Code (development environment)
- NanoClaw (agent orchestration — runs North scheduled briefing, interactive VOSS commands)
- Chrome extension (LinkedIn plugin)
- Claude UI (conversations)

**What moves to Modal:**
- VOSS API endpoints only (data layer, always available even when Mac is off)

**What stays on NanoClaw (Mac):**
- All Telegram interaction (sending briefings, receiving replies, button presses)
- Gmail and Calendar access
- Claude reasoning (briefing intelligence, prep, drafting)

**What stays on Google:**
- Google Sheets (VOSS data backend — migrating to reimagined.industries company workspace)
- Google Calendar API
- Gmail API

**Note on Modal web endpoints:** `modal deploy` gives stable persistent URLs that don't change between deployments. No custom timeout code needed — unlike `modal run` (used for CONSTELLATION simulations), web endpoints automatically scale to zero after ~5 minutes of inactivity. This is different from CONSTELLATION's use case which needed explicit timeout handling because `modal run` starts long-running processes.

---

## Environment / Secrets on Modal

```bash
# Only Google Sheets credentials needed on Modal
modal secret create google-sheets-credentials \
  GOOGLE_CREDENTIALS_JSON=@path/to/credentials.json
```

**Note:** Modal is purely the VOSS data layer. All Telegram, Gmail, and Calendar credentials live with NanoClaw on Mac. Modal never touches Telegram.

**Google Sheets migration:** The VOSS Google Sheet needs moving from Mark's personal Google account to the reimagined.industries company workspace:
1. Create a copy of the existing VOSS sheet in the company workspace
2. Verify all data transferred correctly
3. Create a service account in the company workspace for Modal to use
4. Update the Modal secret with company workspace credentials
5. Update any local references (MCP config, scripts) to the new sheet ID
6. Keep the old sheet as read-only backup for 30 days, then archive

---

## Migration Sequence

1. Add CHANGELOG.md to VOSS repo
2. Migrate Google Sheets from personal account to reimagined.industries company workspace
3. Extract VOSS route handlers into standalone functions
4. Create `modal_app.py` with web endpoints
5. Add Google Sheets credentials (company workspace) as Modal secret
6. Deploy: `modal deploy modal_app.py`
7. Test VOSS endpoints via curl
8. Update MCP config to point at Modal
9. Create NanoClaw `groups/north/CLAUDE.md` with briefing instructions
10. Configure North to call VOSS API on Modal for follow-ups and contact data
11. Set NanoClaw scheduled task for 7:30am weekdays
12. Verify briefing arrives next morning (Mac must be on)
13. Remove VOSS local polling script from Mac startup
14. Log all changes in CHANGELOG.md

---

## Risks

**Cold start latency:** Modal functions take 2-3 seconds to spin up after idle. NanoClaw calls to VOSS API will have a brief delay on first call. Acceptable.

**Google Sheets rate limits:** 300 requests per minute per project. At 50 calls/day, not a concern.

**Modal downtime:** Modal is a startup. Outages happen. If Modal is down, VOSS API is down. Acceptable at this scale. Move to Render or Fly later if needed.

**Mac dependency:** Morning briefing only fires when Mac is on. Accepted trade-off. Migrate NanoClaw to always-on hosting when revenue justifies it.

---

## CHANGELOG.md

Add to VOSS repo root. Format:

```markdown
# Changelog

## [Unreleased]

### Added
- Modal deployment for VOSS API endpoints
- North integration via NanoClaw (CLAUDE.md-based agent)
- Google Sheets migrated to company workspace

### Changed
- VOSS API now hosted on Modal (was localhost)
- MCP config points to Modal URLs

### Removed
- Local Telegram polling (replaced by NanoClaw)
```

Update with every meaningful change. Not every commit — every change a user or collaborator would care about.

---

*This spec is the input for Claude Code. Deploy VOSS API to Modal, migrate Google Sheets to company workspace, then configure NanoClaw North group on Mac.*
