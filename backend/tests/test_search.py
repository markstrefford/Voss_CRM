"""Unified search must surface entities via resolved foreign keys.

The canonical bug being prevented: searching "Endava" returned zero contacts
even though contacts existed at Endava — because contacts only carry
company_id, not the company name. Same failure mode applies to deals,
interactions, and follow-ups — all of which can only be reached by
resolving FK references into the searchable text.
"""

from unittest.mock import MagicMock

import pytest

from app.services import search_service
from app.services.sheet_service import _cache


@pytest.fixture(autouse=True)
def _clear_cache():
    _cache.clear()
    yield
    _cache.clear()


def _stub_sheet(records: list[dict]) -> MagicMock:
    sheet = MagicMock()
    sheet.get_all.return_value = records
    return sheet


@pytest.fixture
def voss_data(monkeypatch):
    """Two contacts at Endava, no other entities containing the literal 'Endava' string."""
    companies = [
        {"id": "comp_endava", "name": "Endava", "industry": "IT consultancy",
         "website": "endava.com", "notes": ""},
        {"id": "comp_other", "name": "Acme Corp", "industry": "Manufacturing",
         "website": "acme.example", "notes": ""},
    ]
    contacts = [
        {"id": "c_andrew", "company_id": "comp_endava",
         "first_name": "Andrew", "last_name": "Rossiter",
         "email": "andrew@endava.com", "phone": "", "role": "CTO",
         "linkedin_url": "", "platform_handles": "", "urls": "",
         "source": "linkedin", "referral_contact_id": "",
         "tags": "", "notes": "Discussed identity question",
         "status": "active",
         "segment": "", "engagement_stage": "active",
         "inbound_channel": "", "do_not_contact": "", "campaign_id": ""},
        {"id": "c_tom", "company_id": "comp_endava",
         "first_name": "Tom", "last_name": "Vincent",
         "email": "tom@endava.com", "phone": "", "role": "Account Manager",
         "linkedin_url": "", "platform_handles": "", "urls": "",
         "source": "referral", "referral_contact_id": "",
         "tags": "", "notes": "",
         "status": "active",
         "segment": "", "engagement_stage": "new",
         "inbound_channel": "", "do_not_contact": "", "campaign_id": ""},
        {"id": "c_jane", "company_id": "comp_other",
         "first_name": "Jane", "last_name": "Doe",
         "email": "jane@acme.example", "phone": "", "role": "VP",
         "linkedin_url": "", "platform_handles": "", "urls": "",
         "source": "", "referral_contact_id": "",
         "tags": "", "notes": "",
         "status": "active",
         "segment": "", "engagement_stage": "",
         "inbound_channel": "", "do_not_contact": "", "campaign_id": ""},
        {"id": "c_archived", "company_id": "comp_endava",
         "first_name": "Old", "last_name": "Contact",
         "email": "", "phone": "", "role": "",
         "linkedin_url": "", "platform_handles": "", "urls": "",
         "source": "", "referral_contact_id": "",
         "tags": "", "notes": "",
         "status": "archived",
         "segment": "", "engagement_stage": "",
         "inbound_channel": "", "do_not_contact": "", "campaign_id": ""},
    ]
    deals = [
        {"id": "d1", "contact_id": "c_andrew", "company_id": "comp_endava",
         "title": "Platform engagement", "stage": "proposal",
         "value": "150000", "currency": "GBP", "priority": "high",
         "expected_close": "", "notes": ""},
        {"id": "d2", "contact_id": "c_jane", "company_id": "comp_other",
         "title": "Pilot project", "stage": "lead",
         "value": "5000", "currency": "GBP", "priority": "medium",
         "expected_close": "", "notes": ""},
    ]
    interactions = [
        {"id": "i1", "contact_id": "c_andrew", "deal_id": "d1",
         "type": "call", "subject": "Identity discussion",
         "body": "He paused on the identity question",
         "url": "", "direction": "outbound",
         "occurred_at": "2026-04-12T10:00:00", "created_at": "2026-04-12T10:00:00"},
        {"id": "i2", "contact_id": "c_jane", "deal_id": "",
         "type": "email", "subject": "Intro",
         "body": "", "url": "", "direction": "outbound",
         "occurred_at": "2026-04-01", "created_at": "2026-04-01"},
    ]
    follow_ups = [
        {"id": "f1", "contact_id": "c_andrew", "deal_id": "",
         "title": "Capture company contact list",
         "due_date": "2026-05-15", "due_time": "",
         "status": "pending", "reminder_sent": "", "notes": "",
         "created_at": "", "completed_at": ""},
    ]

    monkeypatch.setattr(search_service, "companies_sheet", _stub_sheet(companies))
    monkeypatch.setattr(search_service, "contacts_sheet", _stub_sheet(contacts))
    monkeypatch.setattr(search_service, "deals_sheet", _stub_sheet(deals))
    monkeypatch.setattr(search_service, "interactions_sheet", _stub_sheet(interactions))
    monkeypatch.setattr(search_service, "follow_ups_sheet", _stub_sheet(follow_ups))


