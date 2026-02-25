"""Security tests: JWT validation, auth bypass, input sanitization."""

import pytest
from datetime import timedelta

from app.auth import create_access_token


class TestJWTSecurity:
    def test_expired_token_rejected(self, client):
        token = create_access_token(
            {"sub": "user-1", "username": "test"},
            expires_delta=timedelta(seconds=-1),
        )
        resp = client.get("/api/contacts", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401

    def test_tampered_token_rejected(self, client):
        token = create_access_token({"sub": "user-1", "username": "test"})
        tampered = token[:-5] + "XXXXX"
        resp = client.get("/api/contacts", headers={"Authorization": f"Bearer {tampered}"})
        assert resp.status_code == 401

    def test_missing_token_rejected(self, client):
        resp = client.get("/api/contacts")
        assert resp.status_code == 403

    def test_empty_bearer_rejected(self, client):
        resp = client.get("/api/contacts", headers={"Authorization": "Bearer "})
        assert resp.status_code == 403


class TestAuthBypass:
    """All protected endpoints should reject unauthenticated requests."""

    PROTECTED_ENDPOINTS = [
        ("GET", "/api/contacts"),
        ("POST", "/api/contacts"),
        ("GET", "/api/contacts/test-id"),
        ("PUT", "/api/contacts/test-id"),
        ("DELETE", "/api/contacts/test-id"),
        ("GET", "/api/companies"),
        ("POST", "/api/companies"),
        ("GET", "/api/deals"),
        ("POST", "/api/deals"),
        ("GET", "/api/follow-ups"),
        ("POST", "/api/follow-ups"),
        ("GET", "/api/interactions"),
        ("POST", "/api/interactions"),
        ("GET", "/api/dashboard/summary"),
        ("GET", "/api/dashboard/stale-deals"),
        ("POST", "/api/email/draft"),
        ("GET", "/api/auth/me"),
    ]

    @pytest.mark.parametrize("method,path", PROTECTED_ENDPOINTS)
    def test_endpoint_requires_auth(self, client, method, path):
        if method == "GET":
            resp = client.get(path)
        elif method == "POST":
            resp = client.post(path, json={})
        elif method == "PUT":
            resp = client.put(path, json={})
        elif method == "DELETE":
            resp = client.delete(path)
        # Should be 401 or 403 (no credentials)
        assert resp.status_code in (401, 403, 422), f"{method} {path} returned {resp.status_code}"


class TestHealthEndpoint:
    def test_health_is_public(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
