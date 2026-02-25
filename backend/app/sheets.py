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
    return spreadsheet.worksheet(tab_name)
