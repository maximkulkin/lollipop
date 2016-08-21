.. _modifiers:

Modifiers
=========

Constant
--------
If you want to model a field in schema that always dumps to the same value, you
can use :class:`~lollipop.types.Constant`. Also, it checks that the same value is
present on load: ::

    CircleType = Object({
        'type': Constant('circle'),
        'center': PointType,
        'radius': Float(),
    })

    RectangleType = Object({
        'type': Constant('rectangle'),
        'top_left': PointType,
        'bottom_right': PointType,
    })

Optional
--------
All types expect that the value will always be there, if it is not there or None,
it will be an error. Sometimes you might want to make values optional. That's
exactly what this modifier type is for: ::

    class User:
        def __init__(self, email, name=None):
            self.email = email
            self.name = name

    UserType = Object({
        'email': Email(),
        'name': Optional(String()),  # it's ok not to have user name
    }, constructor=User)

    UserType.load({'email': 'john.doe@example.com'})
    # => User(email='john.doe@example.com')

You can also specify values to use during loading/dumping if value is not present
with `load_default` and `dump_default`: ::

    UserType = Object({
        'email': String(),
        'role': Optional(
            String(validate=AnyOf(['admin', 'customer'])),
            load_default='customer',
        ),
    })


LoadOnly and DumpOnly
---------------------
If some data should not be accepted from user or not be exposed to user, you can
use :class:`~lollipop.types.LoadOnly` and :class:`~lollipop.types.DumpOnly` to
support that: ::

    UserType = Object({
        'name': String(),
        'password': LoadOnly(String()),     # should not be dumped to user
        'created_at': DumpOnly(DateTime()), # should not be accepted from user
    })

Corresponding `load()` or `dump()` methods will always return
:data:`~lollipop.types.MISSING`.
