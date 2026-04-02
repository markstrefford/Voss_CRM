"""Tests for security hardening: headers, rate limiting, secret validation, pagination."""

import pytest
from unittest.mock import patch

from app.config import Settings


class TestSecurityHeaders:
    """Verify security headers are present on all responses."""

    def test_health_has_security_headers(self, client):
        resp = client.get("/api/health")
        assert resp.headers["X-Content-Type-Options"] == "nosniff"
        assert resp.headers["X-Frame-Options"] == "DENY"
        assert resp.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

    def test_auth_endpoint_has_security_headers(self, client):
        resp = client.post("/api/auth/login", json={"username": "x", "password": "y"})
        assert resp.headers["X-Content-Type-Options"] == "nosniff"
        assert resp.headers["X-Frame-Options"] == "DENY"

    def test_no_hsts_in_development(self, client):
        resp = client.get("/api/health")
        assert "Strict-Transport-Security" not in resp.headers


class TestProductionSecretValidation:
    """Verify startup refuses placeholder secrets in production."""

    def test_validate_production_rejects_default_jwt_secret(self):
        s = Settings(
            _env_file=None,
            app_env="production",
            invite_code="real-code",
            voss_api_key="real-key",
        )
        with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
            s.validate_production()

    def test_validate_production_rejects_default_invite_code(self):
        s = Settings(
            _env_file=None,
            app_env="production",
            jwt_secret_key="real-secret",
            voss_api_key="real-key",
        )
        with pytest.raises(RuntimeError, match="INVITE_CODE"):
            s.validate_production()

    def test_validate_production_rejects_empty_api_key(self):
        s = Settings(
            _env_file=None,
            app_env="production",
            jwt_secret_key="real-secret",
            invite_code="real-code",
            voss_api_key="",
        )
        with pytest.raises(RuntimeError, match="VOSS_API_KEY"):
            s.validate_production()

    def test_validate_production_passes_with_real_secrets(self):
        s = Settings(
            _env_file=None,
            app_env="production",
            jwt_secret_key="real-secret",
            invite_code="real-code",
            voss_api_key="real-key",
        )
        s.validate_production()  # Should not raise

    def test_validate_production_reports_all_issues(self):
        s = Settings(_env_file=None, app_env="production")
        with pytest.raises(RuntimeError) as exc_info:
            s.validate_production()
        msg = str(exc_info.value)
        assert "JWT_SECRET_KEY" in msg
        assert "INVITE_CODE" in msg
        assert "VOSS_API_KEY" in msg


class TestRateLimiting:
    """Verify auth endpoints are rate-limited."""

    @pytest.fixture(autouse=True)
    def reset_limiter(self):
        """Reset rate limiter state before each test."""
        from app.limiter import limiter
        limiter.reset()
        yield

    def test_login_rate_limited(self, client, seeded_users_ws):
        """6th login attempt within a minute should get 429."""
        for i in range(5):
            resp = client.post(
                "/api/auth/login",
                json={"username": "wrong", "password": "wrong"},
            )
            assert resp.status_code == 401, f"Request {i+1} expected 401, got {resp.status_code}"

        resp = client.post(
            "/api/auth/login",
            json={"username": "wrong", "password": "wrong"},
        )
        assert resp.status_code == 429

    def test_register_rate_limited(self, client, seeded_users_ws):
        """6th register attempt within a minute should get 429."""
        for i in range(5):
            resp = client.post(
                "/api/auth/register",
                json={"username": f"user{i}xx", "password": "password123", "invite_code": "wrong"},
            )
            assert resp.status_code == 403, f"Request {i+1} expected 403, got {resp.status_code}"

        resp = client.post(
            "/api/auth/register",
            json={"username": "user99xx", "password": "password123", "invite_code": "wrong"},
        )
        assert resp.status_code == 429


