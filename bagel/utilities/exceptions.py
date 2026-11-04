"""Custom exceptions for the bagel CLI."""


class BagelFileError(Exception):
    """Exception class for input file parsing errors."""

    pass


class BagelValidationError(Exception):
    """Exception class for input validation errors."""

    pass


class BagelResourceError(Exception):
    """Exception class for errors related to loading Neurobagel vocabulary resources."""

    pass
