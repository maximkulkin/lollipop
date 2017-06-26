import inspect
import re
from lollipop.compat import DictMixin, iterkeys
import collections


def identity(value):
    """Function that returns its argument."""
    return value

def constant(value):
    """Returns function that takes any arguments and always returns given value."""
    def func(*args, **kwargs):
        return value
    return func


def is_sequence(value):
    """Returns True if value supports list interface; False - otherwise"""
    return isinstance(value, collections.Sequence)

def is_mapping(value):
    """Returns True if value supports dict interface; False - otherwise"""
    return isinstance(value, collections.Mapping)


# Backward compatibility
is_list = is_sequence
is_dict = is_mapping


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


class DictWithDefault(DictMixin, object):
    def __init__(self, values={}, default=None):
        super(DictWithDefault, self).__init__()
        self.values = values
        self.default = default

    def __len__(self):
        return len(self.values)

    def __getitem__(self, key):
        if key in self.values:
            return self.values[key]
        return self.default

    def __setitem__(self, key, value):
        self.values[key] = value

    def __delitem__(self, key):
        del self.values[key]

    def __iter__(self):
        for key in self.values:
            yield key

    def __len__(self):
        return len(self.values)

    def __contains__(self, key):
        return key in self.values

    def keys(self):
        return self.values.keys()

    def iterkeys(self):
        for k in iterkeys(self.values):
            yield k

    def iteritems(self):
        for k, v in self.values.iteritems():
            yield k, v


class OpenStruct(DictMixin):
    """A dictionary that also allows accessing values through object attributes."""
    def __init__(self, data=None):
        self.__dict__.update({'_data': data or {}})

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __delitem__(self, key):
        del self._data[key]

    def __iter__(self):
        for key in self._data:
            yield key

    def __len__(self):
        return len(self._data)

    def __contains__(self, key):
        return key in self._data

    def keys(self):
        return self._data.keys()

    def iterkeys(self):
        for k in iterkeys(self._data):
            yield k

    def iteritems(self):
        for k, v in self._data.iteritems():
            yield k, v

    def __hasattr__(self, name):
        return name in self._data

    def __getattr__(self, name):
        if name not in self._data:
            raise AttributeError(name)
        return self._data[name]

    def __setattr__(self, name, value):
        self._data[name] = value

    def __delattr__(self, name):
        if name not in self._data:
            raise AttributeError(name)
        del self._data[name]

    def __repr__(self):
        return '<%s %s>' % (
            self.__class__.__name__,
            ' '.join('%s=%s' % (k, repr(v)) for k, v in self._data.iteritems()),
        )
