from lollipop.errors import ValidationError, ValidationErrorBuilder, \
    ErrorMessagesMixin, merge_errors
from lollipop.utils import is_list, is_dict, make_context_aware, constant, identity
from lollipop.compat import string_types, int_types, iteritems, OrderedDict
import datetime


__all__ = [
    'MISSING',
    'Type',
    'Any',
    'String',
    'Integer',
    'Float',
    'Boolean',
    'List',
    'Tuple',
    'Dict',
    'OneOf',
    'type_name_hint',
    'dict_value_hint',
    'Field',
    'AttributeField',
    'MethodField',
    'FunctionField',
    'Object',
    'Constant',
    'Optional',
    'LoadOnly',
    'DumpOnly',
    'Transform',
    'validated_type',
]

class MissingType(object):
    def __repr__(self):
        return '<MISSING>'


#: Special singleton value (like None) to represent case when value is missing.
MISSING = MissingType()


class ValidatorCollection(object):
    def __init__(self, validators):
        self._validators = [make_context_aware(validator, 1)
                            for validator in validators]

    def append(self, validator):
        self._validators.append(make_context_aware(validator, 1))

    def insert(self, idx, validator):
        self._validators.insert(idx, make_context_aware(validator, 1))

    def __len__(self):
        return len(self._validators)

    def __getitem__(self, idx):
        return self._validators[idx]

    def __setitem__(self, idx, validator):
        self._validators[idx] = make_context_aware(validator, 1)

    def __delitem__(self, idx):
        del self._validators[idx]

    def __iter__(self):
        for validator in self._validators:
            yield validator


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

    def __init__(self, name=None, description=None, validate=None, *args, **kwargs):
        super(Type, self).__init__(*args, **kwargs)
        if validate is None:
            validate = []
        elif callable(validate):
            validate = [validate]

        self.name = name
        self.description = description
        self._validators = ValidatorCollection(validate)

    def validate(self, data, context=None):
        """Takes serialized data and returns validation errors or None.

        :param data: Data to validate.
        :param context: Context data.
        :returns: validation errors or None
        """
        try:
            self.load(data, context)
            return None
        except ValidationError as ve:
            return ve.messages

    def load(self, data, context=None):
        """Deserialize data from primitive types. Raises
        :exc:`~lollipop.errors.ValidationError` if data is invalid.

        :param data: Data to deserialize.
        :param context: Context data.
        :returns: Loaded data
        :raises: :exc:`~lollipop.errors.ValidationError`
        """
        errors_builder = ValidationErrorBuilder()
        for validator in self._validators:
            try:
                validator(data, context)
            except ValidationError as ve:
                errors_builder.add_errors(ve.messages)
        errors_builder.raise_errors()
        return data

    def dump(self, value, context=None):
        """Serialize data to primitive types. Raises
        :exc:`~lollipop.errors.ValidationError` if data is invalid.

        :param value: Value to serialize.
        :param context: Context data.
        :returns: Serialized data.
        :raises: :exc:`~lollipop.errors.ValidationError`
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
    default_error_messages = {
        'invalid': 'Value should be list',
        'invalid_length': 'Value length should be {expected_length}',
    }

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
                result.append(item_type.load(item, *args, **kwargs))
            except ValidationError as ve:
                errors_builder.add_errors({idx: ve.messages})
        errors_builder.raise_errors()

        return super(Tuple, self).load(result, *args, **kwargs)

    def dump(self, value, *args, **kwargs):
        if value is MISSING or value is None:
            self._fail('required')

        if not is_list(value):
            self._fail('invalid')

        if len(value) != len(self.item_types):
            self._fail('invalid_length', expected_length=len(self.item_types))

        errors_builder = ValidationErrorBuilder()
        result = []
        for idx, (item_type, item) in enumerate(zip(self.item_types, value)):
            try:
                result.append(item_type.dump(item, *args, **kwargs))
            except ValidationError as ve:
                errors_builder.add_errors({idx: ve.messages})
        errors_builder.raise_errors()

        return super(Tuple, self).dump(result, *args, **kwargs)

    def __repr__(self):
        return '<{klass} of {item_types}>'.format(
            klass=self.__class__.__name__,
            item_types=repr(self.item_types),
        )


def type_name_hint(data):
    """Returns type name of given value.

    To be used as a type hint in :class:`OneOf`.
    """
    return data.__class__.__name__


def dict_value_hint(key, mapper=None):
    """Returns a function that takes a dictionary and returns value of
    particular key. The returned value can be optionally processed by `mapper`
    function.

    To be used as a type hint in :class:`OneOf`.
    """
    if mapper is None:
        mapper = identity

    def hinter(data):
        return mapper(data.get(key))

    return hinter


class OneOf(Type):
    """

    Example: ::

        class Foo(object):
            def __init__(self, foo):
                self.foo = foo

        class Bar(object):
            def __init__(self, bar):
                self.bar = bar

        FooType = Object({'foo': String()}, constructor=Foo)
        BarType = Object({'bar': Integer()}, constructor=Bar)

        def object_with_type(name, subject_type):
            return Object(subject_type, {'type': name},
                          constructor=subject_type.constructor)

        FooBarType = OneOf({
            'Foo': object_with_type('Foo', FooType),
            'Bar': object_with_type('Bar', BarType),
        }, dump_hint=type_name_hint, load_hint=dict_value_hint('type'))

        List(FooBarType).dump([Foo(foo='hello'), Bar(bar=123)])
        # => [{'type': 'Foo', 'foo': 'hello'}, {'type': 'Bar', 'bar': 123}]

        List(FooBarType).load([{'type': 'Foo', 'foo': 'hello'},
                               {'type': 'Bar', 'bar': 123}])
        # => [Foo(foo='hello'), Bar(bar=123)]
    """

    default_error_messages = {
        'invalid': 'Invalid data',
        'unknown_type_id': 'Unknown type ID: {type_id}',
        'no_type_matched': 'No type matched',
    }

    def __init__(self, types,
                 load_hint=type_name_hint,
                 dump_hint=type_name_hint,
                 *args, **kwargs):
        super(OneOf, self).__init__(*args, **kwargs)
        self.types = types
        self.load_hint = load_hint
        self.dump_hint = dump_hint

    def load(self, data, *args, **kwargs):
        if data is MISSING or data is None:
            self._fail('required')

        if is_dict(self.types) and self.load_hint:
            type_id = self.load_hint(data)
            if type_id not in self.types:
                self._fail('unknown_type_id', type_id=type_id)

            item_type = self.types[type_id]
            result = item_type.load(data, *args, **kwargs)
            return super(OneOf, self).load(result, *args, **kwargs)
        else:
            for item_type in (self.types.values() if is_dict(self.types) else self.types):
                try:
                    result = item_type.load(data, *args, **kwargs)
                    return super(OneOf, self).load(result, *args, **kwargs)
                except ValidationError as ve:
                    pass

            self._fail('no_type_matched')

    def dump(self, data, *args, **kwargs):
        if data is MISSING or data is None:
            self._fail('required')

        if is_dict(self.types) and self.dump_hint:
            type_id = self.dump_hint(data)
            if type_id not in self.types:
                self._fail('unknown_type_id', type_id=type_id)

            item_type = self.types[type_id]
            result = item_type.dump(data, *args, **kwargs)
            return super(OneOf, self).dump(result, *args, **kwargs)
        else:
            for item_type in (self.types.values() if is_dict(self.types) else self.types):
                try:
                    result = item_type.dump(data, *args, **kwargs)
                    return super(OneOf, self).dump(result, *args, **kwargs)
                except ValidationError as ve:
                    pass

            self._fail('no_type_matched')

    def __repr__(self):
        return '<{klass} {types}>'.format(
            klass=self.__class__.__name__,
            types=repr(self.types),
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

    :param dict value_types: A single :class:`Type` for all dict values or mapping
        of allowed keys to :class:`Type` instances (defaults to :class:`Any`)
    :param Type key_type: Type for dictionary keys (defaults to :class:`Any`).
        Can be used to either transform or validate dictionary keys.
    :param kwargs: Same keyword arguments as for :class:`Type`.
    """

    default_error_messages = {
        'invalid': 'Value should be dict',
    }

    def __init__(self, value_types=None, key_type=None, **kwargs):
        super(Dict, self).__init__(**kwargs)
        if value_types is None:
            value_types = DictWithDefault(default=Any())
        elif isinstance(value_types, Type):
            value_types = DictWithDefault(default=value_types)
        self.value_types = value_types
        self.key_type = key_type or Any()

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
                k = self.key_type.load(k, *args, **kwargs)
            except ValidationError as ve:
                errors_builder.add_error(k, ve.messages)

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
                k = self.key_type.dump(k, *args, **kwargs)
            except ValidationError as ve:
                errors_builder.add_error(k, ve.messages)

            try:
                result[k] = value_type.dump(v, *args, **kwargs)
            except ValidationError as ve:
                errors_builder.add_error(k, ve.messages)

        errors_builder.raise_errors()

        return super(Dict, self).dump(result, *args, **kwargs)

    def __repr__(self):
        return '<{klass} of {value_types}>'.format(
            klass=self.__class__.__name__,
            value_types=repr(self.value_types),
        )


