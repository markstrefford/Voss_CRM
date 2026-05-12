from contextlib import ExitStack
from unittest.mock import patch

import pytest

from app.services.sheet_service import _cache


class TestContactEndpoints:
    def test_list_contacts(self, client, auth_headers, seeded_contacts_ws):
        with patch("app.routers.contacts.contacts_sheet._worksheet", return_value=seeded_contacts_ws):
            resp = client.get("/api/contacts", headers=auth_headers)
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 2
            assert data[0]["first_name"] == "John"

    def test_list_contacts_no_auth(self, client):
        resp = client.get("/api/contacts")
        assert resp.status_code == 401

    def test_filter_by_tag(self, client, auth_headers, seeded_contacts_ws):
        with patch("app.routers.contacts.contacts_sheet._worksheet", return_value=seeded_contacts_ws):
            resp = client.get("/api/contacts?tag=vip", headers=auth_headers)
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 1
            assert data[0]["first_name"] == "John"

    def test_create_contact(self, client, auth_headers, seeded_contacts_ws):
        with patch("app.routers.contacts.contacts_sheet._worksheet", return_value=seeded_contacts_ws):
            resp = client.post("/api/contacts", headers=auth_headers, json={
                "first_name": "Alice",
                "last_name": "Wonder",
                "email": "alice@example.com",
            })
            assert resp.status_code == 201
            data = resp.json()
            assert data["first_name"] == "Alice"
            assert data["id"] != ""

    def test_create_contact_missing_name(self, client, auth_headers):
        resp = client.post("/api/contacts", headers=auth_headers, json={
            "email": "noname@example.com",
        })
        assert resp.status_code == 422

    def test_get_contact(self, client, auth_headers, seeded_contacts_ws):
        with patch("app.routers.contacts.contacts_sheet._worksheet", return_value=seeded_contacts_ws):
            resp = client.get("/api/contacts/c1", headers=auth_headers)
            assert resp.status_code == 200
            assert resp.json()["first_name"] == "John"

    def test_get_contact_not_found(self, client, auth_headers, seeded_contacts_ws):
        with patch("app.routers.contacts.contacts_sheet._worksheet", return_value=seeded_contacts_ws):
            resp = client.get("/api/contacts/nonexistent", headers=auth_headers)
            assert resp.status_code == 404

    def test_update_contact(self, client, auth_headers, seeded_contacts_ws):
        with patch("app.routers.contacts.contacts_sheet._worksheet", return_value=seeded_contacts_ws):
            resp = client.put("/api/contacts/c1", headers=auth_headers, json={
                "role": "VP Engineering",
            })
            assert resp.status_code == 200
            assert resp.json()["role"] == "VP Engineering"

    def test_delete_contact(self, client, auth_headers, seeded_contacts_ws):
        with patch("app.routers.contacts.contacts_sheet._worksheet", return_value=seeded_contacts_ws):
            resp = client.delete("/api/contacts/c1", headers=auth_headers)
            assert resp.status_code == 204

    def test_xss_in_contact_name(self, client, auth_headers, seeded_contacts_ws):
        """XSS payloads should be stored as plain text, not executed."""
        with patch("app.routers.contacts.contacts_sheet._worksheet", return_value=seeded_contacts_ws):
            resp = client.post("/api/contacts", headers=auth_headers, json={
                "first_name": "<script>alert('xss')</script>",
                "notes": "<img onerror='alert(1)' src=x>",
            })
            assert resp.status_code == 201
            data = resp.json()
            assert data["first_name"] == "<script>alert('xss')</script>"
            assert data["notes"] == "<img onerror='alert(1)' src=x>"


def _patch_both(contacts_ws, companies_ws):
    """Patch the contacts and companies sheet worksheets simultaneously,
    and clear the SheetService cache so reads/writes don't leak between
    sub-cases. Returns an ExitStack — use as a context manager."""
    _cache.clear()
    stack = ExitStack()
    stack.enter_context(patch(
        "app.services.sheet_service.contacts_sheet._worksheet",
        return_value=contacts_ws,
    ))
    stack.enter_context(patch(
        "app.services.sheet_service.companies_sheet._worksheet",
        return_value=companies_ws,
    ))
    return stack


