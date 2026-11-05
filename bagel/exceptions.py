"""Custom exceptions for the bagel CLI."""

# TODO: Create a base BagelError class that all other exceptions inherit from,
# so we can catch all bagel-specific exceptions in one place if needed?


class BagelFileError(Exception):
    """Exception class for input file parsing errors."""

    pass


class BagelValidationError(Exception):
    """Exception class for input validation errors."""

    pass


class BagelResourceError(Exception):
    """Exception class for errors related to loading Neurobagel vocabulary resources."""

    pass
