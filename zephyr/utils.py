import inspect


def is_list(value):
    """Returns True if value supports list interface; False - otherwise"""
    return isinstance(value, list)


def is_dict(value):
    """Returns True if value supports dict interface; False - otherwise"""
    return isinstance(value, dict)


def call_with_context(func, context, *args):
    """
    Check if given function has more arguments than given. Call it with context
    as last argument or without it.
    """
    if inspect.ismethod(func):
        arg_count = len(inspect.getargspec(func).args) - 1
    elif inspect.isfunction(func):
        arg_count = len(inspect.getargspec(func).args)
    else:
        arg_count = len(inspect.getargspec(func.__call__).args) - 1

    if len(args) < arg_count:
        args = list(args)
        args.append(context)

    return func(*args)
