"""Voss CRM MCP Server — wires up all tools using FastMCP."""

import asyncio

from mcp.server.fastmcp import FastMCP

from mcp_server.tools.contacts import search_contacts, get_contact_details, create_contact
from mcp_server.tools.interactions import log_interaction, get_interaction_history
from mcp_server.tools.deals import get_pipeline, get_deal, update_deal_stage, create_deal, update_deal, promote_contact_to_deal
from mcp_server.tools.follow_ups import get_follow_ups, create_follow_up, complete_follow_up
from mcp_server.tools.dashboard import get_dashboard_summary

mcp = FastMCP("voss-crm")


# --- Contacts ---

@mcp.tool()
async def tool_search_contacts(query: str) -> str:
    """Search contacts by name, email, company, role, or tags."""
    return await asyncio.to_thread(search_contacts, query)


@mcp.tool()
async def tool_get_contact_details(contact_id: str) -> str:
    """Get full profile for a contact including interactions, deals, and follow-ups."""
    return await asyncio.to_thread(get_contact_details, contact_id)


@mcp.tool()
async def tool_create_contact(
    first_name: str,
    last_name: str = "",
    email: str = "",
    phone: str = "",
    role: str = "",
    company_name: str = "",
    source: str = "",
    tags: str = "",
    notes: str = "",
    segment: str = "",
    engagement_stage: str = "new",
    inbound_channel: str = "",
) -> str:
    """Create a new contact in the CRM."""
    return await asyncio.to_thread(
        create_contact, first_name, last_name, email, phone,
        role, company_name, source, tags, notes,
        segment, engagement_stage, inbound_channel,
    )


# --- Interactions ---

@mcp.tool()
async def tool_log_interaction(
    contact_id: str,
    type: str,
    subject: str,
    body: str = "",
    direction: str = "",
    deal_id: str = "",
) -> str:
    """Log an interaction (call, email, meeting, or note) with a contact."""
    return await asyncio.to_thread(
        log_interaction, contact_id, type, subject, body, direction, deal_id,
    )


@mcp.tool()
async def tool_get_interaction_history(
    contact_id: str = "",
    deal_id: str = "",
    limit: int = 20,
) -> str:
    """Get recent interaction history, optionally filtered by contact or deal."""
    return await asyncio.to_thread(
        get_interaction_history, contact_id, deal_id, limit,
    )


# --- Deals ---

@mcp.tool()
async def tool_get_pipeline() -> str:
    """Get an overview of all deals grouped by stage with values."""
    return await asyncio.to_thread(get_pipeline)


@mcp.tool()
async def tool_get_deal(deal_id: str) -> str:
    """Get full details about a specific deal."""
    return await asyncio.to_thread(get_deal, deal_id)


@mcp.tool()
async def tool_update_deal_stage(deal_id: str, stage: str) -> str:
    """Move a deal to a new pipeline stage. Valid stages: lead, prospect, qualified, proposal, negotiation, won, lost."""
    return await asyncio.to_thread(update_deal_stage, deal_id, stage)


@mcp.tool()
async def tool_create_deal(
    title: str,
    contact_name: str = "",
    company_name: str = "",
    stage: str = "lead",
    value: str = "",
    currency: str = "GBP",
    priority: str = "medium",
    expected_close: str = "",
    notes: str = "",
) -> str:
    """Create a new deal. Accepts contact/company names (resolved automatically)."""
    return await asyncio.to_thread(
        create_deal, title, contact_name, company_name, stage,
        value, currency, priority, expected_close, notes,
    )


@mcp.tool()
async def tool_promote_contact_to_deal(
    contact_name: str,
    title: str,
    stage: str = "lead",
    value: str = "",
    currency: str = "GBP",
    priority: str = "medium",
    notes: str = "",
) -> str:
    """Create a deal from a contact, automatically resolving their company. Handy after logging a deal-worthy interaction."""
    return await asyncio.to_thread(
        promote_contact_to_deal, contact_name, title, stage,
        value, currency, priority, notes,
    )


@mcp.tool()
async def tool_update_deal(
    deal_id: str,
    title: str = "",
    contact_name: str = "",
    company_name: str = "",
    stage: str = "",
    value: str = "",
    currency: str = "",
    priority: str = "",
    expected_close: str = "",
    notes: str = "",
) -> str:
    """Update an existing deal. Only provided fields are changed. Accepts contact/company names."""
    return await asyncio.to_thread(
        update_deal, deal_id, title, contact_name, company_name, stage,
        value, currency, priority, expected_close, notes,
    )


# --- Follow-ups ---

@mcp.tool()
async def tool_get_follow_ups(
    status: str = "pending",
    overdue_only: bool = False,
    contact_id: str = "",
) -> str:
    """Get follow-ups, optionally filtered by status, overdue, or contact."""
    return await asyncio.to_thread(
        get_follow_ups, status, overdue_only, contact_id,
    )


@mcp.tool()
async def tool_create_follow_up(
    contact_id: str,
    title: str,
    due_date: str,
    due_time: str = "",
    deal_id: str = "",
    notes: str = "",
) -> str:
    """Schedule a new follow-up for a contact. due_date format: YYYY-MM-DD."""
    return await asyncio.to_thread(
        create_follow_up, contact_id, title, due_date, due_time, deal_id, notes,
    )


@mcp.tool()
async def tool_complete_follow_up(follow_up_id: str) -> str:
    """Mark a follow-up as completed."""
    return await asyncio.to_thread(complete_follow_up, follow_up_id)


# --- Dashboard ---

@mcp.tool()
async def tool_get_dashboard_summary() -> str:
    """Get a high-level CRM dashboard: pipeline summary, overdue follow-ups, today's tasks, and recent activity."""
    return await asyncio.to_thread(get_dashboard_summary)
