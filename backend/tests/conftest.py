from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.auth import create_access_token, hash_password


@pytest.fixture
def mock_worksheet():
    """Mock gspread worksheet with in-memory data."""
    ws = MagicMock()
    ws._data = []
    ws._headers = []

    def get_all_records():
        if not ws._data:
            return []
        return [
            {ws._headers[i]: str(row[i]) for i in range(len(ws._headers))}
            for row in ws._data
        ]

    def append_row(row, **kwargs):
        ws._data.append(row)

    def delete_rows(idx):
        ws._data.pop(idx - 2)  # -2 for header + 1-indexed

    def update(range_str, values):
        import re
        match = re.match(r"A(\d+)", range_str)
        if match:
            row_idx = int(match.group(1)) - 2
            if 0 <= row_idx < len(ws._data):
                ws._data[row_idx] = values[0]

    ws.get_all_records = get_all_records
    ws.append_row = append_row
    ws.delete_rows = delete_rows
    ws.update = update
    return ws


@pytest.fixture
def mock_sheets(mock_worksheet):
    """Patch get_worksheet to return the mock."""
    with patch("app.services.sheet_service.get_worksheet", return_value=mock_worksheet):
        # Clear caches
        from app.services.sheet_service import _cache
        _cache.clear()
        yield mock_worksheet


@pytest.fixture
def auth_token():
    """Generate a valid JWT token for testing."""
    return create_access_token({"sub": "test-id", "username": "testuser"})


@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def client(mock_sheets):
    from app.main import app
    return TestClient(app)


@pytest.fixture
def seeded_users_ws(mock_worksheet):
    """Pre-seed the users worksheet with a test user."""
    from app.services.sheet_service import USERS_COLUMNS
    mock_worksheet._headers = USERS_COLUMNS
    mock_worksheet._data.append([
        "test-id", "testuser", hash_password("testpassword123"), "", "2024-01-01T00:00:00"
    ])
    return mock_worksheet


@pytest.fixture
def seeded_contacts_ws(mock_worksheet):
    """Pre-seed contacts worksheet."""
    from app.services.sheet_service import CONTACTS_COLUMNS
    mock_worksheet._headers = CONTACTS_COLUMNS
    mock_worksheet._data.append([
        "c1", "comp1", "John", "Smith", "john@example.com", "+1234567890",
        "CTO", "https://linkedin.com/in/jsmith", "", "referral", "",
        "tech,vip", "Met at conference", "active", "2024-01-01T00:00:00", "2024-01-01T00:00:00",
    ])
    mock_worksheet._data.append([
        "c2", "comp1", "Jane", "Doe", "jane@example.com", "",
        "CEO", "", "", "linkedin", "",
        "decision-maker", "", "active", "2024-01-02T00:00:00", "2024-01-02T00:00:00",
    ])
    return mock_worksheet
