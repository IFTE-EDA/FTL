import sys
import logging


class Logger:
    logger = None
    indent_step = 4

    def __init__(self, tag):
        self._logger = logging.getLogger(tag)
        handler = logging.StreamHandler(sys.stdout)
        self._logger.addHandler(handler)
        self._logger.setLevel(logging.DEBUG)
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
