"""Shared helpers for MCP tool modules."""

from app.helpers import contact_display_name
from app.services.sheet_service import contacts_sheet, companies_sheet


def resolve_contact_name(contact_id: str) -> str:
    """Return 'First Last' for a contact ID, or the raw ID if not found."""
    if not contact_id:
        return "Unknown"
    contact = contacts_sheet.get_by_id(contact_id)
    return contact_display_name(contact, fallback=contact_id)


def resolve_company_name(company_id: str) -> str:
    """Return company name for a company ID, or the raw ID if not found."""
    if not company_id:
        return ""
    company = companies_sheet.get_by_id(company_id)
    if not company:
        return company_id
    return company.get("name", "") or company_id


def format_currency(value: str, currency: str = "USD") -> str:
    """Format a numeric string as currency."""
    try:
        amount = float(value)
        if amount == int(amount):
            return f"${int(amount):,}"
        return f"${amount:,.2f}"
    except (ValueError, TypeError):
        return value or "$0"
