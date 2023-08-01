import logging


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
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(ColorizedFormatter("%(asctime)s %(pathname)s:%(lineno)d %(levelname)s: %(message)s"))

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
    getattr(forest_logger, level.lower())(message)


def add_more_tree_to_errors(message):
    return "\x1b[31;41m🌳🌳" + message + "🌳🌳\x1b[0m"


def custom_error_message_fn(error: Exception) -> str:
    return (", ".join(error.args)) + "🌳🌳🌳"
