from unittest.mock import patch

import pytest

from app.services.sheet_service import DEALS_COLUMNS


class TestDealEndpoints:
    @pytest.fixture
    def seeded_deals_ws(self, mock_worksheet):
        mock_worksheet._headers = DEALS_COLUMNS
        mock_worksheet._data.append([
            "d1", "c1", "comp1", "Website Redesign", "proposal", "50000",
            "USD", "high", "2024-06-01", "Big project",
            "2024-01-01T00:00:00", "2024-01-15T00:00:00",
        ])
        mock_worksheet._data.append([
            "d2", "c2", "comp1", "SEO Campaign", "lead", "10000",
            "USD", "medium", "", "",
            "2024-01-02T00:00:00", "2024-01-02T00:00:00",
        ])
        return mock_worksheet

    def test_list_deals(self, client, auth_headers, seeded_deals_ws):
        with patch("app.routers.deals.deals_sheet._worksheet", return_value=seeded_deals_ws):
            resp = client.get("/api/deals", headers=auth_headers)
            assert resp.status_code == 200
            assert len(resp.json()) == 2

    def test_filter_deals_by_stage(self, client, auth_headers, seeded_deals_ws):
        with patch("app.routers.deals.deals_sheet._worksheet", return_value=seeded_deals_ws):
            resp = client.get("/api/deals?stage=lead", headers=auth_headers)
            assert resp.status_code == 200
            assert len(resp.json()) == 1

    def test_create_deal(self, client, auth_headers, seeded_deals_ws):
        with patch("app.routers.deals.deals_sheet._worksheet", return_value=seeded_deals_ws):
            resp = client.post("/api/deals", headers=auth_headers, json={
                "title": "New Deal",
                "contact_id": "c1",
                "value": "25000",
            })
            assert resp.status_code == 201
            assert resp.json()["title"] == "New Deal"

    def test_update_deal_stage(self, client, auth_headers, seeded_deals_ws):
        with patch("app.routers.deals.deals_sheet._worksheet", return_value=seeded_deals_ws):
            resp = client.patch("/api/deals/d1/stage", headers=auth_headers, json={
                "stage": "negotiation",
            })
            assert resp.status_code == 200
            assert resp.json()["stage"] == "negotiation"

    def test_update_deal_stage_invalid(self, client, auth_headers):
        resp = client.patch("/api/deals/d1/stage", headers=auth_headers, json={
            "stage": "invalid_stage",
        })
        assert resp.status_code == 422
