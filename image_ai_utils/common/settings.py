import json
import os.path
from os import environ

from pydantic import BaseSettings, Field

SETTINGS_PATH = os.path.abspath(
    environ.get(
        'AI_IMAGE_UTILS_SETTINGS_PATH',
        os.path.join(os.path.dirname(os.path.realpath(__file__)), 'settings.json')
    )
)


class Settings(BaseSettings):
    USERNAME: str = Field(...)
    PASSWORD: str = Field(...)
    SERVER_URL: str = Field('localhost:8000')
    USE_TLS: bool = Field(False)

    _settings = None

    @classmethod
    def reload(cls):
        if not os.path.isfile(SETTINGS_PATH):
            return None

        with open(SETTINGS_PATH, 'r') as f:
            cls._settings = Settings(**json.load(f))
        return cls._settings

    @classmethod
    def settings(cls):
        if cls._settings is not None:
            return cls._settings

        if not os.path.isfile(SETTINGS_PATH):
            return None

        with open(SETTINGS_PATH, 'r') as f:
            cls._settings = Settings(**json.load(f))
        return cls._settings
