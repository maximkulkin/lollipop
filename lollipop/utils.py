import inspect
import re


def identity(value):
    """Function that returns its argument."""
    return value

def constant(value):
    """Returns function that takes any arguments and always returns given value."""
    def func(*args, **kwargs):
        return value
    return func


def is_list(value):
    """Returns True if value supports list interface; False - otherwise"""
    return isinstance(value, list)


def is_dict(value):
    """Returns True if value supports dict interface; False - otherwise"""
    return isinstance(value, dict)


def make_context_aware(func, numargs):
    """
    Check if given function has no more arguments than given. If so, wrap it
    into another function that takes extra argument and drops it.
    Used to support user providing callback functions that are not context aware.
    """
    try:
        if inspect.ismethod(func):
            arg_count = len(inspect.getargspec(func).args) - 1
        elif inspect.isfunction(func):
            arg_count = len(inspect.getargspec(func).args)
        elif inspect.isclass(func):
            arg_count = len(inspect.getargspec(func.__init__).args) - 1
        else:
            arg_count = len(inspect.getargspec(func.__call__).args) - 1
    except TypeError:
        arg_count = numargs

    if arg_count <= numargs:
        def normalized(*args):
            return func(*args[:-1])

        return normalized

    return func


def call_with_context(func, context, *args):
    """
    Check if given function has more arguments than given. Call it with context
    as last argument or without it.
    """
    return make_context_aware(func, len(args))(*args + (context,))


def to_snake_case(s):
    """Converts camel-case identifiers to snake-case."""
    return re.sub('([^_A-Z])([A-Z])', lambda m: m.group(1) + '_' + m.group(2).lower(), s)


def to_camel_case(s):
    """Converts snake-case identifiers to camel-case."""
    return re.sub('_([a-z])', lambda m: m.group(1).upper(), s)
