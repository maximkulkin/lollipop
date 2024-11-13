import sys

PY2 = int(sys.version_info[0]) == 2
PY26 = PY2 and int(sys.version_info[1]) < 7

if PY2:
    string_types = (str, unicode)
    int_types = (int, long)
    unicode = unicode
    basestring = basestring

    def iterkeys(d):
        return d.iterkeys()

    def itervalues(d):
        return d.itervalues()

    def iteritems(d):
        return d.iteritems()
else:
    string_types = (str,)
    int_types = (int,)
    unicode = str
    basestring = (str, bytes)

    def iterkeys(d):
        return d.keys()

    def itervalues(d):
        return d.values()

    def iteritems(d):
        return d.items()

if PY26:
    from .ordereddict import OrderedDict
    from UserDict import DictMixin
else:
    from collections import OrderedDict
    try:
        from collections import (
            MutableMapping as DictMixin,
            Mapping,
            Sequence)
    except ImportError:
        from collections.abc import (
            MutableMapping as DictMixin,
            Mapping,
            Sequence)

__all__ = [
    'DictMixin',
    'Mapping',
    'OrderedDict',
    'Sequence',

    'string_types',
    'int_types',
    'unicode',
    'basestring',
    'iterkeys',
    'itervalues',
    'iteritems',
]
