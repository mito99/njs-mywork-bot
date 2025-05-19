import os
from pathlib import Path
from pprint import pprint
from time import time
from typing import Dict, List, Tuple, Type, Union

from njs_mywork_tools.settings import GoogleSheetSetting, SurrealDBSetting
from pydantic import BaseModel, Field
from pydantic_settings import (BaseSettings, PydanticBaseSettingsSource,
                               SettingsConfigDict, YamlConfigSettingsSource)


class StorageConfig(BaseModel):
    path: str

class SlackBotConfig(BaseModel):
    bot_token: str
    app_token: str
    signing_secret: str
    channel_id: str

class ApplicationConfig(BaseModel):
    log_level: str = "INFO"
    storage: Dict[str, StorageConfig] = Field(default_factory=dict)

class AWSConfig(BaseModel):
    access_key_id: str
    secret_access_key: str
    default_region: str
    model_id: str

class Config(BaseSettings):
    """アプリケーション設定"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        yaml_file="config.yaml",
        yaml_file_encoding="utf-8",
        extra="ignore",
    )

    slack_user_token: str
    slack_bot_task: SlackBotConfig = Field(default_factory=SlackBotConfig)
    slack_bot_mail: SlackBotConfig = Field(default_factory=SlackBotConfig)
    
    google_api_key: str
    google_gemini_model_name: str = "gemini-2.0-flash-exp"
    google_sheet : GoogleSheetSetting
    surrealdb: SurrealDBSetting
    application: ApplicationConfig = Field(default_factory=ApplicationConfig)
    startup_time: float = time()
    aws: AWSConfig = Field(default_factory=AWSConfig)

    ignore_mail_addresses: str
    enable_mail_watcher: bool = False
    
    njs_file_access_restriction_enabled: bool = True
    njs_file_name_pattern_restriction: str = ".*"
    
    def is_ignore_mail(self, mail_address: str) -> bool:
        ignore_mail_addresses = self.ignore_mail_addresses.split(",")
        for ignore_mail_address in ignore_mail_addresses:
            if ignore_mail_address in mail_address:
                return True
        return False

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
