import logging
import sys
import traceback
from typing import Callable

from forestadmin.agent_toolkit.options import OptionValidator

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
            # we shouldn't pass here if agent is created
            cls._logger_instance = _ForestLogger(
                OptionValidator.DEFAULT_OPTIONS["logger_level"], ForestLogger.default_logger_function
            )
        cls._logger_instance.log(level, message)

    @staticmethod
    def default_logger_function(level: str, message: str):
        # find in call stack the call to ForestLogger.log
        current_logging_frame = None
        for frame in traceback.extract_stack()[::-1]:
            # get the last frame
            if frame.line.startswith("ForestLogger.log("):
                current_logging_frame = frame
                break

        if current_logging_frame:
            # handle a log record built with the logging frame data
            logger.handle(
                logger.makeRecord(
                    logger.name,
                    _LOG_LEVELS[level.upper()],
                    current_logging_frame.filename,
                    current_logging_frame.lineno,
                    message,
                    {},
                    sys.exc_info() if level.lower() == "exception" else None,
                    current_logging_frame.name,
                )
            )
        else:
            # I don't know why we may be in this else, but if we are...
            getattr(logger, level.lower())(message, stack_info=True)

    @classmethod
    def setup_logger(cls, log_level, custom_fn):
        cls._logger_instance = _ForestLogger(log_level, custom_fn or ForestLogger.default_logger_function)
        if custom_fn is None and len(logger.handlers) == 0:
            handler = logging.StreamHandler()
            handler.setLevel(log_level)
            logger.addHandler(handler)
            logger.setLevel(log_level)


class _ForestLogger:
    def __init__(self, log_level: int, log_function: Callable[[str, str], None]) -> None:
        self.log_level = log_level
        self.log_function = log_function

    def log(self, level, message):
        if _LOG_LEVELS[level.upper()] < self.log_level:
            return
        self.log_function(level, message)
