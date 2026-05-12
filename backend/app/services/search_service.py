"""Unified knowledge-base search across all VOSS entities.

A query for "Endava" must surface every record that references Endava —
contacts at the company, deals on it, interactions and follow-ups
attached to those contacts/deals — not just rows whose own fields contain
the literal token. Foreign keys are resolved into searchable text so that
contacts whose company_id points to "Endava" match a search for "Endava".
"""

from app.helpers import contact_display_name
from app.services.sheet_service import (
    companies_sheet,
    contacts_sheet,
    deals_sheet,
    follow_ups_sheet,
    interactions_sheet,
)


def _tokens(query: str) -> list[str]:
    return [t for t in query.lower().split() if t]


def _matches(haystack: str, tokens: list[str]) -> bool:
    return all(t in haystack for t in tokens)


def _empty_result(query: str) -> dict:
    return {
        "query": query,
        "total": 0,
        "companies": [],
        "contacts": [],
        "deals": [],
        "interactions": [],
        "follow_ups": [],
    }


def unified_search(query: str) -> dict:
    tokens = _tokens(query)
    if not tokens:
        return _empty_result(query)

    contacts = contacts_sheet.get_all()
    companies = companies_sheet.get_all()
    deals = deals_sheet.get_all()
    interactions = interactions_sheet.get_all()
    follow_ups = follow_ups_sheet.get_all()

    company_by_id = {c["id"]: c for c in companies}
    contact_by_id = {c["id"]: c for c in contacts}
    deal_by_id = {d["id"]: d for d in deals}

    def company_name(cid: str) -> str:
        return company_by_id.get(cid, {}).get("name", "")

    def deal_title(did: str) -> str:
        return deal_by_id.get(did, {}).get("title", "")

    company_hits = []
    for c in companies:
        haystack = " ".join([
            c.get("name", ""), c.get("industry", ""),
            c.get("website", ""), c.get("notes", ""),
        ]).lower()
        if _matches(haystack, tokens):
            company_hits.append({
                **c,
                "name": c.get("name", ""),
            })

    contact_hits = []
    for c in contacts:
        if c.get("status") == "archived":
            continue
        company = company_by_id.get(c.get("company_id", ""), {})
        cname = company.get("name", "")
        haystack = " ".join([
            c.get("first_name", ""), c.get("last_name", ""),
            c.get("email", ""), c.get("phone", ""),
            c.get("role", ""), c.get("tags", ""), c.get("notes", ""),
            c.get("segment", ""), c.get("engagement_stage", ""),
            c.get("platform_handles", ""), c.get("urls", ""),
            c.get("source", ""),
            cname, company.get("industry", ""), company.get("website", ""),
        ]).lower()
        if _matches(haystack, tokens):
            contact_hits.append({
                **c,
                "name": contact_display_name(c),
                "company_name": cname,
            })

    deal_hits = []
    for d in deals:
        contact = contact_by_id.get(d.get("contact_id", ""), {})
        contname = contact_display_name(contact) if contact else ""
        cname = company_name(d.get("company_id", "")) or company_name(contact.get("company_id", ""))
        haystack = " ".join([
            d.get("title", ""), d.get("notes", ""),
            d.get("stage", ""), d.get("priority", ""),
            cname, contname,
        ]).lower()
        if _matches(haystack, tokens):
            deal_hits.append({
                **d,
                "contact_name": contname,
                "company_name": cname,
            })

    interaction_hits = []
    for i in interactions:
        contact = contact_by_id.get(i.get("contact_id", ""), {})
        contname = contact_display_name(contact) if contact else ""
        cname = company_name(contact.get("company_id", "")) if contact else ""
        if not cname and i.get("deal_id"):
            cname = company_name(deal_by_id.get(i["deal_id"], {}).get("company_id", ""))
        dtitle = deal_title(i.get("deal_id", ""))
        haystack = " ".join([
            i.get("subject", ""), i.get("body", ""),
            i.get("type", ""), i.get("direction", ""),
            i.get("url", ""),
            contname, cname, dtitle,
        ]).lower()
        if _matches(haystack, tokens):
            interaction_hits.append({
                **i,
                "contact_name": contname,
                "company_name": cname,
                "deal_title": dtitle,
            })

    follow_up_hits = []
    for f in follow_ups:
        contact = contact_by_id.get(f.get("contact_id", ""), {})
        contname = contact_display_name(contact) if contact else ""
        cname = company_name(contact.get("company_id", "")) if contact else ""
        if not cname and f.get("deal_id"):
            cname = company_name(deal_by_id.get(f["deal_id"], {}).get("company_id", ""))
        dtitle = deal_title(f.get("deal_id", ""))
        haystack = " ".join([
            f.get("title", ""), f.get("notes", ""),
            f.get("status", ""),
            contname, cname, dtitle,
        ]).lower()
        if _matches(haystack, tokens):
            follow_up_hits.append({
                **f,
                "contact_name": contname,
                "company_name": cname,
                "deal_title": dtitle,
            })

    total = (len(company_hits) + len(contact_hits) + len(deal_hits)
             + len(interaction_hits) + len(follow_up_hits))

    return {
        "query": query,
        "total": total,
        "companies": company_hits,
        "contacts": contact_hits,
        "deals": deal_hits,
        "interactions": interaction_hits,
        "follow_ups": follow_up_hits,
    }
