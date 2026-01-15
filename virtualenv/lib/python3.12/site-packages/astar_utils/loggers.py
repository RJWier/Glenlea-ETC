# -*- coding: utf-8 -*-
"""To have all logger creation in one place."""

import logging

from colorama import Fore, Back, Style


def get_astar_logger() -> logging.Logger:
    """Get a logger with name "astar"."""
    return logging.getLogger("astar")


def get_logger(name: str) -> logging.Logger:
    """Get a logger with given name as a child of the "astar" logger."""
    return get_astar_logger().getChild(name)


class ColoredFormatter(logging.Formatter):
    """Formats colored logging output to console.

    Uses the ``colorama`` package to append console color codes to log message.
    The colors for each level are defined as a class attribute dict `colors`.
    Above a certain level, the ``Style.BRIGHT`` modifier is added.
    This defaults to anything at or above ERROR, but can be modified in the
    `bright_level` class attribute. Similarly, only above a certain level, the
    name of the level is added to the output message. This defaults to anyting
    at or above WARNING, but can be modified in the `show_level` class
    attribute. The class takes a single optional boolean keyword argument
    `show_name`, which determines if the logger name will be added to the
    output message. Any additional `kwargs` are passed along to the base class
    ``logging.Formatter``.

    Note that unlike the base class, this class currently has no support for
    different `style` arguments (only '%' supported) or `defaults`.
    """

    colors = {
        logging.DEBUG: Fore.CYAN,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.MAGENTA,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.YELLOW + Back.RED
    }
    show_level = logging.WARNING
    bright_level = logging.ERROR

    def __init__(self, show_name: bool = True, **kwargs):
        self._show_name = show_name
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        """Return repr(self)."""
        return f"<{self.__class__.__name__}>"

    def _get_fmt(self, level: int) -> str:
        log_fmt = [
            self.colors.get(level),
            Style.BRIGHT * (level >= self.bright_level),
            "%(name)s - " * self._show_name,
            "%(levelname)s: " * (level >= self.show_level),
            "%(message)s" + Style.RESET_ALL,
        ]
        return "".join(log_fmt)

    def formatMessage(self, record):
        """Override `logging.Formatter.formatMessage()`."""
        log_fmt = self._get_fmt(record.levelno)
        return log_fmt % record.__dict__
