from lollipop.errors import ValidationError, ValidationErrorBuilder, \
    ErrorMessagesMixin, merge_errors
from lollipop.utils import is_list, is_dict, call_with_context
from lollipop.compat import string_types, int_types, iteritems
import datetime


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
    'Optional',
    'LoadOnly',
    'DumpOnly',
]

class MissingType(object):
    def __repr__(self):
        return '<MISSING>'


#: Special singleton value (like None) to represent case when value is missing.
MISSING = MissingType()


class Type(ErrorMessagesMixin, object):
    """Base class for defining data types.

    :param list validate: A validator or list of validators for this data type.
        Validator is a callable that takes serialized data and raises
        :exc:`~lollipop.errors.ValidationError` if data is invalid.
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

    def validate(self, data, context=None):
        """Takes serialized data and returns validation errors or None.

        :param data: Data to validate.
        :param context: Context data.
        """
        try:
            self.load(data, context)
            return {}
        except ValidationError as ve:
            return ve.messages

    def load(self, data, context=None):
        """Deserialize data from primitive types. Raises
        :exc:`~lollipop.errors.ValidationError` if data is invalid.

        :param data: Data to deserialize.
        :param context: Context data.
        """
        errors_builder = ValidationErrorBuilder()
        for validator in self._validators:
            try:
                call_with_context(validator, context, data)
            except ValidationError as ve:
                errors_builder.add_errors(ve.messages)
        errors_builder.raise_errors()
        return data

    def dump(self, value, context=None):
        """Serialize data to primitive types. Raises
        :exc:`~lollipop.errors.ValidationError` if data is invalid.

        :param value: Value to serialize.
        :param context: Context data.
        """
        return value

    def __repr__(self):
        return '<{klass}>'.format(klass=self.__class__.__name__)


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

    def load(self, data, *args, **kwargs):
        if data is MISSING or data is None:
            self._fail('required')

        return super(Number, self).load(self._normalize(data), *args, **kwargs)

    def dump(self, value, *args, **kwargs):
        if value is MISSING or value is None:
            self._fail('required')

        return super(Number, self).dump(self._normalize(value), *args, **kwargs)


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

    def load(self, data, *args, **kwargs):
        if data is MISSING or data is None:
            self._fail('required')

        if not isinstance(data, string_types):
            self._fail('invalid')
        return super(String, self).load(data, *args, **kwargs)

    def dump(self, value, *args, **kwargs):
        if value is MISSING or value is None:
            self._fail('required')

        if not isinstance(value, string_types):
            self._fail('invalid')
        return super(String, self).dump(str(value), *args, **kwargs)


class Boolean(Type):
    """A boolean type."""

    default_error_messages = {
        'invalid': 'Value should be boolean',
    }

    def load(self, data, *args, **kwargs):
        if data is MISSING or data is None:
            self._fail('required')

        if not isinstance(data, bool):
            self._fail('invalid')

        return super(Boolean, self).load(data, *args, **kwargs)

    def dump(self, value, *args, **kwargs):
        if value is MISSING or value is None:
            self._fail('required')

        if not isinstance(value, bool):
            self._fail('invalid')

        return super(Boolean, self).dump(bool(value), *args, **kwargs)


class DateTime(Type):
    """A date and time type which serializes into string.

    :param str format: Format string (see :func:`datetime.datetime.strptime`) or
        one of predefined format names (e.g. 'iso8601', 'rfc3339', etc.
        See :const:`~DateTime.FORMATS`)
    :param kwargs: Same keyword arguments as for :class:`Type`.
    """

    FORMATS = {
        'iso': '%Y-%m-%dT%H:%M:%S%Z',  # shortcut for iso8601
        'iso8601': '%Y-%m-%dT%H:%M:%S%Z',
        'rfc': '%Y-%m-%d',             # shortcut for rfc3339
        'rfc3339': '%Y-%m-%dT%H:%M:%S%Z',
        'rfc822': '%d %b %y %H:%M:%S %Z',
    }

    DEFAULT_FORMAT = 'iso'

    default_error_messages = {
        'invalid': 'Invalid datetime value',
        'invalid_type': 'Value should be string',
        'invalid_format': 'Value should match datetime format',
    }

    def __init__(self, format=None, *args, **kwargs):
        super(DateTime, self).__init__(*args, **kwargs)
        self.format = format or self.DEFAULT_FORMAT

    def _convert_value(self, value):
        return value

    def load(self, data, *args, **kwargs):
        if data is MISSING or data is None:
            self._fail('required')

        if not isinstance(data, string_types):
            self._fail('invalid_type', data=data)

        format_str = self.FORMATS.get(self.format, self.format)
        try:
            date = self._convert_value(datetime.datetime.strptime(data, format_str))
            return super(DateTime, self).load(date, *args, **kwargs)
        except ValueError:
            self._fail('invalid_format', data=data, format=format_str)

    def dump(self, value, *args, **kwargs):
        if value is MISSING or value is None:
            self._fail('required')

        format_str = self.FORMATS.get(self.format, self.format)
        try:
            return super(DateTime, self)\
                .dump(value.strftime(format_str), *args, **kwargs)
        except (AttributeError, ValueError):
            self._fail('invalid', data=value)


class Date(DateTime):
    """A date type which serializes into string.

    :param str format: Format string (see :func:`datetime.datetime.strptime`) or
        one of predefined format names (e.g. 'iso8601', 'rfc3339', etc.
        See :const:`~Date.FORMATS`)
    :param kwargs: Same keyword arguments as for :class:`Type`.
    """

    FORMATS = {
        'iso': '%Y-%m-%d',  # shortcut for iso8601
        'iso8601': '%Y-%m-%d',
        'rfc': '%Y-%m-%d',  # shortcut for rfc3339
        'rfc3339': '%Y-%m-%d',
        'rfc822': '%d %b %y',
    }

    DEFAULT_FORMAT = 'iso'

    default_error_messages = {
        'invalid': 'Invalid date value',
        'invalid_type': 'Value should be string',
        'invalid_format': 'Value should match date format',
    }

    def _convert_value(self, value):
        return value.date()


class Time(DateTime):
    """A date type which serializes into string.

    :param str format: Format string (see :func:`datetime.datetime.strptime`) or
        one of predefined format names (e.g. 'iso8601', 'rfc3339', etc.)
    :param kwargs: Same keyword arguments as for :class:`Type`.
    """

    FORMATS = {
        'iso': '%H:%M:%S',  # shortcut for iso8601
        'iso8601': '%H:%M:%S',
    }

    DEFAULT_FORMAT = 'iso'

    default_error_messages = {
        'invalid': 'Invalid time value',
        'invalid_type': 'Value should be string',
        'invalid_format': 'Value should match time format',
    }

    def _convert_value(self, value):
        return value.time()


class List(Type):
    """A homogenous list type.

    Example: ::

        List(String()).load(['foo', 'bar', 'baz'])

    :param Type item_type: Type of list elements.
    :param kwargs: Same keyword arguments as for :class:`Type`.
    """
    default_error_messages = {
        'invalid': 'Value should be list',
    }

    def __init__(self, item_type, **kwargs):
        super(List, self).__init__(**kwargs)
        self.item_type = item_type

    def load(self, data, *args, **kwargs):
        if data is MISSING or data is None:
            self._fail('required')

        # TODO: Make more intelligent check for collections
        if not is_list(data):
            self._fail('invalid')

        errors_builder = ValidationErrorBuilder()
        items = []
        for idx, item in enumerate(data):
            try:
                items.append(self.item_type.load(item, *args, **kwargs))
            except ValidationError as ve:
                errors_builder.add_errors({idx: ve.messages})
        errors_builder.raise_errors()

        return super(List, self).load(items, *args, **kwargs)

    def dump(self, value, *args, **kwargs):
        if value is MISSING or value is None:
            self._fail('required')

        if not is_list(value):
            self._fail('invalid')

        errors_builder = ValidationErrorBuilder()
        items = []
        for idx, item in enumerate(value):
            try:
                items.append(self.item_type.dump(item, *args, **kwargs))
            except ValidationError as ve:
                errors_builder.add_errors({idx: ve.messages})
        errors_builder.raise_errors()

        return super(List, self).dump(items, *args, **kwargs)

    def __repr__(self):
        return '<{klass} of {item_type}>'.format(
            klass=self.__class__.__name__,
            item_type=repr(self.item_type),
        )


class Tuple(Type):
    """A heterogenous list type.

    Example: ::

        Tuple([String(), Integer(), Boolean()]).load(['foo', 123, False])

    :param list item_types: List of item types.
    :param kwargs: Same keyword arguments as for :class:`Type`.
    """
    default_error_messages = dict(Type.default_error_messages, **{
        'invalid': 'Value should be list',
        'invalid_length': 'Value length should be {expected_length}',
    })

    def __init__(self, item_types, **kwargs):
        super(Tuple, self).__init__(**kwargs)
        self.item_types = item_types

    def load(self, data, *args, **kwargs):
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
                result.add(item_type.load(item, *args, **kwargs))
            except ValidationError as ve:
                errors_builder.add_errors({idx: ve.messages})
        errors_builder.raise_errors()

        return super(Tuple, self).load(result, *args, **kwargs)

    def dump(self, value, *args, **kwargs):
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
                result.add(item_type.dump(item, *args, **kwargs))
            except ValidationError as ve:
                errors_builder.add_errors({idx: ve.messages})
        errors_builder.raise_errors()

        return super(Tuple, self).dump(result, *args, **kwargs)

    def __repr__(self):
        return '<{klass} of {item_types}>'.format(
            klass=self.__class__.__name__,
            item_type=repr(self.item_types),
        )


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
    :param kwargs: Same keyword arguments as for :class:`Type`.
    """

    default_error_messages = {
        'invalid': 'Value should be dict',
    }

    def __init__(self, value_types=Any(), **kwargs):
        super(Dict, self).__init__(**kwargs)
        if isinstance(value_types, Type):
            value_types = DictWithDefault(default=value_types)
        self.value_types = value_types

    def load(self, data, *args, **kwargs):
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
                result[k] = value_type.load(v, *args, **kwargs)
            except ValidationError as ve:
                errors_builder.add_error(k, ve.messages)
        errors_builder.raise_errors()

        return super(Dict, self).load(result, *args, **kwargs)

    def dump(self, value, *args, **kwargs):
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
                result[k] = value_type.dump(v, *args, **kwargs)
            except ValidationError as ve:
                errors_builder.add_error(k, ve.messages)
        errors_builder.raise_errors()

        return super(Dict, self).dump(result, *args, **kwargs)

    def __repr__(self):
        return '<{klass}>'.format(klass=self.__class__.__name__)


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

    def _get_value(self, name, obj, context=None):
        raise NotImplemented()

    def load(self, name, data, *args, **kwargs):
        """Deserialize data from primitive types. Raises
        :exc:`~lollipop.errors.ValidationError` if data is invalid.

        :param str name: Name of attribute to deserialize.
        :param data: Raw data to get value to deserialize from.
        """
        return MISSING

    def dump(self, name, obj, *args, **kwargs):
        """Serialize data to primitive types. Raises
        :exc:`~lollipop.errors.ValidationError` if data is invalid.

        :param str name: Name of attribute to serialize.
        :param obj: Application object to extract serialized value from.
        """
        value = self._get_value(name, obj)
        return self.field_type.dump(value, *args, **kwargs)


