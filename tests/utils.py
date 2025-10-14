"""Utility functions for testing."""


def get_values_by_key(data, target):
    """
    Get values of all instances of a specified key in a dictionary. Will also look inside lists of dictionaries and nested dictionaries.
    """
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                yield from get_values_by_key(value, target)
            elif key == target:
                yield value
    elif isinstance(data, list):
        for item in data:
            yield from get_values_by_key(item, target)
