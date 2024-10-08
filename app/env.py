import os
from functools import lru_cache

from dotenv import dotenv_values

from .config import AppConfig


@lru_cache
def get_app_config() -> AppConfig:
    config = AppConfig.model_validate(
        {
            **dotenv_values(".env-defaults"),
            **dotenv_values(".env"),
            **os.environ,
        }
    )
    return config
