import json
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Google Sheets
    google_sheets_credentials_json: str = ""
    google_sheet_id: str = ""

    # JWT
    jwt_secret_key: str = "change-me-to-a-random-secret"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 1440

    # Auth
    invite_code: str = "change-me"

    # Anthropic
    anthropic_api_key: str = ""

    # Telegram
    telegram_bot_token: str = ""
    telegram_enabled: bool = False

    # CORS
    cors_origins: str = "http://localhost:5173"

    # App
    app_env: str = "development"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def google_credentials_dict(self) -> dict | None:
        if not self.google_sheets_credentials_json:
            return None
        try:
            return json.loads(self.google_sheets_credentials_json)
        except json.JSONDecodeError:
            return None

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
