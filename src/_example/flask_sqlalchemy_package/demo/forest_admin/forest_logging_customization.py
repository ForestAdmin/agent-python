import logging
import sys
import traceback

from forestadmin.agent_toolkit.forest_logger import _LOG_LEVELS


# pure python logging customization
class ColorizedFormatter(logging.Formatter):
    blue = "\x1b[34;20m"
    green = "\x1b[32;20m"
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;41m"
    reset = "\x1b[0m"

    FORMATS = {
        logging.DEBUG: blue,
        logging.INFO: green,
        logging.WARNING: yellow,
        logging.ERROR: red,
        logging.CRITICAL: bold_red,
    }

    def format(self, record):
        log_fmt = self.get_custom_format(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

    def get_custom_format(self, level):
        return self.FORMATS.get(level) + self._fmt + self.reset


def customize_forest_logging():
    forest_logger = logging.getLogger("forestadmin")
    if len(forest_logger.handlers) > 0:
        forest_logger.removeHandler(forest_logger.handlers[0])

    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(ColorizedFormatter("%(asctime)s %(pathname)s:%(lineno)d %(levelname)s: %(message)s"))

    for handler in forest_logger.handlers:
        forest_logger.removeHandler(handler)
    forest_logger.addHandler(handler)
    forest_logger.setLevel(logging.DEBUG)


# forest logging custom function
def custom_logger_fn(level: str, message: str):
    if level.lower() == "warning":
        message = f"! {message} !"
    elif level.lower() == "error":
        message = f"!! {message} !!"
    elif level.lower() == "critical":
        message = f"!!! {message} !!!"

    # reuse the forestadmin default logger permit to handle classical python logging customization
    forest_logger = logging.getLogger("forestadmin")

    # find in call stack the call to ForestLogger.log
    current_logging_frame = None
    for idx, frame in enumerate(traceback.extract_stack()[::-1]):
        # get the last frame
        if frame.line.startswith("ForestLogger.log("):
            current_logging_frame = frame
            break

    if current_logging_frame:
        # handle a log record built with the logging frame data
        forest_logger.handle(
            forest_logger.makeRecord(
                forest_logger.name,
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
        getattr(forest_logger, level.lower())(message, stack_info=True)


def custom_error_message_fn(error: Exception) -> str:
    return (", ".join(error.args)) + "🌳🌳🌳"
