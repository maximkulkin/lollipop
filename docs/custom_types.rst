.. _custom_types:

Custom Types
============

To build a custom type object you can inherit from :class:`~lollipop.types.Type` and
implement functions `load(data, **kwargs)` and `dump(value, **kwargs)`: ::

    from lollipop.types import MISSING, String
    try:
        from urlparse import urlparse, urljoin
    except ImportError:
        from urllib.parse import urlparse, urljoin

    class URL(String):
        def _load(self, data, *args, **kwargs):
            loaded = super(URL, self)._load(data, *args, **kwargs)
            return urlparse(loaded)

        def _dump(self, value, *args, **kwargs):
            dumped = urljoin(value)
            return super(URL, self)._dump(dumped, *args, **kwargs)


Other variant is to take existing type and extend it with some validations while
allowing users to add more validations: ::

    from lollipop import types, validators

    EMAIL_REGEXP = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"

    class Email(types.String):
        def __init__(self, *args, **kwargs):
            super(Email, self).__init__(*args, **kwargs)
            self._validators.insert(0, validators.Regexp(EMAIL_REGEXP))
