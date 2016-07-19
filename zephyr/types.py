from zephyr.utils import merge_errors


MISSING = object()

MISSING_ERROR_MESSAGE = 'Error message "{key}" in class {class_name} does not exist'


class ValidationError(Exception):
    def __init__(self, messages):
        super(ValidationError, self).__init__('Invalid data')
        # TODO: normalize messages
        self.messages = messages


class ValidationErrorBuilder(object):
    def __init__(self):
        super(ValidationErrorBuilder, self).__init__()
        self.errors = {}

    def add(self, messages):
        self.errors = merge_errors(self.errors, messages)

    def raise_errors(self):
        if self.errors:
            raise ValidationError(self.errors)


class Type(object):
    default_error_messages = {
        'invalid_type': 'Value should be {expected}'
    }

    def __init__(self, validate=None, error_messages=None):
        super(Type, self).__init__()
        if validate is None:
            validate = []
        elif callable(validate):
            validate = [validate]

        self._validators = validate
        self._error_messages = error_messages or self.default_error_messages

    def validate(self, data):
        try:
            self.load(data)
            return {}
        except ValidationError as ve:
            return ve.messages

    def load(self, data):
        errors_builder = ValidationErrorBuilder()
        for validator in self._validators:
            try:
                validator(data)
            except ValidationError as ve:
                errors_builder.add(ve.messages)
        errors_builder.raise_errors()
        return data

    def dump(self, value):
        return value

    def _fail(self, key, **kwargs):
        if key not in self._error_messages:
            msg = MISSING_ERROR_MESSAGE.format(
                class_name=self.__class__.__name__,
                key=key
            )
            raise ValueError(msg)

        msg = self._error_messages[key]
        if isinstance(msg, str):
            msg = msg.format(**kwargs)

        raise ValidationError(msg)



class Any(Type):
    pass


class Integer(Type):
    def load(self, data):
        if not isinstance(data, int):
            self._fail('invalid_type', expected='integer')
        return super(Integer, self).load(data)

    def dump(self, value):
        if not isinstance(data, int):
            self._fail('invalid_type', expected='integer')
        return super(Integer, self).dump(value)


class String(Type):
    def load(self, data):
        if not isinstance(data, str) and not isinstance(data, unicode):
            self._fail('invalid_type', expected='string')
        return super(String, self).load(data)

    def dump(self, value):
        if not isinstance(value, str) and not isinstance(value, unicode):
            self._fail('invalid_type', expected='string')
        return super(String, self).dump(str(value))


class Boolean(Type):
    def load(self, data):
        if not isinstance(data, bool):
            self._fail('invalid_type', expected='boolean')
        return super(Boolean, self).load(data)

    def dump(self, value):
        if not isinstance(data, bool):
            self._fail('invalid_type', expected='boolean')
        return super(Boolean, self).dump(bool(value))


class List(Type):
    def __init__(self, item_type, **kwargs):
        super(List, self).__init__(**kwargs)
        self.item_type = item_type

    def load(self, data):
        # TODO: Make more intelligent check for collections
        if not isinstance(data, list):
            self._fail('invalid_type', expected='list')

        errors_builder = ValidationErrorBuilder()
        items = []
        for idx, item in enumerate(data):
            try:
                items.append(self.item_type.load(item))
            except ValidationError as ve:
                errors_builder.add({idx: ve.messages})
        errors_builder.raise_errors()

        return super(List, self).load(items)

    def dump(self, items):
        if not isinstance(data, list):
            self._fail('invalid_type', expected='list')

        errors_builder = ValidationErrorBuilder()
        items = []
        for idx, item in enumerate(data):
            try:
                items.append(self.item_type.dump(item))
            except ValidationError as ve:
                errors_builder.add({idx: ve.messages})
        errors_builder.raise_errors()

        return super(List, self).dump(items)


