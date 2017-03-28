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
        def load(self, data, *args, **kwargs):
            loaded = super(URL, self).load(data, *args, **kwargs)
            return urlparse(loaded)

        def dump(self, value, *args, **kwargs):
            dumped = urljoin(value)
            return super(URL, self).dump(dumped, *args, **kwargs)


Other variant is to take existing type and extend it with some validations while
allowing users to add more validations: ::

    from lollipop import types, validators

    EMAIL_REGEXP = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"

    class Email(types.String):
        def __init__(self, *args, **kwargs):
            super(Email, self).__init__(*args, **kwargs)
            self.validators.insert(0, validators.Regexp(EMAIL_REGEXP))

To simplify creating new types by adding validators to existing types there is
a helper function - :func:`~lollipop.types.validated_type`: ::

    Email = validated_type(
        String, 'Email',
        validate=Regexp('(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)',
                        error='Invalid email')
    )

    Ipv4Address = validated_type(
        String, 'Ipv4Address',
        # regexp simplified for demo purposes
        validate=Regexp('^\d+\.\d+\.\d+\.\d+$', error='Invalid IP address')
    )

    Percentage = validated_type(Integer, validate=Range(0, 100))
