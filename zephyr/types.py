from zephyr.errors import ValidationError, ValidationErrorBuilder, \
    ErrorMessagesMixin, merge_errors
from zephyr.utils import is_list, is_dict
from zephyr.compat import string_types, int_types, iteritems


__all__ = [
    'MISSING',
    'Type',
    'Any',
    'String',
    'Integer',
    'Boolean',
    'List',
    'Tuple',
    'Dict',
    'Field',
    'ConstantField',
    'AttributeField',
    'MethodField',
    'FunctionField',
    'Object',
]

#: Special singleton value (like None) to represent case when value is missing.
MISSING = object()


class Type(ErrorMessagesMixin, object):
    """Base class for defining data types.

    :param list validate: A validator or list of validators for this data type.
        Validator is a callable that takes serialized data and raises
        :exc:`~zephyr.errors.ValidationError` if data is invalid.
        Validator return value is ignored.
    """

    default_error_messages = {
        'invalid': 'Invalid value type',
        'required': 'Value is required',
    }

    def __init__(self, validate=None, *args, **kwargs):
        super(Type, self).__init__(*args, **kwargs)
        if validate is None:
            validate = []
        elif callable(validate):
            validate = [validate]

        self._validators = validate

    def validate(self, data):
        """Takes serialized data and returns validation errors or None.

        :param data: Data to validate.
        """
        try:
            self.load(data)
            return {}
        except ValidationError as ve:
            return ve.messages

    def load(self, data):
        """Deserialize data from primitive types. Raises
        :exc:`~zephyr.errors.ValidationError` if data is invalid.

        :param data: Data to deserialize.
        """
        errors_builder = ValidationErrorBuilder()
        for validator in self._validators:
            try:
                validator(data)
            except ValidationError as ve:
                errors_builder.add_errors(ve.messages)
        errors_builder.raise_errors()
        return data

    def dump(self, value):
        """Serialize data to primitive types. Raises
        :exc:`~zephyr.errors.ValidationError` if data is invalid.

        :param value: Value to serialize.
        """
        return value


class Any(Type):
    """Any type. Does not transform/validate given data."""
    pass


class Number(Type):
    num_type = float
    default_error_messages = {
        'invalid': 'Value should be number',
    }

    def _normalize(self, value):
        try:
            return self.num_type(value)
        except (TypeError, ValueError):
            self._fail('invalid')

    def load(self, data):
        if data is MISSING or data is None:
            self._fail('required')

        return super(Number, self).load(self._normalize(data))

    def dump(self, value):
        if value is MISSING or value is None:
            self._fail('required')

        return super(Number, self).dump(self._normalize(value))


class Integer(Number):
    """An integer type."""

    num_type = int
    default_error_messages = {
        'invalid': 'Value should be integer'
    }


class Float(Number):
    """A float type."""

    num_type = float
    default_error_messages = {
        'invalid': 'Value should be float'
    }


class String(Type):
    """A string type."""

    default_error_messages = {
        'invalid': 'Value should be string',
    }

    def load(self, data):
        if data is MISSING or data is None:
            self._fail('required')

        if not isinstance(data, string_types):
            self._fail('invalid')
        return super(String, self).load(data)

    def dump(self, value):
        if value is MISSING or value is None:
            self._fail('required')

        if not isinstance(value, string_types):
            self._fail('invalid')
        return super(String, self).dump(str(value))


class Boolean(Type):
    """A boolean type."""

    default_error_messages = {
        'invalid': 'Value should be boolean',
    }

    def load(self, data):
        if data is MISSING or data is None:
            self._fail('required')

        if not isinstance(data, bool):
            self._fail('invalid')

        return super(Boolean, self).load(data)

    def dump(self, value):
        if value is MISSING or value is None:
            self._fail('required')

        if not isinstance(value, bool):
            self._fail('invalid')

        return super(Boolean, self).dump(bool(value))


class List(Type):
    """A homogenous list type.

    Example: ::

        List(String()).load(['foo', 'bar', 'baz'])

    :param Type item_type: Type of list elements.
    """
    default_error_messages = {
        'invalid': 'Value should be list',
    }

    def __init__(self, item_type, **kwargs):
        super(List, self).__init__(**kwargs)
        self.item_type = item_type

    def load(self, data):
        if data is MISSING or data is None:
            self._fail('required')

        # TODO: Make more intelligent check for collections
        if not is_list(data):
            self._fail('invalid')

        errors_builder = ValidationErrorBuilder()
        items = []
        for idx, item in enumerate(data):
            try:
                items.append(self.item_type.load(item))
            except ValidationError as ve:
                errors_builder.add_errors({idx: ve.messages})
        errors_builder.raise_errors()

        return super(List, self).load(items)

    def dump(self, value):
        if value is MISSING or value is None:
            self._fail('required')

        if not is_list(value):
            self._fail('invalid')

        errors_builder = ValidationErrorBuilder()
        items = []
        for idx, item in enumerate(value):
            try:
                items.append(self.item_type.dump(item))
            except ValidationError as ve:
                errors_builder.add_errors({idx: ve.messages})
        errors_builder.raise_errors()

        return super(List, self).dump(items)


