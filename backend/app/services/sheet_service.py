import time
import uuid
from datetime import datetime, timezone

from cachetools import TTLCache

from app.sheets import get_worksheet

# Cache: up to 50 worksheets, 30-second TTL
_cache = TTLCache(maxsize=50, ttl=30)


class SheetService:
    """Generic CRUD over a Google Sheets worksheet tab."""

    def __init__(self, tab_name: str, columns: list[str]):
        self.tab_name = tab_name
        self.columns = columns

    def _worksheet(self):
        return get_worksheet(self.tab_name)

    def _get_all_records(self, force_refresh: bool = False) -> list[dict]:
        cache_key = f"{self.tab_name}_all"
        if not force_refresh and cache_key in _cache:
            return _cache[cache_key]
        ws = self._worksheet()
        records = ws.get_all_records()
        # Convert all values to strings for consistency
        records = [{k: str(v) for k, v in r.items()} for r in records]
        _cache[cache_key] = records
        return records

    def _invalidate_cache(self):
        cache_key = f"{self.tab_name}_all"
        _cache.pop(cache_key, None)

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _new_id(self) -> str:
        return str(uuid.uuid4())[:8]

    def get_all(self, filters: dict | None = None) -> list[dict]:
        records = self._get_all_records()
        if filters:
            for key, value in filters.items():
                if value is not None and value != "":
                    records = [r for r in records if r.get(key, "") == value]
        return records

    def search(self, query: str, search_fields: list[str]) -> list[dict]:
        records = self._get_all_records()
        query_lower = query.lower()
        return [
            r for r in records
            if any(query_lower in str(r.get(f, "")).lower() for f in search_fields)
        ]

    def get_by_id(self, record_id: str) -> dict | None:
        records = self._get_all_records()
        for r in records:
            if r.get("id") == record_id:
                return r
        return None

    def find_by_field(self, field: str, value: str) -> dict | None:
        records = self._get_all_records()
        for r in records:
            if r.get(field) == value:
                return r
        return None

    def bulk_create(self, data_list: list[dict]) -> list[dict]:
        """Batch-insert multiple records in a single API call using append_rows()."""
        if not data_list:
            return []

        now = self._now()
        records = []
        rows = []

        for data in data_list:
            record = {col: "" for col in self.columns}
            record["id"] = self._new_id()
            record["created_at"] = now
            if "updated_at" in self.columns:
                record["updated_at"] = now

            for key, value in data.items():
                if key in record and key not in ("id", "created_at"):
                    record[key] = str(value) if value is not None else ""

            records.append(record)
            rows.append([record.get(col, "") for col in self.columns])

        ws = self._worksheet()
        ws.append_rows(rows, value_input_option="USER_ENTERED")
        self._invalidate_cache()
        return records

    def create(self, data: dict) -> dict:
        record = {col: "" for col in self.columns}
        record["id"] = self._new_id()
        record["created_at"] = self._now()
        if "updated_at" in self.columns:
            record["updated_at"] = self._now()

        for key, value in data.items():
            if key in record and key not in ("id", "created_at"):
                record[key] = str(value) if value is not None else ""

        ws = self._worksheet()
        row = [record.get(col, "") for col in self.columns]
        ws.append_row(row, value_input_option="USER_ENTERED")
        self._invalidate_cache()
        return record

    def update(self, record_id: str, data: dict) -> dict | None:
        ws = self._worksheet()
        records = self._get_all_records(force_refresh=True)

        row_index = None
        record = None
        for i, r in enumerate(records):
            if r.get("id") == record_id:
                row_index = i + 2  # +1 for header, +1 for 1-indexed
                record = r
                break

        if record is None:
            return None

        for key, value in data.items():
            if key in record and key not in ("id", "created_at") and value is not None:
                record[key] = str(value)

        if "updated_at" in self.columns:
            record["updated_at"] = self._now()

        row = [record.get(col, "") for col in self.columns]
        ws.update(f"A{row_index}:{chr(64 + len(self.columns))}{row_index}", [row])
        self._invalidate_cache()
        return record

    def delete(self, record_id: str) -> bool:
        """Soft-delete: set status to 'archived' if status column exists, otherwise actual delete."""
        if "status" in self.columns:
            result = self.update(record_id, {"status": "archived"})
            return result is not None

        ws = self._worksheet()
        records = self._get_all_records(force_refresh=True)
        for i, r in enumerate(records):
            if r.get("id") == record_id:
                ws.delete_rows(i + 2)
                self._invalidate_cache()
                return True
        return False


# Column definitions for each tab
CONTACTS_COLUMNS = [
    "id", "company_id", "first_name", "last_name", "email", "phone",
    "role", "linkedin_url", "urls", "source", "referral_contact_id",
    "tags", "notes", "status",
    "segment", "engagement_stage", "inbound_channel", "do_not_contact", "campaign_id",
    "created_at", "updated_at",
]

COMPANIES_COLUMNS = [
    "id", "name", "industry", "website", "size", "notes",
    "created_at", "updated_at",
]

DEALS_COLUMNS = [
    "id", "contact_id", "company_id", "title", "stage", "value",
    "currency", "priority", "expected_close", "notes",
    "created_at", "updated_at",
]

INTERACTIONS_COLUMNS = [
    "id", "contact_id", "deal_id", "type", "subject", "body",
    "url", "direction", "occurred_at", "created_at",
]

FOLLOW_UPS_COLUMNS = [
    "id", "contact_id", "deal_id", "title", "due_date", "due_time",
    "status", "reminder_sent", "notes", "created_at", "completed_at",
]

USERS_COLUMNS = [
    "id", "username", "password_hash", "telegram_chat_id", "created_at",
]

SCHEDULER_LOG_COLUMNS = [
    "id", "job_name", "last_run_date", "created_at",
]

# Lookup used by sheets.py to auto-create tabs with correct headers
_COLUMNS_BY_TAB = {
    "Contacts": CONTACTS_COLUMNS,
    "Companies": COMPANIES_COLUMNS,
    "Deals": DEALS_COLUMNS,
    "Interactions": INTERACTIONS_COLUMNS,
    "FollowUps": FOLLOW_UPS_COLUMNS,
    "Users": USERS_COLUMNS,
    "SchedulerLog": SCHEDULER_LOG_COLUMNS,
}

# Pre-built service instances
contacts_sheet = SheetService("Contacts", CONTACTS_COLUMNS)
companies_sheet = SheetService("Companies", COMPANIES_COLUMNS)
deals_sheet = SheetService("Deals", DEALS_COLUMNS)
interactions_sheet = SheetService("Interactions", INTERACTIONS_COLUMNS)
follow_ups_sheet = SheetService("FollowUps", FOLLOW_UPS_COLUMNS)
users_sheet = SheetService("Users", USERS_COLUMNS)
scheduler_log_sheet = SheetService("SchedulerLog", SCHEDULER_LOG_COLUMNS)