class Constant(Type):
    """Type that always serializes to given value and
    checks this value on deserialize.

    :param value: Value constant for this field.
    :param Type field_type: Field type.
    """

    default_error_messages = {
        'required': 'Value is required',
        'value': 'Value is incorrect',
    }

    def __init__(self, value, field_type=Any(), *args, **kwargs):
        super(Constant, self).__init__(*args, **kwargs)
        self.value = value
        self.field_type = field_type

    def load(self, data, *args, **kwargs):
        value = self.field_type.load(data)
        if value is MISSING or value is None:
            self._fail('required')

        if value != self.value:
            self._fail('value')

        return MISSING

    def dump(self, value, *args, **kwargs):
        return self.field_type.dump(self.value, *args, **kwargs)

    def __repr__(self):
        return '<{klass} {value} of type {field_type}>'.format(
            klass=self.__class__.__name__,
            value=repr(self.value),
            field_type=repr(self.field_type),
        )


class Field(ErrorMessagesMixin):
    """Base class for describing :class:`Object` fields. Defines a way to access
    object fields during serialization/deserialization. Usually it extracts data to
    serialize/deserialize and call `self.field_type.load()` to do data
    transformation.

    :param Type field_type: Field type.
    """
    def __init__(self, field_type, *args, **kwargs):
        super(Field, self).__init__(*args, **kwargs)
        self.field_type = field_type

    def get_value(self, name, obj, context=None):
        """Get value of field `name` from object `obj`.

        :params str name: Field name.
        :params obj: Object to get field value from.
        :returns: Field value.
        """
        raise NotImplemented()

    def set_value(self, name, obj, value, context=None):
        """Set given value of field `name` to object `obj`.

        :params str name: Field name.
        :params obj: Object to get field value from.
        :params value: Field value to set.
        """
        raise NotImplemented()

    def load(self, name, data, *args, **kwargs):
        """Deserialize data from primitive types. Raises
        :exc:`~lollipop.errors.ValidationError` if data is invalid.

        :param str name: Name of attribute to deserialize.
        :param data: Raw data to get value to deserialize from.
        :param kwargs: Same keyword arguments as for :meth:`Type.load`.
        :returns: Loaded data.
        :raises: :exc:`~lollipop.errors.ValidationError`
        """
        return self.field_type.load(data.get(name, MISSING), *args, **kwargs)

    def load_into(self, obj, name, data, inplace=True, *args, **kwargs):
        """Deserialize data from primitive types updating existing object.
        Raises :exc:`~lollipop.errors.ValidationError` if data is invalid.

        :param obj: Object to update with deserialized data.
        :param str name: Name of attribute to deserialize.
        :param data: Raw data to get value to deserialize from.
        :param bool inplace: If True update data inplace;
            otherwise - create new data.
        :param kwargs: Same keyword arguments as for :meth:`load`.
        :returns: Loaded data.
        :raises: :exc:`~lollipop.errors.ValidationError`
        """
        if obj is None:
            raise ValueError('Load target should not be None')

        value = data.get(name, MISSING)

        if value is MISSING:
            return

        target = self.get_value(name, obj, *args, **kwargs)
        if target is not None and target is not MISSING \
                and hasattr(self.field_type, 'load_into'):
            return self.field_type.load_into(target, value, inplace=inplace,
                                             *args, **kwargs)
        else:
            return self.field_type.load(value, *args, **kwargs)

    def dump(self, name, obj, *args, **kwargs):
        """Serialize data to primitive types. Raises
        :exc:`~lollipop.errors.ValidationError` if data is invalid.

        :param str name: Name of attribute to serialize.
        :param obj: Application object to extract serialized value from.
        :returns: Serialized data.
        :raises: :exc:`~lollipop.errors.ValidationError`
        """
        value = self.get_value(name, obj)
        return self.field_type.dump(value, *args, **kwargs)

    def __repr__(self):
        return '<{klass} {field_type}>'.format(
            klass=self.__class__.__name__,
            field_type=repr(self.field_type),
        )


