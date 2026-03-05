# VOSS Social Engagement Capture — Technical Specification

**Version:** 1.0
**Date:** 4 March 2026
**Status:** Ready for implementation planning

---

## Purpose

Two lightweight tools that capture social engagement signals and write them into VOSS CRM. The goal is simple: when someone interacts with Mark on Instagram or LinkedIn, VOSS should know about it without manual data entry.

No auto-replies. No DM automation. No engagement scoring. Just: who did something, what they did, which content triggered it, and is it in VOSS.

---

## Architecture Overview

```
┌─────────────────────┐     ┌──────────────────────┐
│   Instagram          │     │   LinkedIn            │
│   (Meta Graph API)   │     │   (browser DOM)       │
│                      │     │                       │
│   Webhooks push to   │     │   Chrome extension    │
│   listener service   │     │   reads page context  │
└────────┬────────────┘     └────────┬─────────────┘
         │                           │
         ▼                           ▼
┌─────────────────────┐     ┌──────────────────────┐
│   Instagram          │     │   LinkedIn Plugin     │
│   Listener           │     │   Enhancement         │
│   (Python, Render)   │     │   (existing VOSS      │
│                      │     │    Chrome extension)   │
└────────┬────────────┘     └────────┬─────────────┘
         │                           │
         └───────────┬───────────────┘
                     ▼
              ┌──────────────┐
              │   VOSS API    │
              │               │
              │ search_contacts│
              │ create_contact │
              │ log_interaction│
              └──────────────┘
```

Both tools produce the same data shape and write to VOSS through the same API endpoints. They are independent — either can be built and deployed without the other.

---

## Shared Data Model

### Engagement Event (normalised shape from both tools)

```json
{
  "platform": "instagram" | "linkedin",
  "person": {
    "handle": "@username or linkedin-profile-url",
    "display_name": "Sarah Chen",
    "profile_url": "https://instagram.com/username or https://linkedin.com/in/username"
  },
  "action": "comment" | "like" | "dm" | "story_mention" | "story_reply" | "connection_request" | "message" | "share" | "follow",
  "content_ref": {
    "post_url": "url of the post they engaged with (if applicable)",
    "post_title": "short description or first line of post (if available)"
  },
  "text": "what they said (comment text, DM text, etc. — null for likes/follows)",
  "timestamp": "ISO 8601"
}
```

### VOSS Integration Logic

For each engagement event:

1. **Search VOSS** for existing contact matching handle or name
2. **If found:** Log interaction against existing contact
   - Interaction type maps from action (see mapping below)
   - Note includes: platform, what they did, which post, what they said
   - Update `last_interaction_date`
3. **If not found:** Create new contact in VOSS
   - Name: from display name
   - Tags: platform name (e.g. `instagram`, `linkedin`)
   - Source: `instagram_organic` or `linkedin_organic`
   - Engagement stage: `new`
   - Notes: first interaction details
   - Then log the interaction

### Action to VOSS Interaction Type Mapping

| Social Action | VOSS Interaction Type | Notes |
|--------------|----------------------|-------|
| comment | note | "Commented on [post]: [text]" |
| like | note | "Liked [post]" |
| dm / message | note | "DM: [text]" |
| story_mention | note | "Mentioned you in their story" |
| story_reply | note | "Replied to your story: [text]" |
| connection_request | note | "Sent connection request" |
| share | note | "Shared [post]" |
| follow | note | "Started following" |

All logged as `note` type interactions for now. As patterns emerge, we may want richer types. Keep it simple to start.

---

## Tool 1: Instagram Listener

### What It Does

A small Python service hosted on Render that receives webhook events from Meta's Graph API and writes engagement data to VOSS. Runs 24/7, no manual intervention required.

### Prerequisites

- Instagram account: **Creator** or **Business** account (Mark has Creator)
- Facebook Page linked to the Instagram account (Mark to confirm)
- Meta Business App (free to create at developers.facebook.com)
- Permissions needed:
  - `instagram_manage_comments` — read comments on posts/reels
  - `instagram_manage_messages` — read DMs (requires Meta app review)
  - `pages_manage_metadata` — webhook subscriptions
  - `instagram_basic` — profile info for the account

### Webhook Events to Subscribe

