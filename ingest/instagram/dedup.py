"""Simple in-memory deduplication for webhook events."""

from collections import OrderedDict

MAX_EVENTS = 1000

_seen: OrderedDict[str, bool] = OrderedDict()


def is_duplicate(event_id: str) -> bool:
    """Return True if this event ID has been seen before."""
    if event_id in _seen:
        return True
    _seen[event_id] = True
    # Prune oldest entries if we exceed the limit
    while len(_seen) > MAX_EVENTS:
        _seen.popitem(last=False)
    return False
