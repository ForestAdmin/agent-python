import logging


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
