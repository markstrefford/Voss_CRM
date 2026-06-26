"""Unified knowledge-base search across all VOSS entities.

A query for "Endava" must surface every record that references Endava —
contacts at the company, deals on it, interactions and follow-ups
attached to those contacts/deals — not just rows whose own fields contain
the literal token. Foreign keys are resolved into searchable text so that
contacts whose company_id points to "Endava" match a search for "Endava".

Contacts can additionally be narrowed by structured filters (role, segment,
engagement stage, tags). Within a filter the values OR; across filters they
AND; and filters combine with the free-text query (text AND filters). Filters
apply to people only — the other entity buckets stay text-driven.
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


def _norm_list(value) -> list[str]:
    """Normalise a filter argument (None | str | list) to a lowercased list,
    dropping blanks. A bare string is treated as a single value."""
    if not value:
        return []
    if isinstance(value, str):
        value = [value]
    return [v.strip().lower() for v in value if v and v.strip()]


def _passes_contact_filters(contact, roles, segments, stages, tag_filters) -> bool:
    """True when the contact satisfies every supplied filter. Substring filters
    (role, tags) OR their values; equality filters (segment, stage) match any value."""
    if roles:
        role = (contact.get("role") or "").lower()
        if not any(r in role for r in roles):
            return False
    if segments:
        if (contact.get("segment") or "").lower() not in segments:
            return False
    if stages:
        if (contact.get("engagement_stage") or "").lower() not in stages:
            return False
    if tag_filters:
        tagstr = (contact.get("tags") or "").lower()
        if not any(t in tagstr for t in tag_filters):
            return False
    return True


def _score(tiers: list[str], tokens: list[str]) -> int:
    """Relevance score: for each token, add the weight of the highest tier whose text
    contains it (primary tier weighs most). Tiers are ordered strongest-first; text is
    lowercased here. No tokens (filters-only) → 0, leaving order stable."""
    n = len(tiers)
    lowered = [t.lower() for t in tiers]
    total = 0
    for tok in tokens:
        tok = tok.lower()
        for i, text in enumerate(lowered):
            if tok in text:
                total += n - i
                break
    return total


def _ranked(scored: list) -> list:
    """Stable-sort scored (score, hit) pairs best-first and return the hits."""
    scored.sort(key=lambda pair: -pair[0])
    return [hit for _, hit in scored]


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


def unified_search(
    query: str,
    *,
    roles=None,
    segments=None,
    engagement_stages=None,
    tags=None,
) -> dict:
    tokens = _tokens(query)
    roles = _norm_list(roles)
    segments = _norm_list(segments)
    engagement_stages = _norm_list(engagement_stages)
    tag_filters = _norm_list(tags)
    has_filters = bool(roles or segments or engagement_stages or tag_filters)

    # Text drives the search; filters can run without it. But with neither, return
    # nothing — a blank search must never dump the whole book.
    if not tokens and not has_filters:
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

    contact_scored = []
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
        # Free text (when present) AND the structured filters both have to pass.
        if tokens and not _matches(haystack, tokens):
            continue
        if not _passes_contact_filters(c, roles, segments, engagement_stages, tag_filters):
            continue
        # Relevance tiers, strongest first. Resolved company fields are the weakest
        # signal (a contact reached via its company is "related to", not "is").
        tiers = [
            f"{c.get('first_name', '')} {c.get('last_name', '')}",
            " ".join([c.get("role", ""), c.get("email", ""), c.get("tags", ""),
                      c.get("segment", ""), c.get("engagement_stage", ""),
                      c.get("platform_handles", ""), c.get("urls", "")]),
            " ".join([c.get("notes", ""), c.get("source", ""), c.get("phone", ""),
                      cname, company.get("industry", ""), company.get("website", "")]),
        ]
        contact_scored.append((_score(tiers, tokens), {
            **c,
            "name": contact_display_name(c),
            "company_name": cname,
        }))
    contact_hits = _ranked(contact_scored)

    # The remaining buckets are text-only: structured filters describe people, not
    # companies/deals/interactions/follow-ups. With no text query they stay empty.
    company_hits = []
    deal_hits = []
    interaction_hits = []
    follow_up_hits = []

    if tokens:
        company_scored = []
        for c in companies:
            haystack = " ".join([
                c.get("name", ""), c.get("industry", ""),
                c.get("website", ""), c.get("notes", ""),
            ]).lower()
            if _matches(haystack, tokens):
                tiers = [c.get("name", ""),
                         " ".join([c.get("industry", ""), c.get("website", "")]),
                         c.get("notes", "")]
                company_scored.append((_score(tiers, tokens), {
                    **c,
                    "name": c.get("name", ""),
                }))
        company_hits = _ranked(company_scored)

        deal_scored = []
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
                tiers = [d.get("title", ""),
                         " ".join([d.get("stage", ""), d.get("priority", ""), d.get("notes", "")]),
                         " ".join([contname, cname])]
                deal_scored.append((_score(tiers, tokens), {
                    **d,
                    "contact_name": contname,
                    "company_name": cname,
                }))
        deal_hits = _ranked(deal_scored)

        interaction_scored = []
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
                tiers = [i.get("subject", ""),
                         " ".join([i.get("body", ""), i.get("type", ""),
                                   i.get("direction", ""), i.get("url", "")]),
                         " ".join([contname, cname, dtitle])]
                interaction_scored.append((_score(tiers, tokens), {
                    **i,
                    "contact_name": contname,
                    "company_name": cname,
                    "deal_title": dtitle,
                }))
        interaction_hits = _ranked(interaction_scored)

        follow_up_scored = []
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
                tiers = [f.get("title", ""),
                         " ".join([f.get("notes", ""), f.get("status", "")]),
                         " ".join([contname, cname, dtitle])]
                follow_up_scored.append((_score(tiers, tokens), {
                    **f,
                    "contact_name": contname,
                    "company_name": cname,
                    "deal_title": dtitle,
                }))
        follow_up_hits = _ranked(follow_up_scored)

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
