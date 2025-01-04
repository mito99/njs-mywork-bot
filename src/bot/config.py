import os
from pathlib import Path
from pprint import pprint
from time import time
from typing import Dict, List, Tuple, Type, Union

from pydantic import BaseModel, Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)


class StorageConfig(BaseModel):
    path: str


class SlackConfig(BaseModel):
    allowed_users: List[str]



class ApplicationConfig(BaseModel):
    log_level: str = "INFO"
    storage: Dict[str, StorageConfig] = Field(default_factory=dict)
    slack: SlackConfig = Field(default_factory=SlackConfig)

class Config(BaseSettings):
    """アプリケーション設定"""

    model_config = SettingsConfigDict(
        env_file=".env",
        yaml_file="config.yaml",
        extra="ignore",
    )

    slack_bot_token: str
    slack_app_token: str
    slack_signing_secret: str
    google_api_key: str
    google_gemini_model_name: str = "gemini-2.0-flash-exp"

    application: ApplicationConfig = Field(default_factory=ApplicationConfig)

    startup_time: float = time()

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (
            YamlConfigSettingsSource(settings_cls),
            dotenv_settings,
        )


def load_config() -> Config:
    """環境変数と設定ファイルから設定を読み込みます。"""
    return Config()


if __name__ == "__main__":
    config = load_config()
    pprint(config.model_dump())
