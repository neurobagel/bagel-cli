import logging

import typer
from rich.logging import RichHandler

from bagel.config import CONFIG

LOG_FMT = "%(message)s"
DATETIME_FMT = "[%Y-%m-%d %X]"


# TODO: Once we introduce CLI options for reducing or increasing verbosity,
# we can use the "level" parameter to set the logging level
def get_logger(level: int = logging.INFO) -> logging.Logger:
    """Create a logger with the specified logging level."""

    logger = logging.getLogger("test")
    handler = RichHandler(
        omit_repeated_times=False, show_path=False, rich_tracebacks=True
    )
    formatter = logging.Formatter(fmt=LOG_FMT, datefmt=DATETIME_FMT)
    logger.setLevel(level)
    handler.setLevel(level)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # propagate should be False to avoid duplicate messages from root logger
    logger.propagate = False

    return logger


def log_error(
    logger: logging.Logger,
    message: str,
):
    """Log an exception with or without the full traceback."""
    # when exc_info=True, the current exception information will be fetched
    # and included in the log after the custom message
    logger.error(message, exc_info=CONFIG["debug"])
    raise typer.Exit(code=1)


logger = get_logger()