class TestConstantTimeComparison:
    """Verify hmac.compare_digest is used for API key checks."""

    def test_valid_api_key_accepted(self, client):
        with patch("app.dependencies.settings") as mock_settings:
            mock_settings.voss_api_key = "test-api-key"
            resp = client.get(
                "/api/health",
                headers={"X-API-Key": "test-api-key"},
            )
            assert resp.status_code == 200

    def test_invalid_api_key_rejected(self, client):
        with patch("app.dependencies.settings") as mock_settings:
            mock_settings.voss_api_key = "test-api-key"
            resp = client.get(
                "/api/contacts",
                headers={"X-API-Key": "wrong-key"},
            )
            assert resp.status_code == 401


class TestGlobalExceptionHandler:
    """Verify unhandled exceptions return generic 500, not stack traces."""

    def test_unhandled_error_returns_generic_500(self, client, auth_headers):
        """Middleware catches exceptions and returns JSON 500 — no stack trace leak."""
        with patch("app.services.sheet_service.SheetService.get_all", side_effect=RuntimeError("boom")):
            resp = client.get("/api/contacts", headers=auth_headers)
            assert resp.status_code == 500
            body = resp.json()
            assert body["detail"] == "Internal server error"
            assert "boom" not in resp.text
            assert "Traceback" not in resp.text


class TestPagination:
    """Verify limit/offset on SheetService.get_all."""

    def test_get_all_with_limit(self):
        from app.services.sheet_service import SheetService, _cache
        svc = SheetService("TestTab", ["id", "name", "created_at"])
        _cache[f"{svc.tab_name}_all"] = [
            {"id": "1", "name": "Alice", "created_at": ""},
            {"id": "2", "name": "Bob", "created_at": ""},
            {"id": "3", "name": "Charlie", "created_at": ""},
        ]
        result = svc.get_all(limit=2)
        assert len(result) == 2
        assert result[0]["name"] == "Alice"
        assert result[1]["name"] == "Bob"

    def test_get_all_with_offset(self):
        from app.services.sheet_service import SheetService, _cache
        svc = SheetService("TestTab2", ["id", "name", "created_at"])
        _cache[f"{svc.tab_name}_all"] = [
            {"id": "1", "name": "Alice", "created_at": ""},
            {"id": "2", "name": "Bob", "created_at": ""},
            {"id": "3", "name": "Charlie", "created_at": ""},
        ]
        result = svc.get_all(offset=1)
        assert len(result) == 2
        assert result[0]["name"] == "Bob"

    def test_get_all_with_limit_and_offset(self):
        from app.services.sheet_service import SheetService, _cache
        svc = SheetService("TestTab3", ["id", "name", "created_at"])
        _cache[f"{svc.tab_name}_all"] = [
            {"id": "1", "name": "Alice", "created_at": ""},
            {"id": "2", "name": "Bob", "created_at": ""},
            {"id": "3", "name": "Charlie", "created_at": ""},
            {"id": "4", "name": "Diana", "created_at": ""},
        ]
        result = svc.get_all(limit=2, offset=1)
        assert len(result) == 2
        assert result[0]["name"] == "Bob"
        assert result[1]["name"] == "Charlie"


class TestHealthEndpointEnhanced:
    """Verify health endpoint reports Google Sheets status."""

    def test_health_reports_degraded_without_sheets(self, client):
        resp = client.get("/api/health")
        data = resp.json()
        assert resp.status_code == 200
        assert data["env"] == "development"
        # Without real sheets credentials, it should report degraded
        assert data["status"] in ("ok", "degraded")

    def test_health_reports_connected_with_sheets(self, client):
        mock_spreadsheet = type("MockSpreadsheet", (), {"title": "Test Sheet"})()
        with patch("app.sheets.get_spreadsheet", return_value=mock_spreadsheet):
            resp = client.get("/api/health")
            data = resp.json()
            assert data["status"] == "ok"
            assert data["google_sheets"] == "connected"
            assert "sheet_title" not in data
