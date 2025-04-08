import logging
from typing import NoReturn

import typer
from rich.logging import RichHandler

LOG_FMT = "%(message)s"
DATETIME_FMT = "[%Y-%m-%d %X]"

logger = logging.getLogger("bagel.logger")


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
