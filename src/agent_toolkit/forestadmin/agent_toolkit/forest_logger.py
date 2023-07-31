import logging
from typing import Callable

logger = logging.getLogger("forestadmin")


_LOG_LEVELS = {
    "NOTSET": logging.NOTSET,
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "EXCEPTION": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


class ForestLogger:
    _logger_instance = None

    @classmethod
    def log(cls, level, message):
        if not cls._logger_instance:
            cls._logger_instance = _ForestLogger(logging.WARNING, ForestLogger.default_logger_function)
        cls._logger_instance.log(level, message)

    @staticmethod
    def default_logger_function(level: str, message: str):
        getattr(logging.getLogger("forestadmin"), level.lower())(message)

    @classmethod
    def setup_logger(cls, log_level, custom_fn):
        cls._logger_instance = _ForestLogger(log_level, custom_fn or ForestLogger.default_logger_function)


class _ForestLogger:
    def __init__(self, log_level: int, log_function: Callable[[str, str], None]) -> None:
        self.log_level = log_level
        self.log_function = log_function

    def log(self, level, message):
        if _LOG_LEVELS[level.upper()] < self.log_level:
            return
        self.log_function(level, message)