def test_company_query_finds_contacts_via_resolved_company_name(voss_data):
    """Searching by company name must surface contacts whose company_id resolves to it."""
    result = search_service.unified_search("Endava")

    contact_ids = {c["id"] for c in result["contacts"]}
    assert "c_andrew" in contact_ids
    assert "c_tom" in contact_ids
    # Acme contact must not match
    assert "c_jane" not in contact_ids
    # Archived contact must not match
    assert "c_archived" not in contact_ids


def test_company_query_finds_company(voss_data):
    result = search_service.unified_search("Endava")
    assert any(c["id"] == "comp_endava" for c in result["companies"])
    assert not any(c["id"] == "comp_other" for c in result["companies"])


def test_company_query_finds_deals_via_company(voss_data):
    """A deal whose company_id points to Endava should match a query for 'Endava'."""
    result = search_service.unified_search("Endava")
    deal_ids = {d["id"] for d in result["deals"]}
    assert "d1" in deal_ids
    assert "d2" not in deal_ids
    # Deal hits should carry resolved company/contact names
    d1 = next(d for d in result["deals"] if d["id"] == "d1")
    assert d1["company_name"] == "Endava"
    assert d1["contact_name"] == "Andrew Rossiter"


def test_company_query_finds_interactions_via_contact_chain(voss_data):
    """An interaction attached to a contact at Endava must match a query for 'Endava' —
    even though the interaction's own fields contain no mention of Endava."""
    result = search_service.unified_search("Endava")
    interaction_ids = {i["id"] for i in result["interactions"]}
    assert "i1" in interaction_ids
    assert "i2" not in interaction_ids
    i1 = next(i for i in result["interactions"] if i["id"] == "i1")
    assert i1["company_name"] == "Endava"
    assert i1["contact_name"] == "Andrew Rossiter"


def test_company_query_finds_follow_ups_via_contact_chain(voss_data):
    result = search_service.unified_search("Endava")
    follow_up_ids = {f["id"] for f in result["follow_ups"]}
    assert "f1" in follow_up_ids
    f1 = next(f for f in result["follow_ups"] if f["id"] == "f1")
    assert f1["company_name"] == "Endava"
    assert f1["contact_name"] == "Andrew Rossiter"


def test_person_name_query(voss_data):
    """Searching a contact's name still works (the prior search behaviour)."""
    result = search_service.unified_search("Andrew Rossiter")
    contact_ids = {c["id"] for c in result["contacts"]}
    assert contact_ids == {"c_andrew"}


def test_multi_token_and_match(voss_data):
    """All tokens must appear (AND semantics)."""
    result = search_service.unified_search("andrew endava")
    contact_ids = {c["id"] for c in result["contacts"]}
    assert contact_ids == {"c_andrew"}
    # Tom matches "endava" but not "andrew" — must be excluded
    assert "c_tom" not in contact_ids


def test_empty_query_returns_zero(voss_data):
    result = search_service.unified_search("")
    assert result["total"] == 0
    assert result["contacts"] == []


def test_unknown_query_returns_zero(voss_data):
    result = search_service.unified_search("nonexistent-token-xyz")
    assert result["total"] == 0


def test_case_insensitive(voss_data):
    lower = search_service.unified_search("endava")
    upper = search_service.unified_search("ENDAVA")
    assert {c["id"] for c in lower["contacts"]} == {c["id"] for c in upper["contacts"]}


def test_total_aggregates_across_categories(voss_data):
    """The reported total must equal the sum of category lengths — the headline
    'N records reference X' figure callers display."""
    result = search_service.unified_search("Endava")
    assert result["total"] == (
        len(result["companies"])
        + len(result["contacts"])
        + len(result["deals"])
        + len(result["interactions"])
        + len(result["follow_ups"])
    )


def _contact(cid, first, last, role, segment, stage, tags, status="active"):
    return {
        "id": cid, "company_id": "", "first_name": first, "last_name": last,
        "email": "", "phone": "", "role": role, "linkedin_url": "",
        "platform_handles": "", "urls": "", "source": "", "referral_contact_id": "",
        "tags": tags, "notes": "", "status": status,
        "segment": segment, "engagement_stage": stage,
        "inbound_channel": "", "do_not_contact": "", "campaign_id": "",
    }


