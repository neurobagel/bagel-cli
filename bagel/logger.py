import logging

LOG_FMT = "%(asctime)s %(levelname)-7s %(message)s"
DATETIME_FMT = "%Y-%m-%d %H:%M:%S"


def get_logger(level: int = logging.INFO) -> logging.Logger:
    """Create a logger with the specified logging level."""

    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(fmt=LOG_FMT, datefmt=DATETIME_FMT)
    logger.setLevel(level)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # propagate should be False to avoid duplicate messages from root logger
    logger.propagate = False

    return logger


logger = get_logger()