class AttributeField(Field):
    """Field that corresponds to object attribute.
    Subclasses can use `name_to_attribute` field to convert field names to
    attribute names.

    :param Type field_type: Field type.
    :param attribute: Can be either string or callable. If string, use given
        attribute name instead of field name defined in object type.
        If callable, should take a single argument - name of field - and
        return name of corresponding object attribute to obtain value from.
    """
    def __init__(self, field_type, attribute=None, *args, **kwargs):
        super(AttributeField, self).__init__(field_type, *args, **kwargs)
        if attribute is None:
            attribute = identity
        elif not callable(attribute):
            attribute = constant(attribute)
        self.name_to_attribute = attribute

    def get_value(self, name, obj, *args, **kwargs):
        return getattr(obj, self.name_to_attribute(name), MISSING)

    def set_value(self, name, obj, value, *args, **kwargs):
        setattr(obj, self.name_to_attribute(name), value)


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
    :param get: Can be either string or callable. If string, use target object
        method with given name to obain value.
        If callable, should take field name and return name of object
        method to use.
        Referenced method should take no argument - new field value to set.
    :param set: Can be either string or callable. If string, use target object
        method with given name to set value in object.
        If callable, should take field name and return name of object
        method to use.
        Referenced method should take 1 argument - new field value to set.
    :param kwargs: Same keyword arguments as for :class:`Field`.
    """
    def __init__(self, field_type, get=None, set=None, *args, **kwargs):
        super(MethodField, self).__init__(field_type, *args, **kwargs)
        if get is not None:
            if not callable(get):
                get = constant(get)
        if set is not None:
            if not callable(set):
                set = constant(set)
        self.get_method = get
        self.set_method = set

    def get_value(self, name, obj, context=None, *args, **kwargs):
        if not self.get_method:
            return MISSING

        method_name = self.get_method(name)
        if not hasattr(obj, method_name):
            raise ValueError('Object does not have method %s' % method_name)
        method = getattr(obj, method_name)
        if not callable(method):
            raise ValueError('Value of %s is not callable' % method_name)
        return make_context_aware(method, 0)(context)

    def set_value(self, name, obj, value, context=None, *args, **kwargs):
        if not self.set_method:
            return MISSING

        method_name = self.set_method(name)
        if not hasattr(obj, method_name):
            raise ValueError('Object does not have method %s' % method_name)
        method = getattr(obj, method_name)
        if not callable(method):
            raise ValueError('Value of %s is not callable' % method_name)
        return make_context_aware(method, 1)(value, context)


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
    :param callable get: Function that takes source object and returns
        field value.
    :param callable set: Function that takes source object and new field value
        and sets that value to object field. Function return value is ignored.
    """
    def __init__(self, field_type, get=None, set=None, *args, **kwargs):
        super(FunctionField, self).__init__(field_type, *args, **kwargs)
        if get is not None and not callable(get):
            raise ValueError("Get function is not callable")
        if set is not None and not callable(set):
            raise ValueError("Set function is not callable")

        if get is not None:
            get = make_context_aware(get, 1)
        if set is not None:
            set = make_context_aware(set, 2)

        self.get_func = get
        self.set_func = set

    def get_value(self, name, obj, context=None, *args, **kwargs):
        if self.get_func is None:
            return MISSING
        return self.get_func(obj, context)

    def set_value(self, name, obj, value, context=None, *args, **kwargs):
        if self.set_func is None:
            return MISSING
        self.set_func(obj, value, context)


