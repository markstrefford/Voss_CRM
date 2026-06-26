"""MCP search tool filters (e02-s01-t02).

`tool_search` is a thin wrapper over GET /api/search. These tests assert the
outgoing params (the filters reach the API) and that a filters-only call is
allowed — the search behaviour itself is covered by test_search.py."""

from unittest.mock import patch

_HIT = {"total": 1, "companies": [], "contacts": [
    {"id": "q1", "name": "Cara Quantly", "role": "Quant Researcher"}],
    "deals": [], "interactions": [], "follow_ups": []}


def test_text_only_passes_query():
    from mcp_server.tools.search import search
    with patch("mcp_server.tools.search.api_get") as mock_get:
        mock_get.return_value = _HIT
        search("endava")
    path, params = mock_get.call_args.args
    assert path == "/api/search"
    assert params["q"] == "endava"
    assert "role" not in params  # empty filters omitted


def test_filters_passed_through():
    from mcp_server.tools.search import search
    with patch("mcp_server.tools.search.api_get") as mock_get:
        mock_get.return_value = _HIT
        search("", role="quant, portfolio manager, investment", segment="Quant",
               engagement_stage="accepted", tags="signal-strata")
    _, params = mock_get.call_args.args
    assert params["role"] == "quant, portfolio manager, investment"
    assert params["segment"] == "Quant"
    assert params["engagement_stage"] == "accepted"
    assert params["tags"] == "signal-strata"


def test_filters_only_zero_results_message():
    """A filters-only miss must not read 'No VOSS records reference ...'."""
    from mcp_server.tools.search import search
    empty = {"total": 0, "companies": [], "contacts": [],
             "deals": [], "interactions": [], "follow_ups": []}
    with patch("mcp_server.tools.search.api_get") as mock_get:
        mock_get.return_value = empty
        result = search("", segment="Nope")
    assert result == "No VOSS records match those filters."


def test_filters_only_is_allowed():
    """A filters-only call (no text) must reach the API, not the guard."""
    from mcp_server.tools.search import search
    with patch("mcp_server.tools.search.api_get") as mock_get:
        mock_get.return_value = _HIT
        result = search("", segment="Quant")
    mock_get.assert_called_once()
    assert "Cara Quantly" in result


def test_no_text_no_filters_returns_guard():
    from mcp_server.tools.search import search
    with patch("mcp_server.tools.search.api_get") as mock_get:
        result = search("   ")
    assert result == "Provide a search query or a filter."
    mock_get.assert_not_called()