| Event Field | Trigger | Data Available |
|------------|---------|----------------|
| `follows` | Someone follows the account | Follower user ID, username |
| `comments` | Someone comments on a post or reel | Commenter username, comment text, media ID |
| `messages` | Someone sends a DM | Sender ID, message text, timestamp |
| `likes` | Someone likes a post or reel | User ID, media ID |
| `story_insights` | Story mention or reply | Limited — may need polling as fallback |

**Note on DMs:** Instagram Messaging API requires Meta app review for production access. For initial build, start with comments, likes, and follows (no review needed for your own account). DMs can be added once the app passes review.

**Note on stories:** Story mentions and replies have limited webhook support. May need to poll the `/me/stories` endpoint on a schedule (every 5–10 minutes) as a fallback.

**Note on likes:** Likes on posts are available via webhooks. Likes on comments are not — ignore those for now.

### Service Architecture

```
Render (Python / Flask or FastAPI)
│
├── /webhook/instagram (POST)
│   ├── Verify webhook (Meta challenge/response)
│   ├── Receive event
│   ├── Parse into normalised engagement event
│   ├── Call VOSS API:
│   │   ├── search_contacts(handle)
│   │   ├── create_contact (if new)
│   │   └── log_interaction
│   └── Return 200
│
├── /webhook/instagram (GET)
│   └── Webhook verification endpoint (Meta sends challenge on setup)
│
├── /poll/stories (cron, every 10 min)
│   ├── Fetch recent story interactions
│   ├── Parse into normalised events
│   └── Write to VOSS (same logic as above)
│
└── /health
    └── Returns 200 (for Render health checks)
```

### Environment Variables

```
META_APP_ID=
META_APP_SECRET=
META_ACCESS_TOKEN=          # Long-lived page access token
META_VERIFY_TOKEN=          # Webhook verification string (you choose this)
INSTAGRAM_ACCOUNT_ID=       # Instagram business/creator account ID
VOSS_API_URL=               # VOSS backend URL
VOSS_API_KEY=               # Auth for VOSS API (if applicable)
```

### Token Management

Meta access tokens expire. The service needs to handle token refresh:

- **Short-lived token** (from login): 1 hour
- **Long-lived token** (exchanged): 60 days
- **Page token** (from long-lived user token): does not expire but can be invalidated

For initial build: manually generate a long-lived page token and store as env var. Set a calendar reminder to refresh every 50 days. For later: build auto-refresh into the service.

### Deduplication

Meta can send duplicate webhook events. The service should:

- Track event IDs (Meta includes a unique ID per webhook delivery)
- Skip processing if the event ID has been seen before
- Simple approach: keep a set of recent event IDs in memory (last 1000). No persistent storage needed for this.

### Error Handling

