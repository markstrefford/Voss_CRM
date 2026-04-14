"""Shared helpers for MCP tool modules."""


def format_currency(value: str, currency: str = "GBP") -> str:
    """Format a numeric string as currency."""
    symbols = {"GBP": "\u00a3", "USD": "$", "EUR": "\u20ac"}
    symbol = symbols.get(currency, currency + " ")
    try:
        amount = float(value)
        if amount == int(amount):
            return f"{symbol}{int(amount):,}"
        return f"{symbol}{amount:,.2f}"
    except (ValueError, TypeError):
        return f"{symbol}0"


def contact_name(contact: dict) -> str:
    """Return 'First Last' from a contact dict."""
    first = contact.get("first_name", "")
    last = contact.get("last_name", "")
    return f"{first} {last}".strip() or "Unknown"
