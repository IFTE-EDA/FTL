import sys
import os
import logging


class Logger:
    logger = None
    indent_step = 4

    def __init__(self, tag):
        os.system("color")
        self._logger = logging.getLogger(tag)
        # handler = logging.StreamHandler(sys.stdout)
        # self._logger.addHandler(handler)
        self._logger.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        ch.setFormatter(FTLFormatter())

        self._logger.addHandler(ch)
        self._logger.info("Logger started.")
        self.tag = tag

    def _indent(self, msg: str, indent: int = 0):
        return " " * self.indent_step * indent + msg

    def debug(self, msg, indent: int = 0):
        self._logger.debug(self._indent(msg, indent))

    def info(self, msg, indent: int = 0):
        self._logger.info(self._indent(msg, indent))

    def warning(self, msg, indent: int = 0):
        self._logger.warning(self._indent(msg, indent))

    def error(self, msg, indent: int = 0):
        self._logger.error(self._indent(msg, indent))

    def critical(self, msg, indent: int = 0):
        self._logger.critical(self._indent(msg, indent))


class Colors:
    grey = "\x1b[0;37m"
    green = "\x1b[1;32m"
    yellow = "\x1b[1;33m"
    red = "\x1b[1;31m"
    purple = "\x1b[1;35m"
    blue = "\x1b[1;34m"
    light_blue = "\x1b[1;36m"
    reset = "\x1b[0m"
    bold_red = "\x1b[31;1m"
    blink_red = "\x1b[5m\x1b[1;31m"


class FTLFormatter(logging.Formatter):
    # format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"
    format = "%(name)s\t- %(levelname)s\t- %(message)s"

    FORMATS = {
        logging.DEBUG: Colors.grey + format + Colors.reset,
        logging.INFO: Colors.green + format + Colors.reset,
        logging.WARNING: Colors.yellow + format + Colors.reset,
        logging.ERROR: Colors.red + format + Colors.reset,
        logging.CRITICAL: Colors.bold_red + format + Colors.reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class Loggable:
    parent = None
    logger = None
    indent = 0

    def __init__(self, origin):
        if isinstance(origin, Loggable):
            self.parent = origin
            self.logger = origin.get_logger()
            self.indent = origin.get_child_indent()
        elif isinstance(origin, Logger):
            self.logger = origin
        else:
            raise ValueError(
                "Origin must be either a Logger or Loggable object."
            )

    def get_logger(self):
        return self.logger

    def get_child_indent(self):
        return self.indent + 1

    def log_debug(self, msg):
        self.logger.debug(msg, self.indent)

    def log_info(self, msg):
        self.logger.info(msg, self.indent)

    def log_warning(self, msg):
        self.logger.warning(msg, self.indent)

    def log_error(self, msg):
        self.logger.error(msg, self.indent)

    def log_critical(self, msg):
        self.logger.critical(msg, self.indent)