class Tuple(Type):
    """A heterogenous list type.

    Example: ::

        Tuple([String(), Integer(), Boolean()]).load(['foo', 123, False])

    :param list item_types: List of item types.
    """
    default_error_messages = dict(Type.default_error_messages, **{
        'invalid': 'Value should be list',
        'invalid_length': 'Value length should be {expected_length}',
    })

    def __init__(self, item_types, **kwargs):
        super(Tuple, self).__init__(**kwargs)
        self.item_types = item_types

    def load(self, data):
        if data is MISSING or data is None:
            self._fail('required')

        if not is_list(data):
            self._fail('invalid')

        if len(data) != len(self.item_types):
            self._fail('invalid_length', expected_length=len(self.item_types))

        errors_builder = ValidationErrorBuilder()
        result = []
        for idx, (item_type, item) in enumerate(zip(self.item_types, data)):
            try:
                result.add(item_type.load(item))
            except ValidationError as ve:
                errors_builder.add_errors({idx: ve.messages})
        errors_builder.raise_errors()

        return super(Tuple, self).load(result)

    def dump(self, value):
        if value is MISSING or value is None:
            self._fail('required')

        if not is_list(data):
            self._fail('invalid')

        if len(value) != len(self.item_types):
            self._fail('invalid_length', expected_length=len(self.item_types))

        errors_builder = ValidationErrorBuilder()
        result = []
        for idx, (item_type, item) in enumerate(zip(self.item_types, value)):
            try:
                result.add(item_type.dump(item))
            except ValidationError as ve:
                errors_builder.add_errors({idx: ve.messages})
        errors_builder.raise_errors()

        return super(Tuple, self).dump(result)


class DictWithDefault(object):
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

    def get(self, key, default=None):
        return self[key]


class Dict(Type):
    """A dict type. You can specify either a single type for all dict values
    or provide a dict-like mapping object that will return proper Type instance
    for each given dict key.

    Example: ::

        Dict(Integer()).load({'key0': 1, 'key1': 5, 'key2': 15})

        Dict({'foo': String(), 'bar': Integer()}).load({
            'foo': 'hello', 'bar': 123,
        })

    :param dict value_type: A single :class:`Type` for all dict values or mapping
        of allowed keys to :class:`Type` instances.
    """

    default_error_messages = {
        'invalid': 'Value should be dict',
    }

    def __init__(self, value_types=Any(), **kwargs):
        super(Dict, self).__init__(**kwargs)
        if isinstance(value_types, Type):
            value_types = DictWithDefault(default=value_types)
        self.value_types = value_types

    def load(self, data):
        if data is MISSING or data is None:
            self._fail('required')

        if not is_dict(data):
            self._fail('invalid')

        errors_builder = ValidationErrorBuilder()
        result = {}
        for k, v in iteritems(data):
            value_type = self.value_types.get(k)
            if value_type is None:
                continue
            try:
                result[k] = value_type.load(v)
            except ValidationError as ve:
                errors_builder.add_error(k, ve.messages)
        errors_builder.raise_errors()

        return super(Dict, self).load(result)

    def dump(self, value):
        if value is MISSING or value is None:
            self._fail('required')

        if not is_dict(value):
            self._fail('invalid')

        errors_builder = ValidationErrorBuilder()
        result = {}
        for k, v in iteritems(value):
            value_type = self.value_types.get(k)
            if value_type is None:
                continue
            try:
                result[k] = value_type.dump(v)
            except ValidationError as ve:
                errors_builder.add_error(k, ve.messages)
        errors_builder.raise_errors()

        return super(Dict, self).dump(result)


class Field(object):
    """Base class for describing :class:`Object` fields. Defines a way to access
    object fields during serialization/deserialization. Usually it extracts data to
    serialize/deserialize and call `self.field_type.load()` to do data
    transformation.

    :param Type field_type: Field type.
    """
    def __init__(self, field_type):
        super(Field, self).__init__()
        self.field_type = field_type

    def _get_value(self, name, obj):
        raise NotImplemented()

    def load(self, name, data):
        """Deserialize data from primitive types. Raises
        :exc:`~zephyr.errors.ValidationError` if data is invalid.

        :param str name: Name of attribute to deserialize.
        :param data: Raw data to get value to deserialize from.
        """
        return MISSING

    def dump(self, name, obj):
        """Serialize data to primitive types. Raises
        :exc:`~zephyr.errors.ValidationError` if data is invalid.

        :param str name: Name of attribute to serialize.
        :param obj: Application object to extract serialized value from.
        """
        value = self._get_value(name, obj)
        return self.field_type.dump(value)


class ConstantField(Field):
    """Field that always equals to given value.

    :param Type field_type: Field type.
    """
    def __init__(self, field_type, value):
        super(ConstantField, self).__init__(field_type)
        self.value = value

    def _get_value(self, name, obj):
        return self.value


