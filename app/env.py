import os
import sys
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


def get_test_config() -> AppConfig:
    # we setup the DB separately
    config = AppConfig(DATABASE_URL="")
    return config
