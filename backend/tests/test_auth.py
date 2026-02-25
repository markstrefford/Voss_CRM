from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.auth import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_and_verify(self):
        password = "mysecretpassword"
        hashed = hash_password(password)
        assert hashed != password
        assert verify_password(password, hashed)

    def test_wrong_password(self):
        hashed = hash_password("correct")
        assert not verify_password("wrong", hashed)


class TestJWT:
    def test_create_and_decode(self):
        data = {"sub": "user-123", "username": "testuser"}
        token = create_access_token(data)
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["username"] == "testuser"

    def test_invalid_token(self):
        assert decode_access_token("invalid.token.here") is None

    def test_tampered_token(self):
        token = create_access_token({"sub": "user-123"})
        # Tamper with the token
        parts = token.split(".")
        parts[1] = parts[1][:-2] + "XX"
        tampered = ".".join(parts)
        assert decode_access_token(tampered) is None


class TestAuthEndpoints:
    def test_login_success(self, client, seeded_users_ws):
        with patch("app.routers.auth.users_sheet._worksheet", return_value=seeded_users_ws):
            resp = client.post("/api/auth/login", json={
                "username": "testuser",
                "password": "testpassword123",
            })
            assert resp.status_code == 200
            assert "access_token" in resp.json()

    def test_login_wrong_password(self, client, seeded_users_ws):
        with patch("app.routers.auth.users_sheet._worksheet", return_value=seeded_users_ws):
            resp = client.post("/api/auth/login", json={
                "username": "testuser",
                "password": "wrongpassword",
            })
            assert resp.status_code == 401

    def test_login_nonexistent_user(self, client, seeded_users_ws):
        with patch("app.routers.auth.users_sheet._worksheet", return_value=seeded_users_ws):
            resp = client.post("/api/auth/login", json={
                "username": "nobody",
                "password": "whatever",
            })
            assert resp.status_code == 401

    def test_register_success(self, client):
        resp = client.post("/api/auth/register", json={
            "username": "newuser",
            "password": "newpassword123",
            "invite_code": "change-me",
        })
        assert resp.status_code == 201
        assert "access_token" in resp.json()

    def test_register_bad_invite_code(self, client):
        resp = client.post("/api/auth/register", json={
            "username": "newuser",
            "password": "newpassword123",
            "invite_code": "wrong-code",
        })
        assert resp.status_code == 403

    def test_me_authenticated(self, client, auth_headers, seeded_users_ws):
        with patch("app.routers.auth.users_sheet._worksheet", return_value=seeded_users_ws):
            resp = client.get("/api/auth/me", headers=auth_headers)
            assert resp.status_code == 200
            data = resp.json()
            assert data["username"] == "testuser"
            assert "password_hash" not in data

    def test_me_no_token(self, client):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 403

    def test_me_invalid_token(self, client):
        resp = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid"})
        assert resp.status_code == 401
