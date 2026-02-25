from unittest.mock import patch

import pytest


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
        assert resp.status_code == 403

    def test_search_contacts(self, client, auth_headers, seeded_contacts_ws):
        with patch("app.routers.contacts.contacts_sheet._worksheet", return_value=seeded_contacts_ws):
            resp = client.get("/api/contacts?q=John", headers=auth_headers)
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 1
            assert data[0]["first_name"] == "John"

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