class ConstantField(Field):
    """Field that always equals to given value.

    :param Type field_type: Field type.
    """
    def __init__(self, field_type, value):
        super(ConstantField, self).__init__(field_type)
        self.value = value

    def _get_value(self, name, obj, *args, **kwargs):
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

    def _get_value(self, name, obj, *args, **kwargs):
        return getattr(obj, self.attribute or name, MISSING)

    def load(self, name, data, *args, **kwargs):
        value = data.get(name, MISSING)
        return self.field_type.load(value, *args, **kwargs)


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

    def _get_value(self, name, obj, context=None):
        if self.method:
            name = self.method
        if not hasattr(obj, name):
            raise ValueError('Object does not have method %s' % name)
        if not callable(getattr(obj, name)):
            raise ValueError('Value %s is not callable' % name)
        return call_with_context(getattr(obj, name), context)


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

    def _get_value(self, name, obj, context=None):
        return call_with_context(self.function, context, name, obj)


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
        :exc:`~lollipop.errors.ValidationError` for all extra dict keys during
        deserialization. If True, will ignore all extra fields.
    :param kwargs: Same keyword arguments as for :class:`Type`.
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

    def load(self, data, *args, **kwargs):
        if data is MISSING or data is None:
            self._fail('required')

        if not is_dict(data):
            self._fail('invalid')

        errors_builder = ValidationErrorBuilder()
        result = {}
        for name, field in iteritems(self.fields):
            try:
                loaded = field.load(name, data, *args, **kwargs)
                if loaded != MISSING:
                    result[name] = loaded
            except ValidationError as ve:
                errors_builder.add_error(name, ve.messages)

        if not self.allow_extra_fields:
            for name in data:
                if name not in self.fields:
                    errors_builder.add_error(name, self._error_messages['unknown'])

        errors_builder.raise_errors()

        return self.constructor(**super(Object, self).load(result, *args, **kwargs))

    def dump(self, obj, *args, **kwargs):
        if obj is MISSING or obj is None:
            self._fail('required')

        errors_builder = ValidationErrorBuilder()
        result = {}
        for name, field in iteritems(self.fields):
            try:
                dumped = field.dump(name, obj, *args, **kwargs)
                if dumped != MISSING:
                    result[name] = dumped
            except ValidationError as ve:
                errors_builder.add_error(k, ve.messages)
        errors_builder.raise_errors()

        return super(Object, self).dump(result, *args, **kwargs)


