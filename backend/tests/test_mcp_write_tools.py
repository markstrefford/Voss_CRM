"""MCP write-side enrichment tools (e01-s01-t02..t05).

Each tool is a thin wrapper over an existing HTTP endpoint, so these tests
assert the *outgoing* shape (path + body) and the *returned* confirmation —
the API behaviour itself is covered by router-level tests."""

from unittest.mock import patch

import pytest


class TestUpdateContact:
    """t02 — `update_contact` wraps PUT /api/contacts/{id}."""

    def test_sends_only_non_empty_fields(self):
        from mcp_server.tools.contacts import update_contact
        with patch("mcp_server.tools.contacts.api_put") as mock_put:
            mock_put.return_value = {"id": "c1", "first_name": "Tim", "last_name": "Kiel"}
            update_contact(contact_id="c1", email="tim.kiel@serco.com", phone="")
        mock_put.assert_called_once_with("/api/contacts/c1", {"email": "tim.kiel@serco.com"})

    def test_returns_named_confirmation(self):
        from mcp_server.tools.contacts import update_contact
        with patch("mcp_server.tools.contacts.api_put") as mock_put:
            mock_put.return_value = {"id": "c1", "first_name": "Tim", "last_name": "Kiel"}
            result = update_contact(contact_id="c1", email="x@y.com")
        assert "Tim Kiel" in result
        assert "c1" in result

    def test_no_fields_returns_message_without_api_call(self):
        from mcp_server.tools.contacts import update_contact
        with patch("mcp_server.tools.contacts.api_put") as mock_put:
            result = update_contact(contact_id="c1")
        assert result == "No fields to update."
        mock_put.assert_not_called()

    def test_forwards_company_name(self):
        """company_name must reach the API as-is so resolution happens server-side
        (t01 covers the resolution itself). Closes the silent-drop bug class."""
        from mcp_server.tools.contacts import update_contact
        with patch("mcp_server.tools.contacts.api_put") as mock_put:
            mock_put.return_value = {"id": "c1", "first_name": "Tim", "last_name": "Kiel"}
            update_contact(contact_id="c1", company_name="Serco")
        called_path, called_body = mock_put.call_args.args
        assert called_path == "/api/contacts/c1"
        assert called_body.get("company_name") == "Serco"

    # End-to-end company-create-if-missing coverage (AC2 from story spec)
    # is covered by t01's TestContactCompanyNameResolution against the API
    # directly. Wiring the MCP client into the test client through dual
    # API-key + JWT auth makes the integration test brittle relative to
    # the value it adds — the unit tests above prove the MCP layer forwards
    # the call correctly, and t01's tests prove the API resolves it.
