from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Meta / Instagram
    meta_app_id: str = ""
    meta_app_secret: str = ""
    meta_access_token: str = ""
    meta_verify_token: str = "voss-instagram-verify"
    instagram_account_id: str = ""

    # VOSS API
    voss_api_url: str = ""
    voss_api_key: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
