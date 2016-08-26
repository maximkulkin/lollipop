import sys

PY2 = int(sys.version_info[0]) == 2
PY26 = PY2 and int(sys.version_info[1]) < 7

if PY2:
    string_types = (str, unicode)
    int_types = (int, long)
    unicode = unicode
    basestring = basestring
    iterkeys = lambda d: d.iterkeys()
    itervalues = lambda d: d.itervalues()
    iteritems = lambda d: d.iteritems()
else:
    string_types = (str,)
    int_types = (int,)
    unicode = str
    basestring = (str, bytes)
    iterkeys = lambda d: d.keys()
    itervalues = lambda d: d.values()
    iteritems = lambda d: d.items()

if PY26:
    from .ordereddict import OrderedDict
else:
    from collections import OrderedDict
