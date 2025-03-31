import logging
import sys
import traceback

from rich.logging import RichHandler

LOG_FMT = "%(message)s"
DATETIME_FMT = "[%Y-%m-%d %X]"


# TODO: Once we introduce CLI options for reducing or increasing verbosity,
# we can use the "level" parameter to set the logging level
def get_logger(level: int = logging.INFO) -> logging.Logger:
    """Create a logger with the specified logging level."""

    logger = logging.getLogger("test")
    handler = RichHandler(omit_repeated_times=False, show_path=False)
    formatter = logging.Formatter(fmt=LOG_FMT, datefmt=DATETIME_FMT)
    logger.setLevel(level)
    handler.setLevel(level)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # propagate should be False to avoid duplicate messages from root logger
    logger.propagate = False

    return logger


def log_error(
    logger: logging.Logger, message: str, show_traceback: bool = False
):
    """Log an exception with or without the full traceback."""
    if show_traceback:
        logger.error("%s\n%s", traceback.format_exc(), message)
    else:
        logger.error(message)
    sys.exit(1)


logger = get_logger()