class AttributeField(Field):
    """Field that corresponds to object attribute.

    :param Type field_type: Field type.
    :param str attribute: Use given attribute name instead of field name
        defined in object type.
    """
    def __init__(self, field_type, attribute=None):
        super(AttributeField, self).__init__(field_type)
        self.attribute = attribute

    def _get_value(self, name, obj):
        return getattr(obj, self.attribute or name, MISSING)

    def load(self, name, data):
        value = data.get(name, MISSING)
        return self.field_type.load(value)


class MethodField(Field):
    """Field that is result of method invocation.

    Example: ::

        class Person(object):
            def __init__(self, first_name, last_name):
                self.first_name = first_name
                self.last_name = last_name

            def get_name(self):
                return self.first_name + ' ' + self.last_name

        PersonType = Object({
            'name': MethodField(String(), 'get_name'),
        }, constructor=Person)


    :param Type field_type: Field type.
    :param str method: Method name. Method should not take any arguments.
    """
    def __init__(self, field_type, method):
        super(MethodField, self).__init__(field_type)
        self.method = method

    def _get_value(self, name, obj):
        if self.method:
            name = self.method
        if not hasattr(obj, name):
            raise ValueError('Object does not have method %s' % name)
        if not callable(getattr(obj, name)):
            raise ValueError('Value %s is not callable' % name)
        return getattr(obj, name)()


class FunctionField(Field):
    """Field that is result of function invocation.

    Example: ::

        class Person(object):
            def __init__(self, first_name, last_name):
                self.first_name = first_name
                self.last_name = last_name

        def get_name(person):
            return person.first_name + ' ' + person.last_name

        PersonType = Object({
            'name': FunctionField(String(), get_name),
        }, constructor=Person)


    :param Type field_type: Field type.
    :param callable function: Function that takes source object and returns
        field value.
    """
    def __init__(self, field_type, function):
        super(FunctionField, self).__init__(field_type)
        self.function = function

    def _get_value(self, name, obj):
        return self.function(name, obj)


class Object(Type):
    """An object type. Serializes to a dict of field names to serialized field
    values. Parametrized with field names to types mapping.
    The way values are obtained during serialization is determined by type of
    field object in :attr:`~Object.fields` mapping (see :class:`ConstantField`,
    :class:`AttributeField`, :class:`MethodField` for details). You can specify
    either :class:`Field` object or a :class:`Type` object. In later case,
    :class:`Type` will be automatically wrapped with a default field type, which
    is controlled by :attr:`~Object.default_field_type` constructor argument.


    Example: ::

        class Person(object):
            def __init__(self, name, age):
                self.name = name
                self.age = age

        PersonType = Object({
            'name': String(),
            'age': Integer(),
        }, constructor=Person)
        PersonType.load({'name': 'John', 'age': 42})
        # => Person(name='John', age=42)

    :param dict fields: Mapping of object field names to :class:`Type` or
        :class:`Field` objects.
    :param callable contructor: Deserialized value constructor. Constructor
        should take all fields values as keyword arguments.
    :param Field default_field_type: Default field type to use for fields defined
        by their type.
    :param bool allow_extra_fields: If False, it will raise
        :exc:`~zephyr.errors.ValidationError` for all extra dict keys during
        deserialization. If True, will ignore all extra fields.
    """

    default_error_messages = {
        'invalid': 'Value should be dict',
        'unknown': 'Unknown field',
    }

    def __init__(self, fields, constructor=dict,
                 default_field_type=AttributeField,
                 allow_extra_fields=True,
                 **kwargs):
        super(Object, self).__init__(**kwargs)
        self.fields = dict([
            (name, field if isinstance(field, Field) else default_field_type(field))
            for name, field in iteritems(fields)
        ])
        self.constructor = constructor
        self.allow_extra_fields = allow_extra_fields

    def load(self, data):
        if data is MISSING or data is None:
            self._fail('required')

        if not is_dict(data):
            self._fail('invalid')

        errors_builder = ValidationErrorBuilder()
        result = {}
        for name, field in iteritems(self.fields):
            try:
                loaded = field.load(name, data)
                if loaded != MISSING:
                    result[name] = loaded
            except ValidationError as ve:
                errors_builder.add_error(name, ve.messages)

        if not self.allow_extra_fields:
            for name in data:
                if name not in self.fields:
                    errors_builder.add_error(name, self._error_messages['unknown'])

        errors_builder.raise_errors()

        return self.constructor(**super(Object, self).load(result))

    def dump(self, obj):
        if obj is MISSING or obj is None:
            self._fail('required')

        errors_builder = ValidationErrorBuilder()
        result = {}
        for name, field in iteritems(self.fields):
            try:
                dumped = field.dump(name, obj)
                if dumped != MISSING:
                    result[name] = dumped
            except ValidationError as ve:
                errors_builder.add_error(k, ve.messages)
        errors_builder.raise_errors()

        return super(Object, self).dump(result)
