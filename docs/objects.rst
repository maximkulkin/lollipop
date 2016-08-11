.. _objects:

Object schemas
==============

Declaration
-----------

Object schemas are defined with :class:`~lollipop.types.Object` class by passing
it a dictionary mapping field names to :class:`~lollipop.types.Type` instances.

So given an object ::

    class Person(object):
        def __init__(self, name, age):
            self.name = name
            self.age = age

You can define it's type like this: ::

    from lollipop.types import Object, String, Integer

    PersonType = Object({
        'name': String(),
        'age': Integer(),
    })

It will allow serializing Person types to Python's basic types (that you can use to
serialize to JSON) or validate that basic Python data: ::

    PersonType.dump(Person('John', 38))
    # => {"name": "John", "age": 38}

    PersonType.validate({"name": "John"})
    # => {"age": "Value is required"}

    PersonType.load({"name": "John", "age": 38})
    # => {"name": "John", "age": 38}

Yet it loads to same basic type dict instead of real object. To fix that, you need
to provide a data constructor to type object: ::

    PersonType = Object({
        'name': String(),
        'age': Integer(),
    }, constructor=Person)

    PersonType.load({"name": "John", "age": 38})
    # => Person(name="John", age=38)

Constructor function should take field values as keyword arguments and return
constructed object.

Value extraction
----------------

When you serialize (dump) objects, field values are expected to be object attributes.
But library actually allows controlling that. This is done with
:class:`~lollipop.types.Field` class instances. When you define your object and
pass types for it's fields, what really happens is those types are wrapped with
a :class:`~lollipop.types.Field` subclass objects. The actual object fields are
defined like this: ::

    PersonType = Object({
        'name': AttributeField(String()),
        'age': AttributeField(Integer()),
    })

Passing just a :class:`~lollipop.types.Type` instances for field types is just a
shortcut to wrap them all with a default field type which is
:class:`~lollipop.types.AttributeField`. You can change default field type with
`Object.default_field_type` argument: ::

    PersonType = Object({
        'name': String(),
        'age': Integer(),
    }, default_field_type=AttributeField)

And you can actually mix fields defined with just :class:`~lollipop.types.Type`
with fields defined with :class:`~lollipop.types.Field`. The first ones will be
wrapped with default field type while the later ones will be used as is.

:class:`~lollipop.types.AttributeField` is probably the one that would be used most
of the time. It extracts value for serialization from object attribute with the same
name as the field name. You can change the name of attribute to extract value from:
::

    Person = namedtuple('Person', ['full_name'])

    PersonType = Object({'name': AttributeField(String(), attribute='full_name')})

    PersonType.dump(Person('John Doe'))  # => {'name': 'John Doe'}

Other useful instances are :class:`~lollipop.types.MethodField` which calls given
method on the object to get value instead of getting attribute,
:class:`~lollipop.types.FunctionField` which uses given function on a serialized
object to get value, :class:`~lollipop.types.ConstantField` which always serializes
to given constant value. For last one there is another shortcut: if you provide a
value for a field which is not :class:`~lollipop.types.Type` and not
:class:`~lollipop.types.Field` then it will be wrapped with a
:class:`~lollipop.types.ConstantField`.

::

    # Following lines are equivalent
    Object({'answer': ConstantField(Any(), 42)}).dump(object())  # => {'answer': 42}
    Object({'answer': 42}).dump(object())  # => {'answer': 42}


Object Schema Inheritance
-------------------------

To be able to allow reusing parts of schema, you can supply a base
:class:`~lollipop.type.Object`: ::

    BaseType = Object({'base': String()})
    InheritedType = Object(BaseType, {'foo': Integer()})

    # is the same as
    InheritedType = Object({'base': String(), 'foo': Integer()})

You can actually supply multple base types which allows using them as mixins: ::

    TimeStamped = Object({'created_at': DateTime(), 'updated_at': DateTime()})

    BaseType = Object({'base': String()})
    InheritedType = Object([BaseType, TimeStamped], {'foo': Integer()})


Polymorphic types
-----------------

Sometimes you need a way to serialize and deserialize values of different types put
in the same list. Or maybe you value can be of either one of given types. E.g. you
have a graphical application which operates with objects of different shapes: ::

    class Point(object):
        def __init__(self, x, y):
            self.x = x
            self.y = y

    class Shape(object):
        pass

    class Circle(Shape):
        def __init__(self, center, radius):
            self.center = center
            self.radius = radius

    class Rectangle(Shape):
        def __init__(self, left_top, right_bottom):
            self.left_top = left_top
            self.right_bottom = right_bottom

    PointType = Object({'x': Integer(), 'y': Integer()}, constructor=Point)

    CircleType = Object({
        'center': PointType,
        'radius': Integer
    }, constructor=Circle)

    RectangleType = Object({
        'left_top': PointType,
        'right_bottom': PointType,
    }, constructor=Rectangle)


To support that library provides a special type - :class:`~lollipop.types.OneOf`: ::

    def with_type_annotation(subject_type, type_name):
        return Object(subject_type, {'type': type_name},
                      constructor=subject_type.constructor)

    AnyShapeType = OneOf(
        {
            'circle': with_type_annotation(CircleType, 'circle'),
            'rectangle': with_type_annotation(RectangleType, 'rectangle'),
        },
        dump_hint=lambda obj: obj.__class__.__name__.lower(),
        load_hint=dict_value_hint('type'),
    )

    dumped = List(AnyShapeType).dump([
        Circle(Point(5, 8), 4), Rectangle(Point(1, 10), Point(10, 1))
    ])
    # => [
    #   {'type': 'circle',
    #    'center': {'x': 5, 'y': 8},
    #    'radius': 4},
    #   {'type': 'rectangle',
    #    'left_top': {'x': 1, 'y': 10},
    #    'right_bottom': {'x': 10, 'y': 1}}]

    List(AnyShapeType).load(dumped)
    # => [Circle(Point(5, 8), 4), Rectangle(Point(1, 10), Point(10, 1))]

:class:`~lollipop.types.OneOf` uses user supplied functions to determine which
particular type to use during serialization/deserialization. It helps returning
proper error messages. If you're not interested in providing detailed error message,
you can just supply all types as a list. :class:`~lollipop.types.OneOf` will try
to use each of them in given order returning first successfull result. If all types
return errors it will provide generic error message. Here is example of library's
error messages schema: ::

    ErrorMessagesType = OneOf([
        String(), List(String()), Dict('ErrorMessages')
    ], name='ErrorMessages')
