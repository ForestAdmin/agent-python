import logging
import os
import re
from typing import Callable, Optional, TypedDict
from urllib.parse import urlparse

from forestadmin.datasource_toolkit.exceptions import ForestException


class Options(TypedDict):
    # application_url: str  # useless for now
    auth_secret: str
    prefix: str
    env_secret: str
    server_url: str
    is_production: bool
    schema_path: str
    logger: Callable[[str, str], None]
    logger_level: int
    permissions_cache_duration_in_seconds: int
    customize_error_message: Callable[[Exception], str]
    instant_cache_refresh: Optional[bool]
    skip_schema_update: Optional[bool]
    verify_ssl: Optional[bool]


class OptionValidator:
    DEFAULT_OPTIONS: Options = {
        "is_production": False,
        "prefix": "",
        "server_url": "https://api.forestadmin.com",
        "logger": None,
        "logger_level": logging.INFO,
        "customize_error_message": None,
        "permissions_cache_duration_in_seconds": 15 * 60,
        "skip_schema_update": False,
        "verify_ssl": os.environ.get("FOREST_VERIFY_SSL", "True").lower() == "true",
    }

    @classmethod
    def with_defaults(cls, options: Options):
        return_options = {**cls.DEFAULT_OPTIONS}
        return_options.update({k: v for k, v in options.items() if v is not None})

        if return_options.get("instant_cache_refresh") is None:
            return_options["instant_cache_refresh"] = return_options["is_production"]

        return return_options

    @staticmethod
    def validate_options(options: Options):
        OptionValidator._check_forest_server_options(options)
        OptionValidator._check_auth_options(options)
        OptionValidator._check_other_option(options)

        return options

    @staticmethod
    def _check_forest_server_options(options: Options):
        if "env_secret" not in options or not re.search(r"^[0-9a-f]{64}$", options["env_secret"]):
            raise ForestException(
                "options['env_secret'] is missing or invalid. You can retrieve its value "
                + "from https://www.forestadmin.com"
            )
        if "server_url" not in options or not OptionValidator._is_url(options["server_url"]):
            raise ForestException(
                "options['server_url'] is missing or invalid. It should contain an URL "
                + '(i.e. "https://api.forestadmin.com")'
            )

        if "schema_path" not in options or not OptionValidator.is_existing_path(options["schema_path"]):
            raise ForestException(
                'options["schema_path"] is invalid. It should contain a relative filepath '
                + 'where the schema should be loaded/updated (i.e. "./.forestadmin-schema.json")'
            )

    @staticmethod
    def _check_auth_options(options: Options):
        if (
            "auth_secret" not in options
            or not isinstance(options["auth_secret"], str)
            or not re.match(r"^[-~\/\w]*$", options["auth_secret"], re.I)
        ):
            raise ForestException(
                'options["auth_secret"] is invalid. Any long random string should work '
                + '(i.e. "OfpssLrbgF3P4vHJTTpb")'
            )

    @staticmethod
    def _check_other_option(options: Options):
        if not isinstance(options["prefix"], str) or not re.match(r"^[-~\/\w]*$", options["prefix"], re.I):
            raise ForestException(
                'options["prefix"] is invalid. It should contain the prefix on which '
                + 'forest admin routes should be mounted (i.e. "/api/v1")',
            )

    @staticmethod
    def _is_url(url: str) -> bool:
        if not isinstance(url, str):
            return False
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc]) and result.scheme.lower() in ["http", "https"]
        except Exception:
            return False

    @staticmethod
    def is_existing_path(path: str) -> bool:
        if not isinstance(path, str):
            return False
        try:
            return os.path.exists(os.path.dirname(path))
        except Exception:
            return False