- If VOSS API is unreachable, log the event to a local file/queue for retry
- If Meta sends malformed data, log and skip (don't crash the service)
- All webhook endpoints must return 200 quickly — do VOSS writes async or in background

### Rate Limits

Meta Graph API rate limits are generous for single-account usage (~200 calls per hour per user). Polling stories every 10 minutes uses ~6 calls per hour. Well within limits.

### Build Sequence

1. Create Meta Business App, configure Instagram Graph API
2. Build webhook endpoint with verification
3. Subscribe to `comments` events
4. Parse comment events into normalised shape
5. Write to VOSS (search → create/update → log interaction)
6. Deploy to Render
7. Test with a real comment on a real post
8. Add story polling (if webhooks insufficient)
9. Add DM support after Meta app review (Phase 2)

---

## Tool 2: LinkedIn Plugin Enhancement

### What It Does

Extends the existing VOSS Chrome extension to read LinkedIn engagement context from the browser and provide one-click capture to VOSS. Not an API integration — a UI overlay that helps Mark capture engagement he's already looking at.

### Current State

The existing VOSS Chrome extension does one thing: quick-add a contact from a LinkedIn profile page. It reads the profile DOM, extracts name and details, and sends to VOSS.

### Enhancement

Add an **engagement capture mode** that activates on LinkedIn notification and post analytics pages. The extension reads visible interactions from the DOM and presents them as a capture queue.

### Pages to Support

| LinkedIn Page | URL Pattern | What to Extract |
|--------------|-------------|-----------------|
| Notifications | `linkedin.com/notifications` | Name, action type (commented, liked, shared, connected), post reference |
| Post analytics | `linkedin.com/analytics/post-summary/*` or individual post pages | Who liked, who commented, comment text |
| Post detail | `linkedin.com/feed/update/*` | Comments: name + text + timestamp |
| Messaging | `linkedin.com/messaging/*` | Conversation partner name, latest message preview |

### UX Flow

```
1. Mark opens LinkedIn notifications page
2. Extension icon shows badge: "12 new interactions"
3. Mark clicks extension icon
4. Panel shows list:
   ┌─────────────────────────────────────────────┐
   │ LinkedIn Engagement Capture                  │
   │                                              │
   │ ☐ Sarah Chen commented on "Operating Models" │
   │   "This is exactly what we're seeing at..."  │
   │                                              │
   │ ☐ James Ward liked "Operating Models"        │
   │                                              │
   │ ☐ Paris Mudan sent you a message             │
   │   "Hi Mark, following up on..."              │
   │                                              │
   │ ☐ Tom Liu shared your post "Data is noisy"   │
   │                                              │
   │ [Capture Selected]  [Capture All]            │
   └─────────────────────────────────────────────┘
5. Mark selects relevant ones, clicks "Capture Selected"
6. For each selected:
   → VOSS search_contacts (by name or LinkedIn URL)
   → If found: log_interaction
   → If not found: create_contact + log_interaction
7. Panel updates: "3 captured to VOSS ✓"
```

### DOM Parsing Strategy

LinkedIn's DOM changes frequently. The extension should:

- **Use content-based selectors** rather than class names where possible (class names are obfuscated and change)
- **Use ARIA labels and data attributes** which are more stable — LinkedIn uses accessibility attributes like `aria-label="Sarah Chen commented on your post"` and data attributes like `data-control-name="notification_card"`. These are tied to accessibility compliance and functional behaviour, so they change less often than visual class names like `artdeco-button__text` which get regenerated on every frontend rebuild.
- **Fall back to structural patterns** (notification items are list elements with consistent hierarchy)
- **Include a version check** — if the DOM structure seems unrecognisable, show "LinkedIn layout may have changed — update needed" rather than silently failing
- **Log parsing failures** so breakages can be identified quickly

### Data Extraction Per Page

**Notifications page:**
```
Each notification item contains:
- Actor name (who did the action)
- Action text ("commented on your post", "likes your post", etc.)
- Post reference (partial title or snippet)
- Timestamp (relative: "2h", "1d")
- Link to the actor's profile (for VOSS profile URL)

Parse action text to determine interaction type:
- "commented" → comment
- "likes" / "liked" → like
- "shared" → share
- "sent you a message" → message
- "accepted your invitation" → connection_request
- "started following" → follow
```

**Post detail page (comments section):**
```
Each comment contains:
- Commenter name
- Commenter profile URL
- Comment text
- Timestamp
- Whether it's a reply to another comment

Only capture top-level comments by default. 
Mark can expand replies if he wants those too.
```

### Extension Architecture

```
existing VOSS Chrome extension
│
├── content-script-linkedin-profile.js  (existing — quick-add from profile)
│
├── content-script-linkedin-engagement.js  (NEW)
│   ├── Detect page type (notifications / post / messaging)
│   ├── Parse DOM for engagement items
│   ├── Send parsed items to popup/panel
│   └── Re-scan when page scrolls or updates (LinkedIn loads lazily)
│
├── popup.html / popup.js  (ENHANCED)
│   ├── Existing: quick-add contact form
│   ├── New: engagement capture queue (when on supported pages)
│   ├── New: "Capture Selected" / "Capture All" buttons
│   └── New: status indicators (captured ✓, already in VOSS, new)
│
├── background.js  (ENHANCED)
│   ├── Existing: VOSS API communication
│   ├── New: batch capture logic (search → create/update → log)
│   └── New: badge count on extension icon
│
└── voss-api.js  (shared API client)
    ├── searchContacts(name, handle)
    ├── createContact(data)
    └── logInteraction(contactId, data)
```

### Handling "Already in VOSS"

When the extension parses engagement items, it should check VOSS for each person before displaying the queue:

- **Already in VOSS:** Show with a subtle indicator. One-click still logs the new interaction.
- **Not in VOSS:** Show with "NEW" badge. One-click creates contact and logs interaction.
- **Already captured this interaction:** Don't show (deduplication based on name + action + post + approximate timestamp)

This pre-check can be batched: send all names from the current page to VOSS in one search request, then annotate the queue.

### Deduplication

The extension should track recently captured interactions in `chrome.storage.local`:

```json
{
  "captured_interactions": [
    {
      "name": "Sarah Chen",
      "action": "comment",
      "post_snippet": "Operating Models",
      "captured_at": "2026-03-04T16:30:00Z"
    }
  ]
}
```

Prune entries older than 7 days. Don't show items in the queue that match a recent capture. This prevents double-logging when Mark checks notifications multiple times.

### Build Sequence

1. Add content script for notifications page — parse engagement items from DOM
2. Send parsed items to extension popup
3. Build the engagement capture queue UI in popup
4. Wire "Capture Selected" to VOSS API (search → create/update → log)
5. Add badge count on extension icon
6. Test on real notifications page
7. Add post detail page support (comments)
8. Add "already in VOSS" checking
9. Add deduplication via chrome.storage.local
10. Add messaging page support (Phase 2 — lower priority)

---

## VOSS Telegram Bot Changes

The existing VOSS Telegram bot needs minor enhancements to support the social capture pipeline:

### Cross-Platform Match Confirmation

When the Instagram listener flags a `pending_link` (name match, no handle match), the Telegram bot sends a prompt:

```
VOSS: "New Instagram interaction from @sarahchen_
       (commented on 'Operating Models': 'This is exactly what we...')
       Possible match: Sarah Chen (LinkedIn).
       → Link / New contact / Ignore"
```

- **Link:** Adds Instagram handle to existing contact, logs the interaction against them
- **New contact:** Creates a separate contact with Instagram handle, logs interaction
- **Ignore:** Logs interaction without creating or linking (one-off engagement, not worth tracking)

### Link Platform Handle Command

Manual linking when Mark notices a cross-platform connection:

```
Mark: /link @sarahchen_ Sarah Chen
VOSS: "Linked Instagram @sarahchen_ to Sarah Chen (existing LinkedIn contact). 
       Future Instagram interactions will log against this contact."
```

### No Daily Digest (Yet)

A "3 new Instagram interactions, 7 LinkedIn captures, 2 possible matches" daily summary is useful but belongs in North's morning briefing, not the VOSS bot. The bot handles confirmations and commands. North handles the overview. Keep the responsibilities separate.

---

## Measurement

Both tools tag their data consistently so VOSS can answer:

- **"How many new contacts came from Instagram this month?"**
  Query: contacts where source = `instagram_organic` and created_at in range

- **"How many new contacts came from LinkedIn this month?"**
  Query: contacts where source = `linkedin_organic` and created_at in range

- **"Which posts generated the most engagement captures?"**
  Query: interactions grouped by content_ref

- **"What's my engagement-to-conversation rate?"**
  Query: contacts from social sources who progressed past `new` engagement stage

- **"What type of engagement converts best?"**
  Query: contacts who reached a call/meeting stage, grouped by first interaction type (comment vs like vs DM)

These queries require no additional infrastructure — they're just VOSS queries against the contact and interaction data that both tools write.

---

## VOSS API Requirements

Both tools need these VOSS API endpoints to be reliable and fast:

| Endpoint | Purpose | Notes |
|----------|---------|-------|
| `search_contacts(query, platform_handle)` | Find existing contact by name or social handle | Must support partial name matching. Should support searching by a `platform_handles` field. |
| `create_contact(data)` | Create new contact | Must accept: name, tags, source, engagement_stage, notes, platform_handles |
| `log_interaction(contact_id, data)` | Log interaction against contact | Must accept: type (note), content (freeform text), platform, timestamp |

### New field on contacts: `platform_handles`

VOSS contacts should store social platform handles for matching:

```json
{
  "platform_handles": {
    "instagram": "markstrefford",
    "linkedin": "https://linkedin.com/in/markstrefford"
  }
}
```

This enables reliable deduplication — matching on name alone is fragile (common names, display name changes). When the Instagram listener or LinkedIn extension captures an interaction, it first searches by platform handle, then falls back to name.

**If VOSS doesn't currently support this field, it should be added before building either tool.** The whole pipeline depends on reliable contact matching.

### Cross-Platform Linking

When you realise a LinkedIn contact is also on Instagram (or vice versa), VOSS should support adding the second handle to the existing contact rather than creating a duplicate.

**How it works:**

- LinkedIn extension captures "Sarah Chen" with LinkedIn handle → contact created
- Instagram listener later captures "@sarahchen_" commenting → no LinkedIn match on handle, name match finds existing contact
- VOSS prompts: "Sarah Chen already exists (LinkedIn). Link this Instagram handle?" → one click adds Instagram handle to existing contact
- From that point, interactions from both platforms log against the same contact

**Implementation:**

- `platform_handles` is a dictionary, not a single value. A contact can have handles for multiple platforms.
- When a new engagement arrives and the platform handle is unknown but a name match is found, the Instagram listener writes the interaction to VOSS with a `pending_link` flag and the candidate contact ID. The **VOSS Telegram bot** then sends a confirmation prompt:

  ```
  VOSS: "New Instagram interaction from @sarahchen_ (commented on 'Operating Models').
  Possible match: Sarah Chen (LinkedIn). Link them?
  → Yes, link / No, create new / Ignore"
  ```

  Mark replies, VOSS either merges the handle onto the existing contact or creates a new one. This keeps the confirmation in the same channel already used for VOSS interactions — no context switch to a web dashboard.

- The LinkedIn extension should show an "Add Instagram handle" field on the existing quick-add panel when viewing a profile. If Mark sees their Instagram in their LinkedIn bio, one action links them.
- The Instagram listener should include a "possible match" flag in its VOSS write when it finds a name match but no handle match, so the Telegram bot can surface these for confirmation.

This keeps one person as one contact regardless of how many platforms they engage on, and the interaction history tells the full cross-platform story.

---

## Deployment

| Component | Platform | Dependencies |
|-----------|----------|-------------|
| Instagram Listener | Render (Python web service) | VOSS API, Meta Graph API |
| LinkedIn Extension | Chrome Web Store (or local install) | VOSS API |
| VOSS API | Render (existing) | PostgreSQL (existing) |

### Repository Structure

All components live in the `voss_crm` repo but in separate folders so they can be deployed independently:

```
voss_crm/
├── api/                    # Existing VOSS backend (Python/Flask)
├── web/                    # Existing VOSS web UI
├── chrome-extension/       # Existing Chrome extension (LinkedIn quick-add + engagement capture)
├── ingest/
│   └── instagram/          # Instagram listener service (standalone Python app, own Render service)
└── ...
```

Each folder under `ingest/` is a standalone deployable service with its own `requirements.txt` and Render service config. Render deploys directly from the folder — no Dockerfiles needed. Each ingest service only depends on the VOSS API endpoints, not on importing code from `api/`. The Chrome extension is already separate by nature (browser deployment). This structure means you can update, redeploy, or tear down any ingest service without touching the core VOSS backend.

Both tools are independent. Either can be built and deployed without the other. The Instagram listener is the cleaner, faster build (no UI, no DOM parsing). The LinkedIn extension has more moving parts but extends existing infrastructure.

---

## Priority and Phasing

### Phase 1: Instagram comments + LinkedIn notifications

- Instagram: webhook for comments on posts and reels → VOSS
- LinkedIn: parse notifications page → one-click capture to VOSS
- VOSS: add `platform_handles` field to contacts

### Phase 2: Richer signals

- Instagram: DM capture (requires Meta app review)
- Instagram: story mention/reply polling
- LinkedIn: post detail page (comment capture)
- LinkedIn: messaging page (DM awareness)

### Phase 3: Intelligence (future, not in this spec)

- Pattern detection: "This person has engaged 4 times this week — worth a DM?"
- Auto-suggest: "Sarah Chen commented again — she's not in VOSS yet. Capture?"
- Content attribution: "Your operating model posts generate 3x more captures than data posts"

Phase 3 is where the agent layer earns its keep. But the tools need to exist and have data flowing before any of that is useful.

---

*This spec is the input for Claude Code. Build the Instagram listener and LinkedIn plugin enhancement as separate workstreams. The `platform_handles` field on VOSS contacts is a shared prerequisite — build that first.*