class Tuple(Type):
    def __init__(self, item_types, **kwargs):
        super(Tuple, self).__init__(**kwargs)
        self.item_types = item_types

    def load(self, data):
        if not isinstance(data, list):
            self._fail('invalid_type', expected='list')

        if len(data) != len(self.item_types):
            raise ValidationError('List length should be %d' % len(self.item_types))

        errors_builder = ValidationErrorBuilder()
        result = []
        for idx, (item_type, item) in enumerate(zip(self.item_types, data)):
            try:
                result.add(item_type.load(item))
            except ValidationError as ve:
                errors_builder.add({idx: ve.messages})
        errors_builder.raise_errors()

        return super(Tuple, self).load(result)

    def dump(self, value):
        if not isinstance(value, list):
            self._fail('invalid_type', expected='list')

        if len(value) != len(self.item_types):
            raise ValidationError('Tuple length should be %d' % len(self.item_types))

        errors_builder = ValidationErrorBuilder()
        result = []
        for idx, (item_type, item) in enumerate(zip(self.item_types, value)):
            try:
                result.add(item_type.dump(item))
            except ValidationError as ve:
                errors_builder.add({idx: ve.messages})
        errors_builder.raise_errors()

        return super(Tuple, self).dump(result)


class Dict(Type):
    def __init__(self, value_type=Any(), **kwargs):
        super(Dict, self).__init__(**kwargs)
        self.value_type = value_type

    def load(self, data):
        if not isinstance(data, dict):
            self._fail('invalid_type', expected='dict')

        result = {}
        for k, v in data.iteritems():
            if not k in self.fields:
                continue
            try:
                result[k] = self.value_type.load(v)
            except ValidationError as ve:
                errors_builder.add({k: ve.messages})
        errors_builder.raise_errors()

        return super(Object, self).load(result)

    def dump(self, value):
        if not isinstance(value, dict):
            self._fail('invalid_type', expected='dict')

        result = {}
        for k, v in value.iteritems():
            if not k in self.fields:
                continue
            try:
                result[k] = self.value_type.dump(v)
            except ValidationError as ve:
                errors_builder.add({k: ve.messages})
        errors_builder.raise_errors()

        return super(Object, self).dump(result)


class Field(object):
    def __init__(self, field_type,
                 required=False,
                 missing=MISSING,
                 default=MISSING,
                 no_load=False, no_dump=False,
                 attribute=None):
        super(Field, self).__init__()
        self.field_type = field_type
        self.required = required
        self.missing = missing
        self.default = default
        self.no_load = no_load
        self.no_dump = no_dump
        self.attribute = attribute

    def load(self, name, data):
        value = data.get(name, self.missing)
        if value is MISSING or value is None:
            if self.required:
                raise ValidationError('Value is required')
            return value

        return self.field_type.load(value)

    def dump(self, name, obj):
        if self.attribute is not None:
            name = self.attribute

        value = getattr(obj, name, self.default)
        if value is MISSING or value is None:
            if self.required:
                raise ValidationError('Value is required')
            return value

        return self.field_type.dump(value)


class Object(Type):
    constructor = dict

    def __init__(self, fields, **kwargs):
        super(Object, self).__init__(**kwargs)
        self.fields = {}
        for name, field in fields.iteritems():
            self.fields[name] = field if isinstance(field, Field) else Field(field)

    def load(self, data):
        if not isinstance(data, dict):
            raise ValidationError('Value should be dict')

        errors_builder = ValidationErrorBuilder()
        result = {}
        for name, field in self.fields.iteritems():
            if field.no_load:
                continue

            try:
                result[name] = field.load(name, data)
            except ValidationError as ve:
                errors_builder.add({name: ve.messages})
        errors_builder.raise_errors()

        return self.constructor(super(Object, self).load(result))

    def dump(self, obj):
        errors_builder = ValidationErrorBuilder()
        result = {}
        for name, field in self.fields.iteritems():
            if field.no_dump:
                continue

            try:
                result[name] = field.dump(name, obj)
            except ValidationError as ve:
                errors_builder.add({k: ve.messages})
        errors_builder.raise_errors()

        return super(Object, self).dump(result)
