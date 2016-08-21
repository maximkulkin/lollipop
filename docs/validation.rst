.. _validation:

Validation
==========

Validators
----------

Validation allows to check that data is consistent. It is run on raw data before
it is deserialized. E.g. :class:`~lollipop.types.DateTime` deserializes string to
:class:`datetime.datetime` so validations are run on a string before it is parsed.
In :class:`~lollipop.types.Object` validations are run on a dictionary of fields
but after fields themselves were already deserialized. So if you had a field of type
:class:`~lollipop.types.DateTime` your validator will get a dictionary with
:class:`~datetime.datetime` object.

Validators are just callable objects that take one or two arguments (first is
the data to be validated, second (optional) is the operation context) and raise
:class:`~lollipop.errors.ValidationError` in case of errors. Return value of
validator is always ignored.

To add validator or validators to a type, you pass them to type contructor's
`validate` argument: ::

    def is_odd(data):
        if data % 2 == 0:
            raise ValidationError('Value should be odd')

    MyNumber = Integer(validate=is_odd)
    MyNumber.load(1)  # => returns 1
    MyNumber.load(2)  # => raises ValidationError('Value should be odd')

In simple cases you can create a :class:`~lollipop.validators.Predicate` validator
for which you need to specify a boolean function and error message: ::

    is_odd = Predicate(lambda x: x % 2 != 0, 'Value should be odd')

    MyNumber = Integer(validate=is_odd)

In more complex cases where you need to parametrize validator with some data
it is more convenient to create a validator class: ::

    from lollipop.validators import Validator

    class GreaterThan(Validator):
        default_error_messages = {
            'greater': 'Value should be greater than {value}'
        }

        def __init__(self, value, **kwargs):
            super(GreaterThan, self).__init__(**kwargs)
            self.value = value

        def __call__(self, data):
            if data <= self.value:
                self._fail('greater', data=data, value=self.value)
                

The last example demonstrates how you can support customizing error messages in
your validators: there is a default error message keyed with string 'greater' and
users can override it when creating validator with supplying new set of error
messages in validator constructor: ::

    message = 'Should be greater than answer to the Ultimate Question of Life, the Universe, and Everything'
    Integer(validate=GreaterThan(42, error_messages={'greater': message}))


Accumulating Errors
-------------------
If you writing a whole-object validator that checks various field combinations for
correctness, it might be hard to accumulate errors. That's why the library provides
a special builder for errors - :class:`~lollipop.errors.ValidationErrorBuilder`: ::

    def validate_my_object(data):
        builder = ValidationErrorBuilder()

        if data['foo']['bar'] >= data['baz']['bam']:
            builder.add_error('foo.bar': 'Should be less than bam')
        if data['foo']['quux'] >= data['baz']['bam']:
            builder.add_error('foo.quux': 'Should be less than bam')

        builder.raise_errors()
