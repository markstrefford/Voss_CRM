"""Company tools — calls VOSS API over HTTP."""

from mcp_server.api_client import api_put


_UPDATE_FIELDS = ("name", "industry", "website", "size", "notes")


def update_company(
    company_id: str,
    name: str = "",
    industry: str = "",
    website: str = "",
    size: str = "",
    notes: str = "",
) -> str:
    """Update a company record. Use this when you've learned something about
    a company (industry, website, size, notes) so the fact lands on the
    company entity rather than buried in an interaction note."""
    payload = {k: v for k, v in locals().items() if k in _UPDATE_FIELDS and v}
    if not payload:
        return "No fields to update."
    record = api_put(f"/api/companies/{company_id}", payload)
    display = record.get("name") or company_id
    return f"Updated company **{display}** (ID: {company_id})."