def inheritable_property(name):
    cache_attr = '__' + name

    @property
    def getter(self):
        if not hasattr(self, cache_attr):
            value = getattr(self, '_' + name)
            if value is None:
                for base in self.bases:
                    value = getattr(base, name)
                    if value is not None:
                        break
                else:
                    value = None

            setattr(self, cache_attr, value)

        return getattr(self, cache_attr)

    return getter


class Object(Type):
    """An object type. Serializes to a dict of field names to serialized field
    values. Parametrized with field names to types mapping.
    The way values are obtained during serialization is determined by type of
    field object in :attr:`~Object.fields` mapping (see :class:`AttributeField`,
    :class:`MethodField` or :class:`FunctionField` for details). You can specify
    either :class:`Field` object, a :class:`Type` object or any other value.

    In case of :class:`Type`, it will be automatically wrapped with a default
    field type, which is controlled by :attr:`~Object.default_field_type`
    constructor argument.

    In case of any other value it will be transformed into :class:`Constant`.

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

    :param base_or_fields: Either :class:`Object` instance or fields (See
        `fields` argument). In case of fields, the actual fields argument should
        not be specified.
    :param fields: List of name-to-value tuples or mapping of object field names to
        :class:`Type`, :class:`Field` objects or constant values.
    :param callable contructor: Deserialized value constructor. Constructor
        should take all fields values as keyword arguments.
    :param Field default_field_type: Default field type to use for fields defined
        by their type.
    :param bool allow_extra_fields: If False, it will raise
        :exc:`~lollipop.errors.ValidationError` for all extra dict keys during
        deserialization. If True, will ignore all extra fields.
    :param only: Field name or list of field names to include in this object
        from it's base classes. All other base classes' fields won't be used.
        Does not affect own fields.
    :param exclude: Field name or list of field names to exclude from this
        object from base classes. All other base classes' fields will be included.
        Does not affect own fields.
    :param bool ordered: Serialize data into OrderedDict following fields order.
        Fields in this case should be declared with a dictionary which also
        supports ordering or with a list of tuples.
    :param bool immutable: If False, object is allowed to be modified in-place;
        if True - always create a copy with `constructor`.
    :param kwargs: Same keyword arguments as for :class:`Type`.
    """

    default_error_messages = {
        'invalid': 'Value should be dict',
        'unknown': 'Unknown field',
    }

    def __init__(self, bases_or_fields=None, fields=None, constructor=None,
                 default_field_type=None,
                 allow_extra_fields=None, only=None, exclude=None,
                 immutable=None, ordered=None,
                 **kwargs):
        super(Object, self).__init__(**kwargs)

        if bases_or_fields is None and fields is None:
            raise ValueError('No base and/or fields are specified')

        if isinstance(bases_or_fields, Type):
            bases = [bases_or_fields]
        if is_list(bases_or_fields) and \
                all([isinstance(base, Type) for base in bases_or_fields]):
            bases = bases_or_fields
        elif is_list(bases_or_fields) or is_dict(bases_or_fields):
            if fields is None:
                bases = []
                fields = bases_or_fields
            else:
                raise ValueError('Unknown base object type: %r' % bases_or_fields)

        self.bases = bases

        self._default_field_type = default_field_type
        self._constructor = constructor
        self._allow_extra_fields = allow_extra_fields
        self._immutable = immutable
        self._ordered = ordered
        if only is not None and not is_list(only):
            only = [only]
        if exclude is not None and not is_list(exclude):
            exclude = [exclude]
        self._only = only
        self._exclude = exclude
        self._fields = fields

    @property
    def fields(self):
        if not hasattr(self, '_resolved_fields'):
            self._resolved_fields = self._resolve_fields(self.bases, self._fields,
                                                         self._only, self._exclude)
        return self._resolved_fields

    default_field_type = inheritable_property('default_field_type')
    constructor = inheritable_property('constructor')
    allow_extra_fields = inheritable_property('allow_extra_fields')
    immutable = inheritable_property('immutable')
    ordered = inheritable_property('ordered')

    def _normalize_field(self, value):
        if isinstance(value, Field):
            return value
        if not isinstance(value, Type):
            value = Constant(value)
        return (self.default_field_type or AttributeField)(value)

    def _resolve_fields(self, bases, fields, only=None, exclude=None):
        all_fields = []
        if bases is not None:
            for base in bases:
                all_fields += list(iteritems(base.fields))

        if only is not None:
            all_fields = [(name, field)
                          for name, field in all_fields
                          if name in only]

        if exclude is not None:
            all_fields = [(name, field)
                          for name, field in all_fields
                          if name not in exclude]

        if fields is not None:
            all_fields += [
                (name, self._normalize_field(field))
                for name, field in (iteritems(fields) if is_dict(fields) else fields)
            ]

        return OrderedDict(all_fields)

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

        if self.allow_extra_fields is False:
            field_names = [name for name, _ in iteritems(self.fields)]
            for name in data:
                if name not in field_names:
                    errors_builder.add_error(name, self._error_messages['unknown'])

        errors_builder.raise_errors()

        result = super(Object, self).load(result, *args, **kwargs)
        if self.constructor:
            result = self.constructor(**result)
        return result

    def load_into(self, obj, data, inplace=True, *args, **kwargs):
        """Load data and update existing object.

        :param obj: Object to update with deserialized data.
        :param data: Raw data to get value to deserialize from.
        :param bool inplace: If True update data inplace;
            otherwise - create new data.
        :param kwargs: Same keyword arguments as for :meth:`Type.load`.
        :returns: Updated object.
        :raises: :exc:`~lollipop.errors.ValidationError`
        """
        if obj is None:
            raise ValueError('Load target should not be None')

        if data is MISSING:
            return

        if data is None:
            self._fail('required')

        if not is_dict(data):
            self._fail('invalid')

        errors_builder = ValidationErrorBuilder()

        data1 = {}
        for name, field in iteritems(self.fields):
            try:
                if name in data:
                    # Load new data
                    value = field.load_into(obj, name, data,
                                            inplace=not self.immutable and inplace)
                else:
                    # Retrive data from existing object
                    value = field.get_value(name, obj, *args, **kwargs)

                if value is not MISSING:
                    data1[name] = value
            except ValidationError as ve:
                errors_builder.add_error(name, ve.messages)

        if self.allow_extra_fields is False:
            field_names = [name for name, _ in iteritems(self.fields)]
            for name in data:
                if name not in field_names:
                    errors_builder.add_error(name, self._error_messages['unknown'])

        errors_builder.raise_errors()

        data2 = super(Object, self).load(data1, *args, **kwargs)

        if self.immutable or not inplace:
            result = data2
            if self.constructor:
                result = self.constructor(**result)
        else:
            for name, field in iteritems(self.fields):
                if name not in data:
                    continue

                try:
                    field.set_value(name, obj, data2.get(name, MISSING))
                except ValidationError as ve:
                    raise ValidationError({name: ve.messages})

            result = obj

        return result

    def validate_for(self, obj, data, *args, **kwargs):
        """Takes target object and serialized data, tries to update that object
        with data and validate result. Returns validation errors or None.
        Object is not updated.

        :param obj: Object to check data validity against. In case the data is
            partial object is used to get the rest of data from.
        :param data: Data to validate. Can be partial (not all schema field data
            is present).
        :param kwargs: Same keyword arguments as for :meth:`Type.load`.
        :returns: validation errors or None
        """
        try:
            self.load_into(obj, data, inplace=False, *args, **kwargs)
            return None
        except ValidationError as ve:
            return ve.messages

    def dump(self, obj, *args, **kwargs):
        if obj is MISSING or obj is None:
            self._fail('required')

        errors_builder = ValidationErrorBuilder()
        result = OrderedDict() if self.ordered else {}

        for name, field in iteritems(self.fields):
            try:
                dumped = field.dump(name, obj, *args, **kwargs)
                if dumped != MISSING:
                    result[name] = dumped
            except ValidationError as ve:
                errors_builder.add_error(name, ve.messages)
        errors_builder.raise_errors()

        return super(Object, self).dump(result, *args, **kwargs)

    def __repr__(self):
        return '<{klass}{fields}>'.format(
            klass=self.__class__.__name__,
            fields=''.join([' %s=%s' % (name, field_type.field_type)
                            for name, field_type in self.fields.iteritems()]),
        )