@pytest.fixture
def cohort_data(monkeypatch):
    """A quant cohort plus a non-quant and an archived row, for filter tests."""
    contacts = [
        _contact("q1", "Cara", "Quantly", "Quant Researcher", "Quant", "accepted", "Quant, signal-strata"),
        _contact("q2", "Polly", "Folio", "Portfolio Manager", "Quant", "new", "Quant, direct"),
        _contact("q3", "Ivan", "Vester", "Investment Analyst", "Quant", "accepted", "Quant"),
        _contact("o1", "Otto", "Other", "Software Engineer", "consulting", "new", "eng"),
        _contact("a1", "Arch", "Ived", "Quant Researcher", "Quant", "accepted", "Quant", status="archived"),
    ]
    # A company that itself contains "quant" — proves filters-only never leaks it
    # into the company bucket (filters describe people, not companies).
    companies = [{"id": "co1", "name": "Quant Hedge Fund", "industry": "",
                  "website": "", "notes": ""}]
    monkeypatch.setattr(search_service, "companies_sheet", _stub_sheet(companies))
    monkeypatch.setattr(search_service, "contacts_sheet", _stub_sheet(contacts))
    monkeypatch.setattr(search_service, "deals_sheet", _stub_sheet([]))
    monkeypatch.setattr(search_service, "interactions_sheet", _stub_sheet([]))
    monkeypatch.setattr(search_service, "follow_ups_sheet", _stub_sheet([]))


class TestSearchFilters:
    def test_multi_value_role_is_or(self, cohort_data):
        """The motivating query: three roles in one call returns the union."""
        result = search_service.unified_search(
            "", roles=["quant", "portfolio manager", "investment"])
        assert {c["id"] for c in result["contacts"]} == {"q1", "q2", "q3"}

    def test_single_role_substring(self, cohort_data):
        result = search_service.unified_search("", roles=["portfolio"])
        assert {c["id"] for c in result["contacts"]} == {"q2"}

    def test_role_accepts_bare_string(self, cohort_data):
        result = search_service.unified_search("", roles="investment")
        assert {c["id"] for c in result["contacts"]} == {"q3"}

    def test_segment_exact_match(self, cohort_data):
        result = search_service.unified_search("", segments=["quant"])
        assert {c["id"] for c in result["contacts"]} == {"q1", "q2", "q3"}

    def test_engagement_stage_filter(self, cohort_data):
        result = search_service.unified_search("", engagement_stages=["accepted"])
        assert {c["id"] for c in result["contacts"]} == {"q1", "q3"}

    def test_tags_substring(self, cohort_data):
        result = search_service.unified_search("", tags=["direct"])
        assert {c["id"] for c in result["contacts"]} == {"q2"}

    def test_filters_and_across_kinds(self, cohort_data):
        result = search_service.unified_search(
            "", roles=["quant", "portfolio manager", "investment"],
            engagement_stages=["accepted"])
        assert {c["id"] for c in result["contacts"]} == {"q1", "q3"}

    def test_text_and_filter_combine(self, cohort_data):
        result = search_service.unified_search("researcher", segments=["quant"])
        assert {c["id"] for c in result["contacts"]} == {"q1"}

    def test_filters_only_no_text(self, cohort_data):
        result = search_service.unified_search("", segments=["quant"])
        assert result["total"] == 3

    def test_no_text_no_filters_returns_empty(self, cohort_data):
        result = search_service.unified_search("")
        assert result["total"] == 0
        assert result["contacts"] == []

    def test_archived_excluded_under_filter(self, cohort_data):
        result = search_service.unified_search("", segments=["quant"])
        assert "a1" not in {c["id"] for c in result["contacts"]}

    def test_multi_value_segment(self, cohort_data):
        result = search_service.unified_search("", segments=["quant", "consulting"])
        assert {c["id"] for c in result["contacts"]} == {"q1", "q2", "q3", "o1"}

    def test_filters_only_leaves_non_contact_buckets_empty(self, cohort_data):
        """Even with a 'Quant'-named company present, a filters-only query returns
        only people — the other buckets stay text-driven."""
        result = search_service.unified_search("", segments=["quant"])
        assert result["companies"] == []
        assert result["deals"] == []
        assert result["interactions"] == []
        assert result["follow_ups"] == []
        assert result["total"] == 3


class TestSearchEndpoint:
    def test_endpoint_requires_auth(self, client):
        resp = client.get("/api/search?q=Endava")
        assert resp.status_code == 401

    def test_endpoint_passes_filters(self, client, auth_headers, cohort_data):
        resp = client.get(
            "/api/search?role=quant,portfolio manager,investment", headers=auth_headers)
        assert resp.status_code == 200
        ids = {c["id"] for c in resp.json()["contacts"]}
        assert ids == {"q1", "q2", "q3"}

    def test_endpoint_returns_grouped_payload(self, client, auth_headers, voss_data):
        resp = client.get("/api/search?q=Endava", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["query"] == "Endava"
        for key in ("companies", "contacts", "deals", "interactions", "follow_ups"):
            assert key in body
        contact_ids = {c["id"] for c in body["contacts"]}
        assert {"c_andrew", "c_tom"}.issubset(contact_ids)
