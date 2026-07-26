from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
from dotenv import load_dotenv


class Setting(BaseSettings):
    load_dotenv()

    JIRA_BASE_URL: str
    JIRA_EMAIL: str
    JIRA_API_TOKEN: SecretStr
    JIRA_TICKET_KEY:str
    JIRA_CLOUD_ID: str
    OPENAI_API_KEY: str
    OPENAI_MODEL: str
    OPENAI_TIMEOUT: float = 30.0

    model_config = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding="utf-8",
        extra= "ignore"
    )