class TestContactCompanyNameResolution:
    """t01: POST /api/contacts and PUT /api/contacts/{id} must accept
    company_name and resolve it to company_id, creating the company if
    missing — and stop silently dropping the field."""

    def test_create_contact_with_company_name_creates_company_if_missing(
        self, client, auth_headers, seeded_contacts_ws, empty_companies_ws,
    ):
        with _patch_both(seeded_contacts_ws, empty_companies_ws):
            resp = client.post("/api/contacts", headers=auth_headers, json={
                "first_name": "Andrew",
                "last_name": "Rossiter",
                "company_name": "NewCo",
            })
            assert resp.status_code == 201
            data = resp.json()
            assert data["company_id"], "company_id should be populated after resolution"

            companies_resp = client.get("/api/companies", headers=auth_headers)
            assert companies_resp.status_code == 200
            company_names = {c["name"] for c in companies_resp.json()}
            assert "NewCo" in company_names

    def test_create_contact_with_company_name_links_existing_company(
        self, client, auth_headers, seeded_contacts_ws, seeded_companies_ws,
    ):
        with _patch_both(seeded_contacts_ws, seeded_companies_ws):
            companies_before = client.get("/api/companies", headers=auth_headers).json()
            existing = next(c for c in companies_before if c["name"] == "Existing Ltd")

            resp = client.post("/api/contacts", headers=auth_headers, json={
                "first_name": "Linked",
                "company_name": "Existing Ltd",
            })
            assert resp.status_code == 201
            assert resp.json()["company_id"] == existing["id"]

            companies_after = client.get("/api/companies", headers=auth_headers).json()
            assert len(companies_after) == len(companies_before), \
                "no duplicate company should be created when name matches"

    def test_update_contact_with_company_name_resolves_and_creates(
        self, client, auth_headers, seeded_contacts_ws, empty_companies_ws,
    ):
        with _patch_both(seeded_contacts_ws, empty_companies_ws):
            resp = client.put(
                "/api/contacts/c1",
                headers=auth_headers,
                json={"company_name": "FreshCo"},
            )
            assert resp.status_code == 200
            new_cid = resp.json()["company_id"]
            assert new_cid

            companies = client.get("/api/companies", headers=auth_headers).json()
            assert any(c["id"] == new_cid and c["name"] == "FreshCo" for c in companies)

    def test_update_contact_moves_to_existing_company_by_name(
        self, client, auth_headers, seeded_contacts_ws, seeded_companies_ws,
    ):
        with _patch_both(seeded_contacts_ws, seeded_companies_ws):
            target = next(
                c for c in client.get("/api/companies", headers=auth_headers).json()
                if c["name"] == "Existing Ltd"
            )
            resp = client.put(
                "/api/contacts/c1",
                headers=auth_headers,
                json={"company_name": "Existing Ltd"},
            )
            assert resp.status_code == 200
            assert resp.json()["company_id"] == target["id"]

    def test_update_contact_without_company_name_preserves_company_id(
        self, client, auth_headers, seeded_contacts_ws, seeded_companies_ws,
    ):
        with _patch_both(seeded_contacts_ws, seeded_companies_ws):
            before = client.get("/api/contacts/c1", headers=auth_headers).json()
            original_cid = before["company_id"]

            resp = client.put(
                "/api/contacts/c1",
                headers=auth_headers,
                json={"email": "newaddr@example.com"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["company_id"] == original_cid
            assert data["email"] == "newaddr@example.com"

    def test_company_name_takes_precedence_over_company_id(
        self, client, auth_headers, seeded_contacts_ws, seeded_companies_ws,
    ):
        with _patch_both(seeded_contacts_ws, seeded_companies_ws):
            real = next(
                c for c in client.get("/api/companies", headers=auth_headers).json()
                if c["name"] == "Existing Ltd"
            )
            resp = client.post("/api/contacts", headers=auth_headers, json={
                "first_name": "Y",
                "company_name": "Existing Ltd",
                "company_id": "wrong-id",
            })
            assert resp.status_code == 201
            assert resp.json()["company_id"] == real["id"]
            assert resp.json()["company_id"] != "wrong-id"
