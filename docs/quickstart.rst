.. _quickstart:

Quickstart
==========

This guide will walk you through the basics of schema definition, data serialization,
deserialization and validation.

Declaring Types
---------------

Let's start with a your application-level model: ::

    class Person(object):
        def __init__(self, name, birthdate):
            self.name = name
            self.birthdate = birthdate

        def __repr__(self):
            return "<Person name={name} birthdate={birthdate}>".format(
                name=repr(self.name), birthdate=repr(self.birthdate),
            )

You want to create a JSON API to load and dump it. First you need to define a
type for that data: ::

    from lollipop.types import Object, String, Date

    PersonType = Object({
        'name': String(),
        'birthdate': Date(),
    })


Serializing data
----------------

To serialize your data, pass it to your type's `dump()` method: ::

    from datetime import date
    import json

    john = Person(name='John', birthdate=date(1970, 02, 29))
    john_data = PersonType.dump(john)
    print json.dump(john_data, indent=2)
    # {
    #   "name": "John",
    #   "birthdate": "1970-02-29"
    # }


Deserializing data
------------------

To load data back, pass it to your type's `load()` method: ::

    user_data = {
        "name": "Bill",
        "birthdate": "1994-08-12",
    }

    user = PersonType.load(user_data)
    print user
    # {"name": "Bill", "birthdate": date(1994, 08, 12)}

If you want to restore original data type, you can pass it's constructor function
when you define your type: ::

    PersonType = Object({
        'name': String(),
        'birthdate': Date(),
    }, constructor=Person)

    print PersonType.load({
        "name": "Bill",
        "birthdate": "1994-08-12",
    })
    # <Person name="Bill" birthdate=date(1994, 08, 12)>

To deserialize a list of objects, you can create a :class:`~lollipop.types.List`
instance with your object type as element type: ::

    List(PersonType).load([
        {"name": "Bob", "birthdate": "1980-12-12"},
        {"name": "Jane", birthdate": "1991-08-04"},
    ])
    # => [<Person name="Bob" birthdate=date(1980, 12, 12)>,
          <Person name="Jane" birthdate=date(1991, 08, 04)>]


Validation
----------

By default all fields are required to have values, so if you accidentally forget
to specify one, you will get a :exc:`~lollipop.errors.ValidationError` exception: ::

    from lollipop.errors import ValidationError

    try:
        PersonType.load({"name": "Bob"})
    except ValidationError as ve:
        print ve.messages  # => {"birthdate": "Value is required"}

The same applies to field types: if you specify value of incorrect type, you will
get validation error.

If you want more control on your data, you can specify additional validators: ::

    from lollipop.validators import Regexp

    email_validator = Regexp(
        '(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)',
        error='Invalid email',
    )

    UserType = Object({
        'email': String(validate=email_validator),
    })

    try:
        UserType.load({"email": "wasa"})
    except ValidationError as ve:
        print ve.messages  # => {"email": "Invalid email"}

If you just need to validate date and not interested in result, you can use
:func:`~Type.validate()` method: ::

    print UserType.validate({"email": "wasa"})
    # => {"email": "Invalid email"}

    print UserType.validate({"email": "wasa@example.com"})
    # => None

You can define your own validators: ::

    def validate_person(person):
        errors = ValidationErrorBuilder()
        if person.name == 'Bob':
            errors.add_error('name', 'Should not be called Bob')
        if person.age < 18:
            errors.add_error('age', 'Should be at least 18 years old')
        errors.raise_errors()

    PersonType = Object({
        'name': String(),
        'birthdate': Date(),
    }, validate=validate_person)

    PersonType.validate({'name': 'Bob', 'age': 15})
    # => {'name': 'Should not be called Bob',
    #     'age': 'Should be at least 18 years old'}

or use :class:`~lollipop.validators.Predicate` validator and supply a True/False
function to it.

Validating cross-field dependencies is easy: ::

    def validate_person(person):
        if person.name == 'Bob' and person.age < 18:
            raise ValidationError('All Bobs should be at least 18 years old')

Changing The Way Accessing Object Data
--------------------------------------

When you define an :class:`~lollipop.types.Object` type, by default it will retrieve 
object data by accessing object's attributes with the same name as name of the field
you define. Most often it is what you want. However sometimes you might want to
obtain data differently. To do that, you define object's fields not with
:class:`~lollipop.types.Type` instances, but with :class:`~lollipop.types.Field`
instances.

To access attribute with a different name, use :class:`~lollipop.types.AttributeField`:
::

    MyObject = namedtuple('MyObject', ['other_field'])

    MyObjectType = Object({
        'field1': AttributeField(String(), attribute='other_field'),
    })

To get data from a method instead of an attribute, use
:class:`~lollipop.types.MethodField`: ::

    class Person:
        def __init__(self, first_name, last_name):
            self.first_name = first_name
            self.last_name = last_name

        def get_name(self):
            return self.first_name + ' ' + self.last_name

    PersonType = Object({
        'name': MethodField(String(), method='get_name'),
    })

