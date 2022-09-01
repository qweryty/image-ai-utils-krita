import json
import os.path
from os import environ
from typing import Optional

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
    SERVER_URL: str = Field('http://localhost:8000/')


settings: Optional[Settings] = None


def init_settings():
    if not os.path.isfile(SETTINGS_PATH):
        return False

    global settings
    with open(SETTINGS_PATH, 'r') as f:
        settings = Settings(**json.load(f))
    return True


init_settings()
