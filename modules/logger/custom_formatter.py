import logging

class CustomFormatter(logging.Formatter):
    grey = "\x1b[37;49;2m"
    bold_grey = "\x1b[37;49;1m"
    yellow = "\x1b[33;49;2m"
    red = "\x1b[31;49;2m"
    bold_red = "\x1b[31;49;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: bold_grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)