class Modifier(Type):
    """Base class for modifiers - a wrapper for types that modify
    how those types work. Also, it tries to be as transparent as possible
    in regard to inner type, so it proxies all unknown attributes to inner type.

    :param Type inner_type: Actual type that should be optional.
    """
    def __init__(self, inner_type, **kwargs):
        super(Modifier, self).__init__(
            **dict({'name': inner_type.name,
                    'description': inner_type.description},
                   **kwargs)
        )
        self.inner_type = inner_type

    def __hasattr__(self, name):
        return hasattr(self.inner_type, name)

    def __getattr__(self, name):
        return getattr(self.inner_type, name)

    def __repr__(self):
        return '<{klass} {inner_type}>'.format(
            klass=self.__class__.__name__,
            inner_type=repr(self.inner_type),
        )


class Optional(Modifier):
    """A modifier which makes values optional: if value is missing or None,
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
    :param load_default: Value or callable. If value - it will be used when value
        is missing on deserialization. If callable - it will be called with no
        arguments to get value to use when value is missing on deserialization.
    :param dump_default: Value or callable. If value - it will be used when value
        is missing on serialization. If callable - it will be called with no
        arguments to get value to use when value is missing on serialization.
    :param kwargs: Same keyword arguments as for :class:`Type`.
    """
    def __init__(self, inner_type,
                 load_default=None, dump_default=None,
                 **kwargs):
        super(Optional, self).__init__(inner_type, **kwargs)
        if not callable(load_default):
            load_default = constant(load_default)
        if not callable(dump_default):
            dump_default = constant(dump_default)
        self.load_default = make_context_aware(load_default, 0)
        self.dump_default = make_context_aware(dump_default, 0)

    def load(self, data, context=None, *args, **kwargs):
        if data is MISSING or data is None:
            return self.load_default(context)
        return super(Optional, self).load(
            self.inner_type.load(data, context=context, *args, **kwargs),
            *args, **kwargs
        )

    def dump(self, data, context=None, *args, **kwargs):
        if data is MISSING or data is None:
            return self.dump_default(context)
        return super(Optional, self).dump(
            self.inner_type.dump(data, context=context, *args, **kwargs),
            *args, **kwargs
        )

    def __repr__(self):
        return '<{klass} {inner_type}>'.format(
            klass=self.__class__.__name__,
            inner_type=repr(self.inner_type),
        )