class Optional(Type):
    """A wrapper type which makes values optional: if value is missing or None,
    it will not transform it with an inner type but instead will return None
    (or any other configured value).

    Example: ::

        UserType = Object({
            'email': String(),           # by default types require valid values
            'name': Optional(String()),  # value can be omitted or None
            'role': Optional(            # when value is omitted or None, use given value
                String(validate=AnyOf(['admin', 'customer'])),
                load_default='customer',
            ),
        })

    :param Type inner_type: Actual type that should be optional.
    :param load_default: Value to use when value is missing on deserialization.
    :param dump_default: Value to use when value is missing on serialization.
    :param kwargs: Same keyword arguments as for :class:`Type`.
    """
    def __init__(self, inner_type,
                 load_default=None, dump_default=None,
                 **kwargs):
        super(Optional, self).__init__(**kwargs)
        self.inner_type = inner_type
        self.load_default = load_default
        self.dump_default = dump_default

    def load(self, data, *args, **kwargs):
        if data is MISSING or data is None:
            return self.load_default
        return super(Optional, self).load(
            self.inner_type.load(data, *args, **kwargs),
            *args, **kwargs
        )

    def dump(self, data, *args, **kwargs):
        if data is MISSING or data is None:
            return self.dump_default
        return super(Optional, self).dump(
            self.inner_type.dump(data, *args, **kwargs),
            *args, **kwargs
        )

    def __repr__(self):
        return '<{klass} {inner_type}>'.format(
            klass=self.__class__.__name__,
            inner_type=repr(self.inner_type),
        )


