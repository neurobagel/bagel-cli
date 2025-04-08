import logging
from enum import Enum
from typing import NoReturn

import typer
from rich.logging import RichHandler

LOG_FMT = "%(message)s"
DATETIME_FMT = "[%Y-%m-%d %X]"

logger = logging.getLogger("bagel.logger")


class VerbosityLevel(str, Enum):
    """Enum for verbosity levels."""

    ERROR = "0"
    INFO = "1"
    DEBUG = "2"


# TODO: Once we introduce CLI options for reducing or increasing verbosity,
# we can use the "level" parameter to set the logging level
def configure_logger(level: int = logging.INFO):
    """Configure a logger with the specified logging level."""

    # Prevent duplicate handlers
    if not logger.handlers:
        handler = RichHandler(
            omit_repeated_times=False, show_path=False, rich_tracebacks=True
        )
        formatter = logging.Formatter(fmt=LOG_FMT, datefmt=DATETIME_FMT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)

    # propagate should be False to avoid duplicate messages from root logger
    logger.propagate = False


def log_error(
    logger: logging.Logger,
    message: str,
) -> NoReturn:
    """Log an exception with an informative error message, and exit the app."""
    logger.error(message)
    raise typer.Exit(code=1)


def set_log_level(verbosity: VerbosityLevel):
    """Set the logging level based on the verbosity option."""
    if verbosity == VerbosityLevel.ERROR:
        configure_logger(logging.ERROR)
    elif verbosity == VerbosityLevel.INFO:
        configure_logger(logging.INFO)
    elif verbosity == VerbosityLevel.DEBUG:
        configure_logger(logging.DEBUG)