class LoadOnly(Modifier):
    """A wrapper type which proxies loading to inner type but always returns
    :obj:`MISSING` on dump.

    Example: ::

        UserType = Object({
            'name': String(),
            'password': LoadOnly(String()),
        })

    :param Type inner_type: Data type.
    """
    def load(self, data, *args, **kwargs):
        return self.inner_type.load(data, *args, **kwargs)

    def dump(self, data, *args, **kwargs):
        return MISSING


class DumpOnly(Modifier):
    """A wrapper type which proxies dumping to inner type but always returns
    :obj:`MISSING` on load.

    Example: ::

        UserType = Object({
            'name': String(),
            'created_at': DumpOnly(DateTime()),
        })

    :param Type inner_type: Data type.
    """
    def load(self, data, *args, **kwargs):
        return MISSING

    def dump(self, data, *args, **kwargs):
        return self.inner_type.dump(data, *args, **kwargs)


class Transform(Modifier):
    """A wrapper type which allows us to convert data structures to an inner type,
    then loaded or dumped with a customized format.

    Example: ::

        Point = namedtuple('Point', ['x', 'y'])

        PointType = Transform(
            Tuple(Integer(), Integer()),
            post_load=lambda values: Point(values[0], values[1]),
            pre_dump=lambda point: [point.x, point.y],
        )

        PointType.dump((Point(x=1, y=2)))
        # => [1,2]

        PointType.load([1,2])
        # => Point(x=1, y=2)

    :param Type inner_type: Data type.
    :param pre_load: Modify data before it is passed to inner_type load. Argument
        should be a callable taking one argument - data - and returning updated data.
        Optionally it can take a second argument - context.
    :param post_load: Modify data after it is returned from inner_type load.
        Argument should be a callable taking one argument - data - and returning
        updated data. Optionally it can take a second argument - context.
    :param pre_dump: Modify value before it passed to inner_type dump. Argument
        should be a callable taking one argument - value - and returning updated value.
        Optionally it can take a second argument - context.
    :param post_dump: Modify value after it is returned from inner_type dump.
        Argument should be a callable taking one argument - value - and returning
        updated value. Optionally it can take a second argument - context.
    """
    def __init__(self, inner_type,
                 pre_load=identity, post_load=identity,
                 pre_dump=identity, post_dump=identity):
        super(Transform, self).__init__(inner_type)
        self.pre_load = make_context_aware(pre_load, 1)
        self.post_load = make_context_aware(post_load, 1)
        self.pre_dump = make_context_aware(pre_dump, 1)
        self.post_dump = make_context_aware(post_dump, 1)

    def load(self, data, context=None):
        return self.post_load(
            self.inner_type.load(
                self.pre_load(data, context),
                context,
            ),
            context,
        )

    def dump(self, value, context=None):
        return self.post_dump(
            self.inner_type.dump(
                self.pre_dump(value, context),
                context,
            ),
            context,
        )