class LoadOnly(Type):
    """A wrapper type which proxies loading to inner type but always returns
    :obj:`MISSING` on dump.

    Example: ::

        UserType = Object({
            'name': String(),
            'password': LoadOnly(String()),
        })

    :param Type inner_type: Data type.
    """
    def __init__(self, inner_type):
        super(LoadOnly, self).__init__()
        self.inner_type = inner_type

    def load(self, data, *args, **kwargs):
        return self.inner_type.load(data, *args, **kwargs)

    def dump(self, data, context=None):
        return MISSING

    def __repr__(self):
        return '<{klass} {inner_type}>'.format(
            klass=self.__class__.__name__,
            inner_type=repr(self.inner_type),
        )


class DumpOnly(Type):
    """A wrapper type which proxies dumping to inner type but always returns
    :obj:`MISSING` on load.

    Example: ::

        UserType = Object({
            'name': String(),
            'created_at': DumpOnly(DateTime()),
        })

    :param Type inner_type: Data type.
    """
    def __init__(self, inner_type):
        super(DumpOnly, self).__init__()
        self.inner_type = inner_type

    def load(self, data, *args, **kwargs):
        return MISSING

    def dump(self, data, *args, **kwargs):
        return self.inner_type.dump(data, *args, **kwargs)

    def __repr__(self):
        return '<{klass} {inner_type}>'.format(
            klass=self.__class__.__name__,
            inner_type=repr(self.inner_type),
        )
