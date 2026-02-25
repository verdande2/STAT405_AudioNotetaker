from pydantic_settings import BaseSettings, SettingsConfigDict

class NotebookSettings(BaseSettings):
    """ A pydantic settings class for the project, mainly to contain .env variables """
    hf_token: str
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")

settings = NotebookSettings()
