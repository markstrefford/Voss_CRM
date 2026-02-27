# Voss CRM — Workflow & Process Design

## Philosophy: Contact-Centric, Signal-Driven

This CRM is built around **people, not companies**. The mental model is "I'm speaking to David at Acme Corp" not "I'm interacting with Acme Corp." Contacts are the primary unit of work. Companies provide grouping and context — when you need "everything with Acme Corp", the company view gives you that, but day-to-day you think in terms of people.

The system follows the Signal Strata philosophy: **surface what needs attention right now**, with both positive signals (act on momentum) and negative signals (don't let things slip). The CRM does the thinking, you work the list.

## Opens and Opportunities

Every contact starts as an **Open** — someone new to your world. They arrive through two paths:

**Inbound:**
- Followed you on LinkedIn
- Viewed a post or your profile
- Commented on your content
- Subscribed to a newsletter or lead magnet

**Outbound:**
- You sent a connect request
- You sent them an email or message
- You commented on their post to start building a relationship

To move from Open to **Opportunity**, four things need to be true: they have **pain**, they have **desire** to solve it, there's **proof you can help**, and they're **engaged** (this also means ICP match). That's when a casual relationship becomes a real business conversation.

## Contacts vs Deals: The Pipeline Problem

A typical B2B consulting pipeline looks like:

```
Lead → Prospect → Discovery → Proposal → Negotiation → Won / Lost
```

But "this isn't just deals — deals are further down the line." If you import 157 cold prospects, the pipeline is empty — and that's actually correct. There's no revenue opportunity yet. They're pre-pipeline.

The question is: **where's the tracking of conversations?** You have a lead list, you start talking to people, but where does that live before there's a deal?

### How other CRMs solve this

**Pipedrive**: Everything is a deal from day one. Even "cold outreach to Acme Corp" is a £0 deal in the "Lead" stage. Simple, but clutters the pipeline with hundreds of unqualified entries.

**HubSpot**: Lifecycle stages on contacts (subscriber → lead → MQL → SQL → opportunity → customer) as a separate funnel from the deal pipeline. Structured, but heavy.

**Close CRM**: No separate board for prospecting. Instead, **smart filtered views** of your contacts list — "reached out this week, no reply", "replied but no meeting booked", "had a call, no follow-up scheduled." Views update automatically based on interaction data you're already logging. No manual stage-dragging.

### The Signal Strata approach

We chose Close CRM's philosophy, applied through the Signal Strata lens: the system **surfaces what needs attention right now** rather than making you manage boards and stages manually. Not just negative signals ("not replied") but positive ones too ("they just replied — act now").

This means no prospecting kanban board. Instead, the action feed is an opinionated dashboard that watches your data and tells you who needs attention and why.

## The Two-Track Model

With that decision made, relationships and revenue are tracked on two separate axes:

### Track 1: Relationship (on the Contact)

Every contact has an **engagement stage** that tracks where the relationship is:

```
new → nurturing → active → client → churned
```

- **New** — just entered your world, no outreach yet (your "Opens")
- **Nurturing** — you've reached out, building the relationship
- **Active** — regular back-and-forth, conversations happening (your "Opportunities")
- **Client** — paying customer, active engagement
- **Churned** — relationship has gone cold or ended

This is the pre-deal relationship. Most contacts live here permanently — they may never become a deal, but they're still worth tracking and nurturing. The smart queues surface who needs attention without you having to drag cards between columns.

### Track 2: Revenue (on the Deal)

A **Deal** represents a specific revenue opportunity. It gets created at the point where you can say **"there's a potential £X engagement here."** That could be as early as Discovery (if you know roughly what they need) or as late as Proposal (when you're putting numbers on paper).

```
lead → prospect → qualified → proposal → negotiation → won / lost
```

The later pipeline stages (proposal, negotiation, won) are essentially the deal itself — there's a specific piece of work, a value, and a timeline. The earlier stages (lead, prospect, discovery) overlap with the contact's engagement stage, which is fine. The deal tracks the money; the contact tracks the relationship.

A Deal attaches to a Contact (and their Company). Not every contact has a deal. Not every relationship needs one. The deal pipeline only activates when there's something concrete on the table.

### How They Connect

1. Contact arrives (engagement_stage: `new`) — your cold outbound list or an inbound lead
2. You engage — update to `nurturing` or `active`
3. Real opportunity emerges — create a Deal linked to the contact/company
4. Deal progresses through pipeline stages (proposal → negotiation → won)
5. Deal closes → contact becomes `client`

The gap most CRMs have is the space between "I know this person" and "there's a deal on the table." That's where engagement stages and the smart queues fill in — they track the pre-deal relationship that traditional pipelines miss entirely.

## Contact Segments

Contacts are tagged with a **segment** to distinguish business lines:

| Segment        | Description                              |
|----------------|------------------------------------------|
| signal_strata  | Signal Strata product prospects/clients  |
| consulting     | IT/management consulting prospects       |
| pe             | Private equity contacts                  |
| other          | Everything else                          |

## Inbound Channels

How the contact entered your world:

- **linkedin** — connected, messaged, or engaged on LinkedIn
- **referral** — introduced by someone
- **conference** — met at an event
- **cold_outbound** — you reached out first
- **website** — came through a web form or lead magnet
- **other** — catch-all

## The Multi-Contact Scenario

When multiple people at the same company are involved in the same engagement (e.g., David and his colleague John at Acme Corp):

- David and John are **separate contacts**, both with `company_id` pointing to Acme Corp
- Each has their own interactions, follow-ups, and engagement stage
- If they're part of the same deal, the Deal links to the company
- The company page shows all contacts, giving you the full picture

## Daily Workflow

### Morning (phone, still in bed)

The **morning digest** arrives via Telegram at 09:30:

- Overdue follow-ups (people you should have contacted already)
- Today's follow-ups (what's on the plate)
- Stale deals (pipeline items going cold)

You scan it and decide what to tackle first.

### Working the Smart Queues

The **Action Feed** (dashboard) surfaces four priority queues:

#### 1. Action Required (red)
Overdue and due-today follow-ups. These are commitments you've already made — "call David Tuesday", "send proposal to Jane by Friday." Non-negotiable, do these first.

#### 2. Momentum (green)
**Positive signals** — act while the iron's hot:
- Someone replied to your message in the last 7 days
- You had an active conversation but haven't scheduled a next step

These are opportunities to keep things moving. A reply sitting without a response for 3 days kills momentum.

#### 3. At Risk (amber)
**Negative signals** — things slipping through the cracks:
- Contacts going cold (14+ days since last interaction, but engagement stage says they should be active)
- Stale deals (pipeline items with no update in 14+ days)

These need a nudge, a check-in, or a decision to deprioritise.

#### 4. Ready to Reach Out (blue)
New contacts with zero interactions. Your cold outbound list. When you have capacity, work through these.

### Throughout the Day

- **Log interactions** as they happen (calls, emails, meetings, LinkedIn messages) — from the contact page or via Telegram `/note`
- **Schedule follow-ups** immediately after every conversation — "what's the next step and when?" via the contact page or Telegram `/followup`
- **Timed reminders** fire via Telegram when a follow-up has a specific due time

### Evening

**Stale deal alerts** arrive at 18:00 — a nudge to review pipeline items that haven't moved.

### The Safety Net

"View all" links on the dashboard give a global view of all contacts and all deals — in case something falls through the cracks of the smart queues. This is deliberate: queues are opinionated filters, but you always need a way to see everything.

## Follow-Up Lifecycle

Follow-ups are the connective tissue of the workflow. Every conversation should end with a scheduled next step.

```
Created → Pending → Completed
                 ↘ Snoozed (new date) → Pending → ...
```

- **Created** from: contact detail page, Telegram `/followup`, MCP tools
- **Grouped** into: overdue, due today, upcoming, completed
- **Actions**: complete (done), snooze (push to a new date)
- **Reminders**: if a due_time is set, Telegram fires a reminder at that time
- **Surfaced**: in morning digest, action feed, contact detail page, follow-ups page

## From Cold List to Client — A Typical Flow

Here's a concrete example using the 157 UK IT consulting prospects imported from Sales Navigator:

1. **Import** — 157 companies, 208 contacts arrive as `segment: consulting`, `engagement_stage: new`, `inbound_channel: cold_outbound`
2. **Ready to Reach Out queue** shows all 208 with "No outreach yet"
3. **You reach out** to 20 of them on LinkedIn — log interactions, update stage to `nurturing`, schedule follow-ups for "check if they accepted connect request" in 5 days
4. **5 reply** — they appear in the **Momentum queue** ("Replied via linkedin_message, 1d ago"). You respond, schedule follow-ups
5. **2 go quiet** — after 14 days they appear in **At Risk** ("No interaction for 16d ago"). You decide to try one more message or deprioritise
6. **1 conversation turns into an opportunity** — you create a Deal (stage: `qualified`, value: £50K). Contact moves to `active`
7. **Deal progresses** — proposal sent, negotiation, eventually won. Contact becomes `client`
8. **The other 155** stay in `new` or `nurturing`, worked when you have capacity, surfaced by the queues when relevant

The CRM doesn't force you through steps. It watches what's happening and tells you what needs attention.
