import gspread
from google.oauth2.service_account import Credentials

from app.config import settings

_client: gspread.Client | None = None
_spreadsheet: gspread.Spreadsheet | None = None

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def get_gspread_client() -> gspread.Client:
    global _client
    if _client is None:
        creds_dict = settings.google_credentials_dict
        if creds_dict is None:
            raise RuntimeError("Google Sheets credentials not configured")
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        _client = gspread.authorize(creds)
    return _client


def get_spreadsheet() -> gspread.Spreadsheet:
    global _spreadsheet
    if _spreadsheet is None:
        client = get_gspread_client()
        _spreadsheet = client.open_by_key(settings.google_sheet_id)
    return _spreadsheet


def get_worksheet(tab_name: str) -> gspread.Worksheet:
    spreadsheet = get_spreadsheet()
    try:
        return spreadsheet.worksheet(tab_name)
    except gspread.exceptions.WorksheetNotFound:
        # Auto-create the tab with column headers from SheetService
        from app.services.sheet_service import _COLUMNS_BY_TAB
        cols = _COLUMNS_BY_TAB.get(tab_name, [])
        ws = spreadsheet.add_worksheet(title=tab_name, rows=100, cols=max(len(cols), 1))
        if cols:
            ws.append_row(cols, value_input_option="USER_ENTERED")
        return ws
