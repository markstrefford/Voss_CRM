from unittest.mock import patch

import pytest

from app.services.sheet_service import SheetService, _cache


class TestSheetService:
    @pytest.fixture(autouse=True)
    def clear_cache(self):
        _cache.clear()
        yield
        _cache.clear()

    @pytest.fixture
    def service(self, mock_worksheet):
        columns = ["id", "name", "email", "status", "created_at", "updated_at"]
        mock_worksheet._headers = columns
        svc = SheetService("TestTab", columns)
        with patch.object(svc, "_worksheet", return_value=mock_worksheet):
            yield svc

    def test_create(self, service):
        result = service.create({"name": "Alice", "email": "alice@test.com"})
        assert result["name"] == "Alice"
        assert result["email"] == "alice@test.com"
        assert result["id"] != ""
        assert result["created_at"] != ""

    def test_get_all(self, service):
        service.create({"name": "Alice", "email": "alice@test.com"})
        service.create({"name": "Bob", "email": "bob@test.com"})
        results = service.get_all()
        assert len(results) == 2

    def test_get_all_with_filter(self, service):
        service.create({"name": "Alice", "email": "alice@test.com", "status": "active"})
        service.create({"name": "Bob", "email": "bob@test.com", "status": "inactive"})
        results = service.get_all({"status": "active"})
        assert len(results) == 1
        assert results[0]["name"] == "Alice"

    def test_get_by_id(self, service):
        created = service.create({"name": "Alice"})
        found = service.get_by_id(created["id"])
        assert found is not None
        assert found["name"] == "Alice"

    def test_get_by_id_not_found(self, service):
        assert service.get_by_id("nonexistent") is None

    def test_find_by_field(self, service):
        service.create({"name": "Alice", "email": "alice@test.com"})
        found = service.find_by_field("email", "alice@test.com")
        assert found is not None
        assert found["name"] == "Alice"

    def test_search(self, service):
        service.create({"name": "Alice"})
        service.create({"name": "Bob"})
        results = service.search("ali", ["name"])
        assert len(results) == 1
        assert results[0]["name"] == "Alice"

    def test_update(self, service):
        created = service.create({"name": "Alice"})
        updated = service.update(created["id"], {"name": "Alice Updated"})
        assert updated is not None
        assert updated["name"] == "Alice Updated"

    def test_update_not_found(self, service):
        assert service.update("nonexistent", {"name": "test"}) is None

    def test_delete_soft(self, service):
        created = service.create({"name": "Alice", "status": "active"})
        assert service.delete(created["id"])

    def test_cache_invalidation(self, service):
        service.create({"name": "Alice"})
        assert len(service.get_all()) == 1
        service.create({"name": "Bob"})
        assert len(service.get_all()) == 2