def validated_type(base_type, name=None, validate=None):
    """Convenient way to create a new type by adding validation to existing type.

    Example: ::

        Ipv4Address = validated_type(
            String, 'Ipv4Address',
            # regexp simplified for demo purposes
            Regexp('^\d+\.\d+\.\d+\.\d+$', error='Invalid IP address')
        )

        Percentage = validated_type(Integer, validate=Range(0, 100))

        # The above is the same as

        class Ipv4Address(String):
            def __init__(self, *args, **kwargs):
                super(Ipv4Address, self).__init__(*args, **kwargs)
                self._validators.insert(0, Regexp('^\d+\.\d+\.\d+\.\d+$', error='Invalid IP address'))

        class Percentage(Integer):
            def __init__(self, *args, **kwargs):
                super(Percentage, self).__init__(*args, **kwargs)
                self._validators.insert(0, Range(0, 100))

    :param Type base_type: Base type for a new type.
    :param name str: Optional class name for new type
        (will be shown in places like repr).
    :param validate: A validator or list of validators for this data type.
        See `Type.validate` for details.
    """
    if validate is None:
        validate = []
    if not is_list(validate):
        validate = [validate]

    class ValidatedSubtype(base_type):
        if name is not None:
            __name__ = name

        def __init__(self, *args, **kwargs):
            super(ValidatedSubtype, self).__init__(*args, **kwargs)
            for validator in reversed(validate):
                self._validators.insert(0, validator)

    return ValidatedSubtype
