import pytest
from functools import partial
import datetime
from lollipop.compat import OrderedDict
from lollipop.types import MISSING, ValidationError, Type, Any, String, \
    Number, Integer, Float, Boolean, DateTime, Date, Time, OneOf, List, Tuple, \
    Dict, Field, AttributeField, MethodField, FunctionField, Constant, Object, \
    Optional, LoadOnly, DumpOnly, Transform, type_name_hint, dict_value_hint, \
    validated_type
from lollipop.errors import merge_errors
from lollipop.validators import Validator, Predicate
from lollipop.utils import to_camel_case
from collections import namedtuple
import uuid


def validator(predicate, message='Something went wrong'):
    return Predicate(predicate, message)


def constant_succeed_validator():
    """Returns validator that always succeeds"""
    return validator(lambda _: True)


def constant_fail_validator(message):
    """Returns validator that always fails with given message"""
    return validator(lambda _: False, message)


def is_odd_validator():
    """Returns validator that checks if integer is odd"""
    return validator(lambda x: x % 2 == 1, is_odd_validator.message)
is_odd_validator.message = 'Value should be odd'


def divisible_by_validator(n):
    """Returns validator that checks if integer is divisible by given `n`"""
    return Predicate(lambda x: x % n == 0, 'Value should be divisible by %d' % n)

def random_string():
    return str(uuid.uuid4())


class SpyValidator(Validator):
    def __init__(self):
        super(SpyValidator, self).__init__()
        self.validated = None
        self.context = None

    def __call__(self, value, context=None):
        self.validated = value
        self.context = context


class SpyType(Type):
    def __init__(self, load_result=None, dump_result=None):
        super(SpyType, self).__init__()
        self.loaded = None
        self.load_called = False
        self.load_context = None
        self.load_result = load_result
        self.dumped = None
        self.dump_called = False
        self.dump_context = None
        self.dump_result = dump_result

    def load(self, data, context=None, *args, **kwargs):
        self.loaded = data
        self.load_called = True
        self.load_context = context
        return self.load_result or data

    def dump(self, value, context=None, *args, **kwargs):
        self.dumped = value
        self.dump_called = True
        self.dump_context = context
        return self.dump_result or value


class SpyTypeWithLoadInto(SpyType):
    def __init__(self, load_into_result=None, *args, **kwargs):
        super(SpyTypeWithLoadInto, self).__init__(*args, **kwargs)
        self.loaded_into = None
        self.load_into_called = False
        self.load_into_context = None
        self.load_into_result = load_into_result

    def load_into(self, obj, data, context=None, *args, **kwargs):
        self.loaded_into = (obj, data)
        self.load_into_called = True
        self.load_into_context = context
        return self.load_into_result or data


class NameDescriptionTestsMixin(object):
    """Mixin that adds tests for adding name and description for type.
    Host class should define `tested_type` properties.
    """
    def test_name(self):
        assert self.tested_type(name='foo').name == 'foo'

    def test_description(self):
        assert self.tested_type(description='Just a description').description \
            == 'Just a description'


class RequiredTestsMixin:
    """Mixin that adds tests for reacting to missing/None values during load/dump.
    Host class should define `tested_type` property.
    """
    def test_loading_missing_value_raises_required_error(self):
        with pytest.raises(ValidationError) as exc_info:
            self.tested_type().load(MISSING)
        assert exc_info.value.messages == Type.default_error_messages['required']

    def test_loading_None_raises_required_error(self):
        with pytest.raises(ValidationError) as exc_info:
            self.tested_type().load(None)
        assert exc_info.value.messages == Type.default_error_messages['required']

    def test_dumping_missing_value_raises_required_error(self):
        with pytest.raises(ValidationError) as exc_info:
            self.tested_type().dump(MISSING)
        assert exc_info.value.messages == Type.default_error_messages['required']

    def test_dumping_None_raises_required_error(self):
        with pytest.raises(ValidationError) as exc_info:
            self.tested_type().dump(None)
        assert exc_info.value.messages == Type.default_error_messages['required']


class ValidationTestsMixin:
    """Mixin that adds tests for reacting to validators.
    Host class should define `tested_type` and `valid_value` properties.
    """
    def test_loading_does_not_raise_ValidationError_if_validators_succeed(self):
        assert self.tested_type(
            validate=[constant_succeed_validator(),
                      constant_succeed_validator()],
        ).load(self.valid_data) == self.valid_value

    def test_loading_raises_ValidationError_if_validator_fails(self):
        message1 = 'Something went wrong'
        with pytest.raises(ValidationError) as exc_info:
            self.tested_type(validate=constant_fail_validator(message1))\
                .load(self.valid_data)
        assert exc_info.value.messages == message1

    def test_loading_raises_ValidationError_with_combined_messages_if_multiple_validators_fail(self):
        message1 = 'Something went wrong 1'
        message2 = 'Something went wrong 2'
        with pytest.raises(ValidationError) as exc_info:
            self.tested_type(validate=[constant_fail_validator(message1),
                                       constant_fail_validator(message2)])\
                .load(self.valid_data)
        assert exc_info.value.messages == [message1, message2]

    def test_loading_passes_context_to_validator(self):
        context = object()
        validator = SpyValidator()
        self.tested_type(validate=validator).load(self.valid_data, context)
        assert validator.context == context

    def test_validation_returns_None_if_validators_succeed(self):
        assert self.tested_type(
            validate=[constant_succeed_validator(),
                      constant_succeed_validator()],
        ).validate(self.valid_data) is None

    def test_validation_returns_errors_if_validator_fails(self):
        message1 = 'Something went wrong'
        assert self.tested_type(validate=constant_fail_validator(message1))\
            .validate(self.valid_data) == message1

    def test_validation_returns_combined_errors_if_multiple_validators_fail(self):
        message1 = 'Something went wrong 1'
        message2 = 'Something went wrong 2'
        assert self.tested_type(validate=[constant_fail_validator(message1),
                                          constant_fail_validator(message2)])\
            .validate(self.valid_data) == [message1, message2]


class TestString(NameDescriptionTestsMixin, RequiredTestsMixin, ValidationTestsMixin):
    tested_type = String
    valid_data = 'foo'
    valid_value = 'foo'

    def test_loading_string_value(self):
        assert String().load('foo') == 'foo'

    def test_loading_non_string_value_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            String().load(123)
        assert exc_info.value.messages == String.default_error_messages['invalid']

    def test_dumping_string_value(self):
        assert String().dump('foo') == 'foo'

    def test_dumping_non_string_value_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            String().dump(123)
        assert exc_info.value.messages == String.default_error_messages['invalid']


class TestNumber(NameDescriptionTestsMixin, RequiredTestsMixin, ValidationTestsMixin):
    tested_type = Number
    valid_data = 1.23
    valid_value = 1.23

    def test_loading_float_value(self):
        assert Number().load(1.23) == 1.23

    def test_loading_non_numeric_value_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Number().load("abc")
        assert exc_info.value.messages == Number.default_error_messages['invalid']

    def test_dumping_float_value(self):
        assert Number().dump(1.23) == 1.23

    def test_dumping_non_numeric_value_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Number().dump("abc")
        assert exc_info.value.messages == Number.default_error_messages['invalid']


class TestInteger:
    def test_loading_integer_value(self):
        assert Integer().load(123) == 123

    def test_loading_long_value(self):
        value = 10000000000000000000000000000000000000
        assert Integer().load(value) == value

    def test_loading_non_numeric_value_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Integer().load("abc")
        assert exc_info.value.messages == Integer.default_error_messages['invalid']

    def test_dumping_integer_value(self):
        assert Integer().dump(123) == 123

    def test_dumping_long_value(self):
        value = 10000000000000000000000000000000000000
        assert Integer().dump(value) == value

    def test_dumping_non_numeric_value_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Integer().dump("abc")
        assert exc_info.value.messages == Integer.default_error_messages['invalid']


class TestFloat:
    def test_loading_float_value(self):
        assert Float().load(1.23) == 1.23

    def test_loading_non_numeric_value_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Float().load("abc")
        assert exc_info.value.messages == Float.default_error_messages['invalid']

    def test_dumping_float_value(self):
        assert Float().dump(1.23) == 1.23

    def test_dumping_non_numeric_value_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Float().dump("abc")
        assert exc_info.value.messages == Float.default_error_messages['invalid']


class TestBoolean(NameDescriptionTestsMixin, RequiredTestsMixin, ValidationTestsMixin):
    tested_type = Boolean
    valid_data = True
    valid_value = True

    def test_loading_boolean_value(self):
        assert Boolean().load(True) == True
        assert Boolean().load(False) == False

    def test_loading_non_boolean_value_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Boolean().load("123")
        assert exc_info.value.messages == Boolean.default_error_messages['invalid']

    def test_dumping_boolean_value(self):
        assert Boolean().dump(True) == True
        assert Boolean().dump(False) == False

    def test_dumping_non_boolean_value_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Boolean().dump("123")
        assert exc_info.value.messages == Boolean.default_error_messages['invalid']


class TestDateTime(NameDescriptionTestsMixin, RequiredTestsMixin, ValidationTestsMixin):
    tested_type = DateTime
    valid_data = '2016-07-28T11:22:33UTC'
    valid_value = datetime.datetime(2016, 7, 28, 11, 22, 33)

    def test_loading_string_date(self):
        assert DateTime().load('2011-12-13T11:22:33UTC') == \
            datetime.datetime(2011, 12, 13, 11, 22, 33)

    def test_loading_using_predefined_format(self):
        assert DateTime(format='rfc822').load('13 Dec 11 11:22:33 UTC') == \
            datetime.datetime(2011, 12, 13, 11, 22, 33)

    def test_loading_using_custom_format(self):
        assert DateTime(format='%m/%d/%Y %H:%M:%S').load('12/13/2011 11:22:33') == \
            datetime.datetime(2011, 12, 13, 11, 22, 33)

    def test_loading_raises_ValidationError_if_value_is_not_string(self):
        with pytest.raises(ValidationError) as exc_info:
            DateTime().load(123)
        assert exc_info.value.messages == \
            DateTime.default_error_messages['invalid_type']

    def test_customizing_error_message_if_value_is_not_string(self):
        with pytest.raises(ValidationError) as exc_info:
            DateTime(error_messages={
                'invalid_type': 'Data {data} should be string',
            }).load(123)
        assert exc_info.value.messages == 'Data 123 should be string'

    def test_loading_raises_ValidationError_if_value_string_does_not_match_date_format(self):
        with pytest.raises(ValidationError) as exc_info:
            DateTime().load('12/13/2011 11:22:33')
        assert exc_info.value.messages == \
            DateTime.default_error_messages['invalid_format']

    def test_customizing_error_message_if_value_string_does_not_match_date_format(self):
        with pytest.raises(ValidationError) as exc_info:
            DateTime(format='%Y-%m-%d %H:%M', error_messages={
                'invalid_format': 'Data {data} does not match format {format}',
            }).load('12/13/2011')
        assert exc_info.value.messages == \
            'Data 12/13/2011 does not match format %Y-%m-%d %H:%M'

    def test_loading_passes_deserialized_date_to_validator(self):
        validator = SpyValidator()
        DateTime(validate=validator).load('2011-12-13T11:22:33GMT')
        assert validator.validated == datetime.datetime(2011, 12, 13, 11, 22, 33)

    def test_dumping_date(self):
        assert DateTime().dump(datetime.datetime(2011, 12, 13, 11, 22, 33)) == \
            '2011-12-13T11:22:33'

    def test_dumping_using_predefined_format(self):
        assert DateTime(format='rfc822')\
            .dump(datetime.datetime(2011, 12, 13, 11, 22, 33)) == \
            '13 Dec 11 11:22:33 '

    def test_dumping_using_custom_format(self):
        assert DateTime(format='%m/%d/%Y %H:%M:%S')\
            .dump(datetime.datetime(2011, 12, 13, 11, 22, 33)) == \
            '12/13/2011 11:22:33'

    def test_dumping_raises_ValidationError_if_value_is_not_string(self):
        with pytest.raises(ValidationError) as exc_info:
            DateTime().dump(123)
        assert exc_info.value.messages == DateTime.default_error_messages['invalid']

    def test_customizing_error_message_if_value_is_not_string(self):
        with pytest.raises(ValidationError) as exc_info:
            DateTime(error_messages={
                'invalid': 'Data {data} should be string',
            }).dump(123)
        assert exc_info.value.messages == 'Data 123 should be string'


class TestDate(NameDescriptionTestsMixin, RequiredTestsMixin, ValidationTestsMixin):
    tested_type = Date
    valid_data = '2016-07-28'
    valid_value = datetime.date(2016, 7, 28)

    def test_loading_string_date(self):
        assert Date().load('2011-12-13') == datetime.date(2011, 12, 13)

    def test_loading_using_predefined_format(self):
        assert Date(format='rfc822').load('13 Dec 11') == datetime.date(2011, 12, 13)

    def test_loading_using_custom_format(self):
        assert Date(format='%m/%d/%Y').load('12/13/2011') == \
            datetime.date(2011, 12, 13)

    def test_loading_raises_ValidationError_if_value_is_not_string(self):
        with pytest.raises(ValidationError) as exc_info:
            Date().load(123)
        assert exc_info.value.messages == Date.default_error_messages['invalid_type']

    def test_customizing_error_message_if_value_is_not_string(self):
        with pytest.raises(ValidationError) as exc_info:
            Date(error_messages={
                'invalid_type': 'Data {data} should be string',
            }).load(123)
        assert exc_info.value.messages == 'Data 123 should be string'

    def test_loading_raises_ValidationError_if_value_string_does_not_match_date_format(self):
        with pytest.raises(ValidationError) as exc_info:
            Date().load('12/13/2011')
        assert exc_info.value.messages == Date.default_error_messages['invalid_format']

    def test_customizing_error_message_if_value_string_does_not_match_date_format(self):
        with pytest.raises(ValidationError) as exc_info:
            Date(format='%Y-%m-%d', error_messages={
                'invalid_format': 'Data {data} does not match format {format}',
            }).load('12/13/2011')
        assert exc_info.value.messages == \
            'Data 12/13/2011 does not match format %Y-%m-%d'

    def test_loading_passes_deserialized_date_to_validator(self):
        validator = SpyValidator()
        Date(validate=validator).load('2011-12-13')
        assert validator.validated == datetime.date(2011, 12, 13)

    def test_dumping_date(self):
        assert Date().dump(datetime.date(2011, 12, 13)) == '2011-12-13'

    def test_dumping_using_predefined_format(self):
        assert Date(format='rfc822').dump(datetime.date(2011, 12, 13)) == '13 Dec 11'

    def test_dumping_using_custom_format(self):
        assert Date(format='%m/%d/%Y').dump(datetime.date(2011, 12, 13)) == \
            '12/13/2011'

    def test_dumping_raises_ValidationError_if_value_is_not_string(self):
        with pytest.raises(ValidationError) as exc_info:
            Date().dump(123)
        assert exc_info.value.messages == Date.default_error_messages['invalid']

    def test_customizing_error_message_if_value_is_not_string(self):
        with pytest.raises(ValidationError) as exc_info:
            Date(error_messages={
                'invalid': 'Data {data} should be string',
            }).dump(123)
        assert exc_info.value.messages == 'Data 123 should be string'


class TestTime(NameDescriptionTestsMixin, RequiredTestsMixin, ValidationTestsMixin):
    tested_type = Time
    valid_data = '11:22:33'
    valid_value = datetime.time(11, 22, 33)

    def test_loading_string_date(self):
        assert Time().load('11:22:33') == datetime.time(11, 22, 33)

    def test_loading_using_custom_format(self):
        assert Time(format='%H %M %S').load('11 22 33') == \
            datetime.time(11, 22, 33)

    def test_loading_raises_ValidationError_if_value_is_not_string(self):
        with pytest.raises(ValidationError) as exc_info:
            Time().load(123)
        assert exc_info.value.messages == Time.default_error_messages['invalid_type']

    def test_customizing_error_message_if_value_is_not_string(self):
        with pytest.raises(ValidationError) as exc_info:
            Time(error_messages={
                'invalid_type': 'Data {data} should be string',
            }).load(123)
        assert exc_info.value.messages == 'Data 123 should be string'

    def test_loading_raises_ValidationError_if_value_string_does_not_match_date_format(self):
        with pytest.raises(ValidationError) as exc_info:
            Time().load('12/13/2011')
        assert exc_info.value.messages == Time.default_error_messages['invalid_format']

    def test_customizing_error_message_if_value_string_does_not_match_date_format(self):
        with pytest.raises(ValidationError) as exc_info:
            Time(format='%H:%M:%S', error_messages={
                'invalid_format': 'Data {data} does not match format {format}',
            }).load('11 22 33')
        assert exc_info.value.messages == \
            'Data 11 22 33 does not match format %H:%M:%S'

    def test_loading_passes_deserialized_date_to_validator(self):
        validator = SpyValidator()
        Time(validate=validator).load('11:22:33')
        assert validator.validated == datetime.time(11, 22, 33)

    def test_dumping_date(self):
        assert Time().dump(datetime.time(11, 22, 33)) == '11:22:33'

    def test_dumping_using_custom_format(self):
        assert Time(format='%H %M %S').dump(datetime.time(11, 22, 33)) == \
            '11 22 33'

    def test_dumping_raises_ValidationError_if_value_is_not_string(self):
        with pytest.raises(ValidationError) as exc_info:
            Time().dump(123)
        assert exc_info.value.messages == Time.default_error_messages['invalid']

    def test_customizing_error_message_if_value_is_not_string(self):
        with pytest.raises(ValidationError) as exc_info:
            Time(error_messages={
                'invalid': 'Data {data} should be string',
            }).dump(123)
        assert exc_info.value.messages == 'Data 123 should be string'


class TestList(NameDescriptionTestsMixin, RequiredTestsMixin, ValidationTestsMixin):
    tested_type = partial(List, String())
    valid_data = ['foo', 'bar']
    valid_value = ['foo', 'bar']

    def test_loading_list_value(self):
        assert List(String()).load(['foo', 'bar', 'baz']) == ['foo', 'bar', 'baz']

    def test_loading_non_list_value_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            List(String()).load('1, 2, 3')
        assert exc_info.value.messages == List.default_error_messages['invalid']

    def test_loading_list_value_with_items_of_incorrect_type_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            List(String()).load([1, '2', 3])
        message = String.default_error_messages['invalid']
        assert exc_info.value.messages == {0: message, 2: message}

    def test_loading_list_value_with_items_that_have_validation_errors_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            List(Integer(validate=is_odd_validator())).load([1, 2, 3])
        assert exc_info.value.messages == {1: is_odd_validator.message}

    def test_loading_does_not_validate_whole_list_if_items_have_errors(self):
        message1 = 'Something went wrong'
        def validate(value):
            validate.called += 1
        validate.called = 0
        with pytest.raises(ValidationError) as exc_info:
            List(Integer(validate=is_odd_validator()),
                 validate=[constant_fail_validator(message1)]).load([1, 2, 3])
        assert validate.called == 0

    def test_loading_passes_context_to_inner_type_load(self):
        inner_type = SpyType()
        context = object()
        List(inner_type).load(['foo'], context)
        assert inner_type.load_context == context

    def test_dumping_list_value(self):
        assert List(String()).dump(['foo', 'bar', 'baz']) == ['foo', 'bar', 'baz']

    def test_dumping_non_list_value_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            List(String()).dump('1, 2, 3')
        assert exc_info.value.messages == List.default_error_messages['invalid']

    def test_dumping_list_value_with_items_of_incorrect_type_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            List(String()).dump([1, '2', 3])
        message = String.default_error_messages['invalid']
        assert exc_info.value.messages == {0: message, 2: message}

    def test_dumping_passes_context_to_inner_type_dump(self):
        inner_type = SpyType()
        context = object()
        List(inner_type).dump(['foo'], context)
        assert inner_type.dump_context == context


class TestTuple(NameDescriptionTestsMixin, RequiredTestsMixin, ValidationTestsMixin):
    tested_type = partial(Tuple, [Integer(), Integer()])
    valid_data = [123, 456]
    valid_value = [123, 456]

    def test_loading_tuple_with_values_of_same_type(self):
        assert Tuple([Integer(), Integer()]).load([123, 456]) == \
            [123, 456]

    def test_loading_tuple_with_values_of_different_type(self):
        assert Tuple([String(), Integer(), Boolean()]).load(['foo', 123, False]) == \
            ['foo', 123, False]

    def test_loading_non_tuple_value_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Tuple([Integer(), Integer()]).load({'foo': 'foo', 'bar': 'bar'})
        assert exc_info.value.messages == Tuple.default_error_messages['invalid']

    def test_loading_tuple_with_items_of_incorrect_type_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Tuple([Integer(), Integer()]).load(['foo', 'bar'])
        message = Integer.default_error_messages['invalid']
        assert exc_info.value.messages == {0: message, 1: message}

    def test_loading_tuple_with_items_that_have_validation_errors_raises_ValidationErrors(self):
        with pytest.raises(ValidationError) as exc_info:
            Tuple([Integer(validate=is_odd_validator()), Integer()]).load([2, 1])
        assert exc_info.value.messages == {0: is_odd_validator.message}

    def test_loading_passes_context_to_inner_type_load(self):
        inner_type = SpyType()
        context = object()
        Tuple([inner_type, inner_type]).load(['foo', 'foo'], context)
        assert inner_type.load_context == context

    def test_dump_tuple(self):
        assert Tuple([Integer(), Integer()]).dump([123, 456]) == [123, 456]

    def test_dumping_non_tuple_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Tuple(String()).dump('foo')
        assert exc_info.value.messages == Tuple.default_error_messages['invalid']

    def test_dumping_tuple_with_items_of_incorrect_type_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Tuple([String(), String()]).dump([123, 456])
        message = String.default_error_messages['invalid']
        assert exc_info.value.messages == {0: message, 1: message}

    def test_dumping_tuple_passes_context_to_inner_type_dump(self):
        inner_type = SpyType()
        context = object()
        Tuple([inner_type, inner_type]).dump(['foo','foo'], context)
        assert inner_type.dump_context == context


class TestDict(NameDescriptionTestsMixin, RequiredTestsMixin, ValidationTestsMixin):
    tested_type = partial(Dict, Integer())
    valid_data = {'foo': 123, 'bar': 456}
    valid_value = {'foo': 123, 'bar': 456}

    def test_loading_dict_with_custom_key_type(self):
        assert Dict(Any(), key_type=Integer())\
            .load({'123': 'foo', '456': 'bar'}) == {123: 'foo', 456: 'bar'}

    def test_loading_accepts_any_key_if_key_type_is_not_specified(self):
        assert Dict(Any())\
            .load({'123': 'foo', 456: 'bar'}) == {'123': 'foo', 456: 'bar'}

    def test_loading_dict_with_values_of_the_same_type(self):
        assert Dict(Integer()).load({'foo': 123, 'bar': 456}) == \
            {'foo': 123, 'bar': 456}

    def test_loading_dict_with_values_of_different_types(self):
        value = {'foo': 1, 'bar': 'hello', 'baz': True}
        assert Dict({'foo': Integer(), 'bar': String(), 'baz': Boolean()})\
            .load(value) == value

    def test_loading_accepts_any_value_if_value_types_are_not_specified(self):
        assert Dict()\
            .load({'foo': 'bar', 'baz': 123}) == {'foo': 'bar', 'baz': 123}

    def test_loading_non_dict_value_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Dict(Integer()).load(['1', '2'])
        assert exc_info.value.messages == Dict.default_error_messages['invalid']

    def test_loading_dict_with_incorrect_key_value_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Dict(Any(), key_type=Integer()).load({'123': 'foo', 'bar': 'baz'})
        assert exc_info.value.messages == \
            {'bar': Integer.default_error_messages['invalid']}

    def test_loading_dict_with_items_of_incorrect_type_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Dict(Integer()).load({'foo': 1, 'bar': 'abc'})
        message = Integer.default_error_messages['invalid']
        assert exc_info.value.messages == {'bar': message}

    def test_loading_dict_with_items_that_have_validation_errors_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Dict(Integer(validate=is_odd_validator())).load({'foo': 1, 'bar': 2})
        assert exc_info.value.messages == {'bar': is_odd_validator.message}

    def test_loading_does_not_validate_whole_list_if_items_have_errors(self):
        message1 = 'Something went wrong'
        def validate(value):
            validate.called += 1
        validate.called = 0
        with pytest.raises(ValidationError) as exc_info:
            Dict(Integer(validate=is_odd_validator()),
                 validate=[constant_fail_validator(message1)]).load([1, 2, 3])
        assert validate.called == 0

    def test_loading_dict_with_incorrect_key_value_and_incorrect_value_raises_ValidationError_with_both_errors(self):
        key_error = 'Key should be integer'
        with pytest.raises(ValidationError) as exc_info:
            Dict(String(), key_type=Integer(error_messages={'invalid': key_error}))\
                .load({123: 'foo', 'bar': 456})
        assert exc_info.value.messages == \
            {'bar': [key_error, String.default_error_messages['invalid']]}

    def test_loading_passes_context_to_inner_type_load(self):
        inner_type = SpyType()
        context = object()
        Dict(inner_type).load({'foo': 123}, context)
        assert inner_type.load_context == context

    def test_dumping_dict_with_custom_key_type(self):
        assert Dict(Any(), key_type=Transform(Integer(), post_dump=str))\
            .dump({123: 'foo', 456: 'bar'}) == {'123': 'foo', '456': 'bar'}

    def test_dumping_accepts_any_key_if_key_type_is_not_specified(self):
        assert Dict(Any())\
            .dump({'123': 'foo', 456: 'bar'}) == {'123': 'foo', 456: 'bar'}

    def test_dumping_dict_with_values_of_the_same_type(self):
        assert Dict(Integer()).dump({'foo': 123, 'bar': 456}) == \
            {'foo': 123, 'bar': 456}

    def test_dumping_dict_with_values_of_different_types(self):
        value = {'foo': 1, 'bar': 'hello', 'baz': True}
        assert Dict({'foo': Integer(), 'bar': String(), 'baz': Boolean()})\
            .load(value) == value

    def test_dumping_accepts_any_value_if_value_types_are_not_specified(self):
        assert Dict()\
            .dump({'foo': 'bar', 'baz': 123}) == {'foo': 'bar', 'baz': 123}

    def test_dumping_non_dict_value_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Dict(()).dump('1, 2, 3')
        assert exc_info.value.messages == Dict.default_error_messages['invalid']

    def test_dumping_dict_with_incorrect_key_value_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Dict(Any(), key_type=Transform(Integer(), post_dump=str))\
                .dump({123: 'foo', 'bar': 'baz'})
        assert exc_info.value.messages == \
            {'bar': Integer.default_error_messages['invalid']}

    def test_dumping_dict_with_items_of_incorrect_type_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Dict(Integer()).dump({'foo': 1, 'bar': 'abc'})
        message = Integer.default_error_messages['invalid']
        assert exc_info.value.messages == {'bar': message}

    def test_dumping_dict_with_incorrect_key_value_and_incorrect_value_raises_ValidationError_with_both_errors(self):
        key_error = 'Key should be integer'
        with pytest.raises(ValidationError) as exc_info:
            Dict(String(), key_type=Integer(error_messages={'invalid': key_error}))\
                .dump({123: 'foo', 'bar': 456})
        assert exc_info.value.messages == \
            {'bar': [key_error, String.default_error_messages['invalid']]}

    def test_dumping_passes_context_to_inner_type_dump(self):
        inner_type = SpyType()
        context = object()
        Dict(inner_type).dump({'foo': 123}, context)
        assert inner_type.dump_context == context


class TestOneOf:
    def test_loading_values_of_one_of_listed_types(self):
        one_of = OneOf([Integer(), String()])
        assert one_of.load('foo') == 'foo'
        assert one_of.load(123) == 123

    def test_loading_raises_ValidationError_if_value_is_of_unlisted_type(self):
        one_of = OneOf([Integer(), String()])
        with pytest.raises(ValidationError) as exc_info:
            one_of.load({'foo': 'bar'})
        assert exc_info.value.messages == OneOf.default_error_messages['no_type_matched']

    def test_loading_raises_ValidationError_if_deserialized_value_has_errors(self):
        message = 'Something is wrong'
        one_of = OneOf([
            Object({'foo': String()}),
            Object({'bar': Object({
                'baz': Integer(validate=constant_fail_validator(message))
            })}),
        ])
        with pytest.raises(ValidationError) as exc_info:
            one_of.load({'bar': {'baz': 123}})
        assert exc_info.value.messages == OneOf.default_error_messages['no_type_matched']

    def test_loading_raises_ValidationError_if_type_hint_is_unknown(self):
        one_of = OneOf({'foo': String(), 'bar': Integer()},
                       load_hint=dict_value_hint('type'))
        with pytest.raises(ValidationError) as exc_info:
            one_of.load({'type': 'baz'})
        assert exc_info.value.messages == \
            OneOf.default_error_messages['unknown_type_id'].format(type_id='baz')

    def test_loading_with_type_hinting(self):
        Foo = namedtuple('Foo', ['foo'])
        Bar = namedtuple('Bar', ['bar', 'baz'])

        FooType = Object({'foo': String()}, constructor=Foo)
        BarType = Object({'bar': Integer(), 'baz': Boolean()}, constructor=Bar)

        one_of = OneOf({
            'Foo': Object(FooType, {'type': 'foo'}, constructor=FooType.constructor),
            'Bar': Object(BarType, {'type': 'bar'}, constructor=BarType.constructor),
        }, load_hint=dict_value_hint('type', str.capitalize))

        assert one_of.load({'type': 'foo', 'foo': 'hello'}) == \
            Foo(foo='hello')
        assert one_of.load({'type': 'bar', 'bar': 123, 'baz': True}) == \
            Bar(bar=123, baz=True)

    def test_loading_with_type_hinting_raises_ValidationError_if_deserialized_value_has_errors(self):
        Foo = namedtuple('Foo', ['foo'])
        Bar = namedtuple('Bar', ['bar', 'baz'])

        FooType = Object({'foo': String()}, constructor=Foo)
        BarType = Object({'bar': Integer(), 'baz': Boolean()}, constructor=Bar)

        one_of = OneOf({
            'Foo': Object(FooType, {'type': 'foo'}, constructor=FooType.constructor),
            'Bar': Object(BarType, {'type': 'bar'}, constructor=BarType.constructor),
        }, load_hint=dict_value_hint('type', str.capitalize))

        with pytest.raises(ValidationError) as exc_info:
            one_of.load({'type': 'bar', 'bar': 'abc'})
        assert exc_info.value.messages == {'bar': 'Value should be integer',
                                           'baz': 'Value is required'}

    def test_dumping_values_of_one_of_listed_types(self):
        one_of = OneOf([Integer(), String()])
        assert one_of.dump('foo') == 'foo'
        assert one_of.dump(123) == 123

    def test_dumping_raises_ValidationError_if_value_is_of_unlisted_type(self):
        one_of = OneOf([Integer(), String()])
        with pytest.raises(ValidationError) as exc_info:
            one_of.dump({'foo': 'bar'})
        assert exc_info.value.messages == OneOf.default_error_messages['no_type_matched']

    def test_dumping_raises_ValidationError_if_type_hint_is_unknown(self):
        class Baz:
            pass

        one_of = OneOf({'foo': Integer(), 'bar': String()},
                       dump_hint=type_name_hint)
        with pytest.raises(ValidationError) as exc_info:
            one_of.dump(Baz())
        assert exc_info.value.messages == \
            OneOf.default_error_messages['unknown_type_id'].format(type_id='Baz')

    def test_dumping_raises_ValidationError_if_serialized_value_has_errors(self):
        Baz = namedtuple('Baz', ['baz'])
        Bar = namedtuple('Bar', ['bar'])

        message = 'Something is wrong'
        one_of = OneOf([
            Object({'foo': String()}),
            Object({'bar': Object({
                'baz': Integer(validate=constant_fail_validator(message))
            })}),
        ])
        with pytest.raises(ValidationError) as exc_info:
            one_of.dump(Bar(bar=Baz(baz='hello')))
        assert exc_info.value.messages == OneOf.default_error_messages['no_type_matched']

    def test_dumping_with_type_hinting(self):
        Foo = namedtuple('Foo', ['foo'])
        Bar = namedtuple('Bar', ['bar', 'baz'])

        FooType = Object({'foo': String()}, constructor=Foo)
        BarType = Object({'bar': Integer(), 'baz': Boolean()}, constructor=Bar)

        one_of = OneOf({
            'Foo': Object(FooType, {'type': 'foo'}, constructor=FooType.constructor),
            'Bar': Object(BarType, {'type': 'bar'}, constructor=BarType.constructor),
        }, load_hint=dict_value_hint('type', str.capitalize))

        assert one_of.dump(Foo(foo='hello')) == \
            {'type': 'foo', 'foo': 'hello'}
        assert one_of.dump(Bar(bar=123, baz=True)) == \
            {'type': 'bar', 'bar': 123, 'baz': True}

    def test_dumping_with_type_hinting_raises_ValidationError_if_deserialized_value_has_errors(self):
        Foo = namedtuple('Foo', ['foo'])
        Bar = namedtuple('Bar', ['bar', 'baz'])
        FooType = Object({'foo': String()}, constructor=Foo)
        BarType = Object({'bar': Integer(), 'baz': Boolean()}, constructor=Bar)

        one_of = OneOf({
            'Foo': Object(FooType, {'type': 'foo'}, constructor=FooType.constructor),
            'Bar': Object(BarType, {'type': 'bar'}, constructor=BarType.constructor),
        }, load_hint=dict_value_hint('type', str.capitalize))

        with pytest.raises(ValidationError) as exc_info:
            one_of.dump(Bar(bar='hello', baz=None))
        assert exc_info.value.messages == {'bar': 'Value should be integer',
                                           'baz': 'Value is required'}


class AttributeDummy:
    def __init__(self, foo='hello', bar=123):
        self.foo = foo
        self.bar = bar


class TestAttributeField:
    def test_getting_value_returns_value_of_given_object_attribute(self):
        obj = AttributeDummy()
        assert AttributeField(Any()).get_value('foo', obj) == obj.foo

    def test_getting_value_returns_value_of_configured_object_attribute(self):
        obj = AttributeDummy()
        assert AttributeField(Any(), attribute='bar')\
            .get_value('foo', obj) == obj.bar

    def test_getting_value_returns_value_of_field_name_transformed_with_given_name_transformation(self):
        class Dummy:
            def __init__(self, fooBar):
                self.fooBar = fooBar

        obj = Dummy(fooBar='hello')
        assert AttributeField(Any(), attribute=to_camel_case)\
            .get_value('foo_bar', obj) == obj.fooBar

    def test_setting_value_sets_given_value_to_given_object_attribute(self):
        obj = AttributeDummy()
        AttributeField(Any()).set_value('foo', obj, 'goodbye')
        assert obj.foo == 'goodbye'

    def test_setting_value_sets_given_value_to_configured_object_attribute(self):
        obj = AttributeDummy(foo='hello')
        AttributeField(Any(), attribute='bar').set_value('foo', obj, 'goodbye')
        assert obj.foo == 'hello'
        assert obj.bar == 'goodbye'

    def test_setting_value_sets_given_value_to_field_name_transformed_with_given_name_transformation(self):
        class Dummy:
            def __init__(self, fooBar):
                self.fooBar = fooBar

        obj = Dummy(fooBar='hello')
        AttributeField(Any(), attribute=to_camel_case)\
            .set_value('foo_bar', obj, 'goodbye')
        assert obj.fooBar == 'goodbye'

    def test_loading_value_with_field_type(self):
        field_type = SpyType()
        assert AttributeField(field_type)\
            .load('foo', {'foo': 'hello', 'bar': 123}) == 'hello'
        assert field_type.loaded == 'hello'

    def test_loading_given_attribute_regardless_of_attribute_override(self):
        assert AttributeField(String(), attribute='baz')\
            .load('foo', {'foo': 'hello', 'bar': 123, 'baz': 'goodbye'}) == 'hello'

    def test_loading_missing_value_if_attribute_does_not_exist(self):
        assert AttributeField(SpyType())\
            .load('foo', {'bar': 123, 'baz': 'goodbye'}) == MISSING

    def test_loading_passes_context_to_field_type_load(self):
        field_type = SpyType()
        context = object()
        AttributeField(field_type).load('foo', {'foo': 123}, context)
        assert field_type.load_context == context

    def test_dumping_given_attribute_from_object(self):
        assert AttributeField(SpyType())\
            .dump('foo', AttributeDummy()) == AttributeDummy().foo

    def test_dumping_object_attribute_with_field_type(self):
        field_type = SpyType()
        assert AttributeField(field_type).dump('foo', AttributeDummy())
        assert field_type.dumped == AttributeDummy().foo

    def test_dumping_a_different_attribute_from_object(self):
        assert AttributeField(SpyType(), attribute='bar')\
            .dump('foo', AttributeDummy()) == AttributeDummy().bar

    def test_dumping_passes_context_to_field_type_dump(self):
        field_type = SpyType()
        context = object()
        AttributeField(field_type).dump('foo', AttributeDummy(), context)
        assert field_type.dump_context == context


class MethodDummy:
    def __init__(self, foo='hello', bar=123):
        self._foo = foo
        self._bar = bar

    def foo(self):
        return self._foo

    def set_foo(self, value):
        self._foo = value

    def bar(self):
        return self._bar

    def set_bar(self, value):
        self._bar = value

    baz = 'goodbye'


class TestMethodField:
    def test_get_value_returns_result_of_calling_configured_method_on_object(self):
        obj = MethodDummy()
        assert MethodField(Any(), get='foo').get_value('quux', obj) == obj.foo()

    def test_get_value_returns_result_of_calling_method_calculated_by_given_function_on_object(self):
        class Dummy:
            def fooBar(self):
                return 'hello'

            def barBaz(self):
                return 123

        obj = Dummy()
        assert MethodField(Any(), get=to_camel_case)\
            .get_value('foo_bar', obj) == obj.fooBar()
        assert MethodField(Any(), get=to_camel_case)\
            .get_value('bar_baz', obj) == obj.barBaz()

    def test_get_value_returns_MISSING_if_get_method_is_not_specified(self):
        obj = MethodDummy()
        assert MethodField(Any()).get_value('quux', obj) == MISSING

    def test_get_value_raises_ValueError_if_method_does_not_exist(self):
        with pytest.raises(ValueError):
            MethodField(Any(), 'unknown').get_value('quux', MethodDummy())

    def test_get_value_raises_ValueError_if_property_is_not_callable(self):
        with pytest.raises(ValueError):
            MethodField(Any(), 'baz').get_value('quux', MethodDummy())

    def test_get_value_passes_context_to_method(self):
        class MyDummy(MethodDummy):
            def get_bam(self, context):
                self.get_context = context

        obj = MyDummy()
        context = object()

        MethodField(Any(), 'get_bam').get_value('quux', obj, context=context)
        assert obj.get_context is context

    def test_set_value_calls_configure_method_on_object(self):
        obj = MethodDummy()
        MethodField(Any(), set='set_foo').set_value('quux', obj, 'goodbye')
        assert obj.foo() == 'goodbye'

    def test_set_value_calls_method_calculated_by_given_function_on_object(self):
        class Dummy:
            def fooBar(self):
                return self._fooBar

            def setFooBar(self, value):
                self._fooBar = value

            def barBaz(self):
                return self._barBaz

            def setBarBaz(self, value):
                self._barBaz = value

        obj = Dummy()
        field = MethodField(Any(), set=lambda name: to_camel_case('set_'+name))

        field.set_value('foo_bar', obj, 'goodbye')
        field.set_value('bar_baz', obj, 456)

        assert obj.fooBar() == 'goodbye'
        assert obj.barBaz() == 456

    def test_set_value_does_not_do_anything_if_set_method_is_not_specified(self):
        obj = MethodDummy(foo='hello', bar=123)
        MethodField(Any()).set_value('quux', obj, 'goodbye')
        assert obj.foo() == 'hello'
        assert obj.bar() == 123

    def test_set_value_raises_ValueError_if_method_does_not_exist(self):
        with pytest.raises(ValueError):
            MethodField(Any(), set='unknown').set_value('quux', MethodDummy(), 'foo')

    def test_set_value_raises_ValueError_if_property_is_not_callable(self):
        with pytest.raises(ValueError):
            MethodField(Any(), set='baz').set_value('quux', MethodDummy(), 'foo')

    def test_set_value_passes_context_to_method(self):
        class MyDummy(MethodDummy):
            def set_bam(self, value, context):
                self.set_value = value
                self.set_context = context

        obj = MyDummy()
        context = object()
        MethodField(Any(), set='set_bam')\
            .set_value('quux', obj, 'hello', context=context)
        assert obj.set_value == 'hello'
        assert obj.set_context is context

    def test_loading_value_with_field_type(self):
        field_type = SpyType(load_result='goodbye')
        assert MethodField(field_type, 'foo')\
            .load('foo', {'foo': 'hello', 'bar': 123}) == 'goodbye'
        assert field_type.loaded == 'hello'

    def test_loading_value_returns_loaded_value(self):
        field_type = SpyType()
        assert MethodField(field_type, 'foo', 'set_foo')\
            .load('foo', {'foo': 'hello', 'bar': 123}) == 'hello'

    def test_loading_value_passes_context_to_field_types_load(self):
        field_type = SpyType()
        context = object()
        MethodField(field_type, 'foo').load('foo', {'foo': 'hello', 'bar': 123},
                                            context=context)
        assert field_type.load_context is context

    def test_loading_value_into_existing_object_calls_field_types_load_into(self):
        obj = MethodDummy(foo='hello')
        field_type = SpyTypeWithLoadInto()
        MethodField(field_type, 'foo', 'set_foo')\
            .load_into(obj, 'foo', {'foo': 'goodbye', 'bar': 123})
        assert field_type.loaded_into == ('hello', 'goodbye')

    def test_loading_value_into_existing_object_calls_field_types_load_if_load_into_is_not_available(self):
        obj = MethodDummy(foo='hello')
        field_type = SpyType()
        MethodField(field_type, 'foo', 'set_foo')\
            .load_into(obj, 'foo', {'foo': 'goodbye', 'bar': 123})
        assert field_type.loaded == 'goodbye'

    def test_loading_value_into_existing_object_calls_field_types_load_if_old_value_is_None(self):
        obj = MethodDummy(foo=None)
        field_type = SpyTypeWithLoadInto()
        MethodField(field_type, 'foo', 'set_foo')\
            .load_into(obj, 'foo', {'foo': 'goodbye', 'bar': 123})
        assert field_type.loaded_into is None
        assert field_type.loaded == 'goodbye'

    def test_loading_value_into_existing_object_calls_field_types_load_if_old_value_is_MISSING(self):
        class MyDummy(MethodDummy):
            def missing_field(self):
                return MISSING

        obj = MyDummy(foo=None)
        field_type = SpyTypeWithLoadInto()
        MethodField(field_type, 'missing_field', 'set_foo')\
            .load_into(obj, 'foo', {'foo': 'goodbye', 'bar': 123})

        assert field_type.loaded_into is None
        assert field_type.loaded == 'goodbye'

    def test_loading_value_into_existing_object_passes_context_to_field_types_load_into(self):
        obj = MethodDummy(foo='hello')
        field_type = SpyTypeWithLoadInto()
        context = object()
        MethodField(field_type, 'foo')\
            .load_into(obj, 'foo', {'foo': 'goodbye', 'bar': 123}, context=context)
        assert field_type.load_into_context is context

    def test_dumping_result_of_given_objects_method(self):
        assert MethodField(SpyType(), 'foo')\
            .dump('foo', MethodDummy()) == MethodDummy().foo()

    def test_dumping_result_of_objects_method_with_field_type(self):
        field_type = SpyType()
        assert MethodField(field_type, 'foo').dump('foo', MethodDummy())
        assert field_type.dumped == MethodDummy().foo()

    def test_dumping_result_of_a_different_objects_method(self):
        assert MethodField(SpyType(), get='bar')\
            .dump('foo', MethodDummy()) == MethodDummy().bar()

    def test_dumping_raises_ValueError_if_given_method_does_not_exist(self):
        with pytest.raises(ValueError):
            MethodField(SpyType(), get='unknown').dump('bam', MethodDummy())

    def test_dumping_raises_ValueError_if_given_method_is_not_callable(self):
        with pytest.raises(ValueError):
            MethodField(SpyType(), get='baz').dump('foo', MethodDummy())

    def test_dumping_passes_context_to_field_type_dump(self):
        field_type = SpyType()
        context = object()
        MethodField(field_type, 'foo').dump('foo', MethodDummy(), context)
        assert field_type.dump_context == context


class TestFunctionField:
    def test_get_value_returns_result_of_calling_configured_function_with_object(self):
        obj = MethodDummy()
        assert FunctionField(Any(), get=lambda obj: obj.foo()+'abc')\
            .get_value('quux', obj) == obj.foo()+'abc'

    def test_get_value_returns_MISSING_if_get_func_is_not_specified(self):
        obj = MethodDummy()
        assert FunctionField(Any()).get_value('quux', obj) == MISSING

    def test_get_value_raises_ValueError_if_property_is_not_callable(self):
        with pytest.raises(ValueError):
            FunctionField(Any(), 'foo')

    def test_get_value_passes_context_to_func(self):
        class Spy:
            def get_value(self, obj, context):
                self.obj = obj
                self.context = context

        spy = Spy()
        obj = MethodDummy()
        context = object()

        FunctionField(Any(), spy.get_value).get_value('quux', obj, context=context)

        assert spy.obj is obj
        assert spy.context is context

    def test_set_value_calls_configure_method_on_object(self):
        obj = MethodDummy()
        FunctionField(Any(), set=lambda o, v: o.set_foo(v))\
            .set_value('quux', obj, 'goodbye')
        assert obj.foo() == 'goodbye'

    def test_set_value_does_not_do_anything_if_set_func_is_not_specified(self):
        obj = MethodDummy(foo='hello', bar=123)
        FunctionField(Any()).set_value('quux', obj, 'goodbye')
        assert obj.foo() == 'hello'
        assert obj.bar() == 123

    def test_set_value_raises_ValueError_if_property_is_not_callable(self):
        with pytest.raises(ValueError):
            FunctionField(Any(), set='baz').set_value('quux', MethodDummy(), 'foo')

    def test_set_value_passes_context_to_func(self):
        class Spy:
            def set_bam(self, obj, value, context):
                self.set_obj = obj
                self.set_value = value
                self.set_context = context

        spy = Spy()
        obj = MethodDummy()
        context = object()

        FunctionField(Any(), set=spy.set_bam)\
            .set_value('quux', obj, 'hello', context=context)

        assert spy.set_obj is obj
        assert spy.set_value == 'hello'
        assert spy.set_context is context

    def test_loading_value_with_field_type(self):
        field_type = SpyType(load_result='goodbye')
        assert FunctionField(field_type, lambda obj: obj.foo)\
            .load('foo', {'foo': 'hello', 'bar': 123}) == 'goodbye'
        assert field_type.loaded == 'hello'

    def test_loading_value_returns_loaded_value(self):
        field_type = SpyType()
        assert FunctionField(field_type, lambda obj: obj.foo)\
            .load('foo', {'foo': 'hello', 'bar': 123}) == 'hello'

    def test_loading_value_passes_context_to_field_types_load(self):
        field_type = SpyType()
        context = object()
        FunctionField(field_type, lambda obj: obj.foo)\
            .load('foo', {'foo': 'hello', 'bar': 123}, context=context)
        assert field_type.load_context is context

    def test_loading_value_into_existing_object_calls_field_types_load_into(self):
        obj = MethodDummy(foo='hello')
        field_type = SpyTypeWithLoadInto()
        FunctionField(field_type,
                      lambda o: o.foo(),
                      lambda o, v: o.set_foo(v))\
            .load_into(obj, 'foo', {'foo': 'goodbye', 'bar': 123})
        assert field_type.loaded_into == ('hello', 'goodbye')

    def test_loading_value_into_existing_object_calls_field_types_load_if_load_into_is_not_available(self):
        obj = MethodDummy(foo='hello')
        field_type = SpyType()
        FunctionField(field_type, lambda o: o.foo(), lambda o, v: o.set_foo(v))\
            .load_into(obj, 'foo', {'foo': 'goodbye', 'bar': 123})
        assert field_type.loaded == 'goodbye'

    def test_loading_value_into_existing_object_calls_field_types_load_if_old_value_is_None(self):
        obj = MethodDummy(foo=None)
        field_type = SpyTypeWithLoadInto()
        FunctionField(field_type, lambda o: o.foo(), lambda o, v: o.set_foo(v))\
            .load_into(obj, 'foo', {'foo': 'goodbye', 'bar': 123})
        assert field_type.loaded_into is None
        assert field_type.loaded == 'goodbye'

    def test_loading_value_into_existing_object_calls_field_types_load_if_old_value_is_MISSING(self):
        class MyDummy(MethodDummy):
            def missing_field(self):
                return MISSING

        obj = MyDummy(foo=None)
        field_type = SpyTypeWithLoadInto()
        FunctionField(field_type, lambda o: o.missing_field(), lambda o, v: o.set_foo(v))\
            .load_into(obj, 'foo', {'foo': 'goodbye', 'bar': 123})

        assert field_type.loaded_into is None
        assert field_type.loaded == 'goodbye'

    def test_loading_value_into_existing_object_passes_context_to_field_types_load_into(self):
        obj = MethodDummy(foo='hello')
        field_type = SpyTypeWithLoadInto()
        context = object()
        FunctionField(field_type, lambda o: o.foo(), lambda o, v: o.set_foo(v))\
            .load_into(obj, 'foo', {'foo': 'goodbye', 'bar': 123}, context=context)
        assert field_type.load_into_context is context

    def test_dumping_result_of_given_function(self):
        obj = MethodDummy()
        assert FunctionField(SpyType(), lambda o: o.foo()+'abc')\
            .dump('foo', obj) == obj.foo()+'abc'

    def test_dumping_result_of_objects_method_with_field_type(self):
        field_type = SpyType()
        assert FunctionField(field_type, lambda o: 'goodbye')\
            .dump('foo', MethodDummy())
        assert field_type.dumped == 'goodbye'

    def test_dumping_raises_ValueError_if_given_get_func_is_not_callable(self):
        with pytest.raises(ValueError):
            FunctionField(SpyType(), get='baz').dump('foo', MethodDummy())

    def test_dumping_passes_context_to_field_type_dump(self):
        field_type = SpyType()
        context = object()
        FunctionField(field_type, lambda o: 'goodbye')\
            .dump('foo', MethodDummy(), context)
        assert field_type.dump_context == context


class TestConstant(NameDescriptionTestsMixin):
    tested_type = partial(Constant, 42)

    def test_loading_always_returns_missing(self):
        assert Constant(42).load(42) == MISSING

    def test_loading_raises_ValidationError_if_loaded_value_is_not_a_constant_value_specified(self):
        with pytest.raises(ValidationError) as exc_info:
            Constant(42).load(43)
        assert exc_info.value.messages == Constant.default_error_messages['value']

    def test_loading_value_with_inner_type_before_checking_value_correctness(self):
        inner_type = SpyType(load_result=42)
        assert Constant(42, inner_type).load(44) == MISSING
        assert inner_type.loaded == 44

    def test_customizing_error_message_when_value_is_incorrect(self):
        message = 'Bad value'
        with pytest.raises(ValidationError) as exc_info:
            Constant(42, error_messages={'value': message}).load(43)
        assert exc_info.value.messages == message

    def test_dumping_always_returns_given_value(self):
        assert Constant(42).dump(43) == 42
        assert Constant(42).dump(MISSING) == 42
        assert Constant(42).dump(None) == 42

    def test_dumping_given_constant_with_field_type(self):
        field_type = SpyType()
        Constant(42, field_type).dump(45)
        assert field_type.dumped == 42


class AlwaysMissingType(Type):
    def load(self, data, context=None):
        return MISSING

    def dump(self, value, context=None):
        return MISSING


class AlwaysInvalidType(Type):
    def __init__(self, error_message='Invalid'):
        super(AlwaysInvalidType, self).__init__()
        self.error_message = error_message

    def load(self, data, context=None):
        raise ValidationError(self.error_message)

    def dump(self, value, context=None):
        raise ValidationError(self.error_message)


class SpyField(Field):
    def get_value(self, name, obj, context=None):
        return 123

    def set_value(self, name, obj, value, context=None):
        pass

    def load(self, name, data, context=None):
        self.loaded = (name, data)
        return data

    def dump(self, name, obj, context=None):
        self.dumped = (name, obj)
        return obj

    def load_into(self, obj, name, data, inplace=True, context=None):
        self.loaded_into = (obj, name, data)
        self.load_into_context = context


class TestObject(NameDescriptionTestsMixin, RequiredTestsMixin, ValidationTestsMixin):
    tested_type = partial(Object, {'foo': String(), 'bar': Integer()})
    valid_data = {'foo': 'hello', 'bar': 123}
    valid_value = {'foo': 'hello', 'bar': 123}

    def test_default_field_type_is_unset_by_default(self):
        assert Object({'x': String()}).default_field_type is None

    def test_inheriting_default_field_type_from_first_base_class_that_has_it_set(self):
        field_type = MethodField
        a = Object({'a': String()})
        b = Object({'b': String()}, default_field_type=field_type)
        c = Object({'c': Integer()}, default_field_type=AttributeField)

        d = Object([a, b, c], {'d': Boolean()})

        assert d.default_field_type == field_type

    def test_constructor_is_unset_by_default(self):
        assert Object({'x': String()}).constructor is None

    def test_inheriting_constructor_from_first_base_class_that_has_it_set(self):
        class Foo:
            pass

        class Bar:
            pass

        a = Object({'a': String()})
        b = Object({'b': String()}, constructor=Foo)
        c = Object({'c': Integer()}, constructor=Bar)

        d = Object([a, b, c], {'d': Boolean()})

        assert d.constructor == Foo

    def test_allow_extra_fields_is_unset_by_default(self):
        assert Object({'x': String()}).allow_extra_fields is None

    def test_inheriting_allow_extra_fields_from_first_base_class_that_has_it_set(self):
        a = Object({'a': String()})
        b = Object({'b': String()}, allow_extra_fields=True)
        c = Object({'c': Integer()}, allow_extra_fields=False)

        d = Object([a, b, c], {'d': Boolean()})
        e = Object([a, c, b], {'e': Boolean()})

        assert d.allow_extra_fields == True
        assert e.allow_extra_fields == False

    def test_immutable_is_unset_by_default(self):
        assert Object({'x': String()}).immutable is None

    def test_inheriting_immutable_from_first_base_class_that_has_it_set(self):
        a = Object({'a': String()})
        b = Object({'b': String()}, immutable=True)
        c = Object({'c': Integer()}, immutable=False)

        d = Object([a, b, c], {'d': Boolean()})
        e = Object([a, c, b], {'e': Boolean()})

        assert d.immutable == True
        assert e.immutable == False

    def test_ordered_is_unset_by_default(self):
        assert Object({'x': String()}).ordered is None

    def test_iheriting_ordered_from_first_base_class_that_has_it_set(self):
        a = Object({'a': String()})
        b = Object({'b': String()}, ordered=True)
        c = Object({'c': Integer()}, ordered=False)

        d = Object([a, b, c], {'d': Boolean()})
        e = Object([a, c, b], {'e': Boolean()})

        assert d.ordered == True
        assert e.ordered == False

    def test_loading_dict_value(self):
        assert Object({'foo': String(), 'bar': Integer()})\
            .load({'foo': 'hello', 'bar': 123}) == {'foo': 'hello', 'bar': 123}

    def test_loading_non_dict_values_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Object({'foo': String(), 'bar': Integer()}).load(['hello', 123])
        assert exc_info.value.messages == Object.default_error_messages['invalid']

    def test_loading_bypasses_values_for_which_field_type_returns_missing_value(self):
        assert Object({'foo': AlwaysMissingType(), 'bar': Integer()})\
            .load({'foo': 'hello', 'bar': 123}) == {'bar': 123}

    def test_loading_dict_with_field_errors_raises_ValidationError_with_all_field_errors_merged(self):
        message1 = 'Error 1'
        message2 = 'Error 2'
        with pytest.raises(ValidationError) as exc_info:
            Object({
                'foo': AlwaysInvalidType(message1),
                'bar': AlwaysInvalidType(message2),
                'baz': String(),
            }).load({'foo': 'hello', 'bar': 123, 'baz': 'goodbye'})

        assert exc_info.value.messages == {'foo': message1, 'bar': message2}

    def test_loading_dict_with_field_errors_does_not_run_whole_object_validators(self):
        def validate(value):
            validate.called += 1
        validate.called = 0
        with pytest.raises(ValidationError):
            Object({
                'foo': AlwaysInvalidType(),
                'bar': AlwaysInvalidType(),
                'baz': String(),
            }, validate=validate).load({'foo': 'hello', 'bar': 123, 'baz': 'goodbye'})

        assert validate.called == 0

    def test_loading_calls_field_load_passing_field_name_and_whole_data(self):
        foo_field = SpyField(String())
        bar_field = SpyField(Integer())
        data = {'foo': 'hello', 'bar': 123}
        Object({'foo': foo_field, 'bar': bar_field}).load(data)
        assert foo_field.loaded == ('foo', data)
        assert bar_field.loaded == ('bar', data)

    def test_loading_passes_context_to_inner_type_load(self):
        foo_type = SpyType()
        bar_type = SpyType()
        context = object()
        Object({'foo': foo_type, 'bar': bar_type})\
            .load({'foo': 'hello', 'bar': 123}, context)
        assert foo_type.load_context == context
        assert bar_type.load_context == context

    def test_constructing_custom_objects_on_load(self):
        MyData = namedtuple('MyData', ['foo', 'bar'])
        assert Object({'foo': String(), 'bar': Integer()}, constructor=MyData)\
            .load({'foo': 'hello', 'bar': 123}) == MyData('hello', 123)

    def test_load_ignores_extra_fields_by_default(self):
        assert Object({'foo': String()})\
            .load({'foo': 'hello', 'bar': 123}) == {'foo': 'hello'}

    def test_load_raises_ValidationError_if_reporting_extra_fields(self):
        with pytest.raises(ValidationError) as exc_info:
            Object({'foo': String()}, allow_extra_fields=False)\
                .load({'foo': 'hello', 'bar': 123, 'baz': True})

        unknown = Object.default_error_messages['unknown']
        assert exc_info.value.messages == {'bar': unknown, 'baz': unknown}

    def test_loading_inherited_fields(self):
        Type1 = Object({'foo': String()})
        Type2 = Object(Type1, {'bar': Integer()})
        Type3 = Object(Type2, {'baz': Boolean()})
        assert Type3.load({'foo': 'hello', 'bar': 123, 'baz': True}) == \
            {'foo': 'hello', 'bar': 123, 'baz': True}

    def test_loading_multiple_inherited_fields(self):
        Type1 = Object({'foo': String()})
        Type2 = Object({'bar': Integer()})
        Type3 = Object([Type1, Type2], {'baz': Boolean()})
        assert Type3.load({'foo': 'hello', 'bar': 123, 'baz': True}) == \
            {'foo': 'hello', 'bar': 123, 'baz': True}

    def test_loading_raises_ValidationError_if_inherited_fields_have_errors(self):
        message = 'Invalid value'
        Type1 = Object({'foo': String(validate=constant_fail_validator(message))})
        Type2 = Object(Type1, {'bar': Integer()})
        Type3 = Object(Type2, {'baz': Boolean()})
        with pytest.raises(ValidationError) as exc_info:
            Type3.load({'foo': 'hello', 'baz': True})
        assert exc_info.value.messages == {'foo': message, 'bar': 'Value is required'}

    def test_loading_only_specified_fields(self):
        Type1 = Object({'foo': String()})
        Type2 = Object({'bar': String()})
        Type3 = Object([Type1, Type2], {'baz': Integer(), 'bam': Integer()},
                       only=['foo'])
        assert 'foo' in Type3.fields
        assert 'bar' not in Type3.fields
        assert Type3.load({'foo': 'hello', 'bar': 'goodbye',
                           'baz': 123, 'bam': 456}) == \
            {'foo': 'hello', 'baz': 123, 'bam': 456}

    def test_loading_only_specified_fields_does_not_affect_own_fields(self):
        Type1 = Object({'foo': String()})
        Type2 = Object({'bar': String()})
        Type3 = Object([Type1, Type2], {'baz': Integer(), 'bam': Integer()},
                       only=['foo', 'baz'])
        assert 'baz' in Type3.fields
        assert Type3.load({'foo': 'hello', 'bar': 'goodbye',
                           'baz': 123, 'bam': 456}) == \
            {'foo': 'hello', 'baz': 123, 'bam': 456}

    def test_loading_all_but_specified_base_class_fields(self):
        Type1 = Object({'foo': String()})
        Type2 = Object({'bar': String()})
        Type3 = Object([Type1, Type2], {'baz': Integer(), 'bam': Integer()},
                       exclude=['foo'])
        assert 'foo' not in Type3.fields
        assert Type3.load({'foo': 'hello', 'bar': 'goodbye',
                           'baz': 123, 'bam': 456}) == \
            {'bar': 'goodbye', 'baz': 123, 'bam': 456}

    def test_loading_all_but_specified_fields_does_not_affect_own_fields(self):
        Type1 = Object({'foo': String()})
        Type2 = Object({'bar': String()})
        Type3 = Object([Type1, Type2], {'baz': Integer(), 'bam': Integer()},
                       exclude=['foo', 'baz'])
        assert 'baz' in Type3.fields
        assert Type3.load({'foo': 'hello', 'bar': 'goodbye',
                           'baz': 123, 'bam': 456}) == \
            {'bar': 'goodbye', 'baz': 123, 'bam': 456}

    def test_loading_values_into_existing_object(self):
        obj = AttributeDummy()
        obj.foo = 'hello'
        obj.bar = 123

        Object({'foo': String(), 'bar': Integer()})\
            .load_into(obj, {'foo': 'goodbye', 'bar': 456})

        assert obj.foo == 'goodbye'
        assert obj.bar == 456

    def test_loading_values_into_existing_object_returns_that_object(self):
        obj = AttributeDummy()
        obj.foo = 'hello'
        obj.bar = 123

        assert obj is Object({'foo': String(), 'bar': Integer()})\
            .load_into(obj, {'foo': 'goodbye', 'bar': 456})

    def test_loading_values_into_existing_object_passes_all_object_attributes_to_validators(self):
        obj = AttributeDummy()
        obj.foo = 'hello'
        obj.bar = 123

        validator = SpyValidator()
        Object({'foo': String(), 'bar': Integer()}, validate=validator)\
            .load_into(obj, {'foo': 'goodbye'})
        assert validator.validated == {'foo': 'goodbye', 'bar': 123}

    def test_loading_values_into_immutable_object_creates_a_copy(self):
        obj = AttributeDummy()
        obj.foo = 'hello'
        obj.bar = 123

        obj_type = Object({'foo': String(), 'bar': Integer()},
                          constructor=AttributeDummy, immutable=True)
        result = obj_type.load_into(obj, {'foo': 'goodbye'})
        assert result is not obj
        assert result.foo == 'goodbye'
        assert result.bar == 123

    def test_loading_values_into_immutable_object_does_not_modify_original_object(self):
        obj = AttributeDummy()
        obj.foo = 'hello'
        obj.bar = 123

        obj_type = Object({'foo': String(), 'bar': Integer()},
                          constructor=AttributeDummy, immutable=True)
        obj_type.load_into(obj, {'foo': 'goodbye'})
        assert obj.foo == 'hello'
        assert obj.bar == 123

    def test_loading_values_into_nested_object_of_immutable_object_creates_copy_of_it_regardless_of_nested_objects_immutable_flag(self):
        class Foo:
            def __init__(self, foo, bar):
                self.foo = foo
                self.bar = bar

        class Bar:
            def __init__(self, baz, bam):
                self.baz = baz
                self.bam = bam

        BarType = Object({
            'baz': String(),
            'bam': Boolean(),
        }, constructor=Bar)

        FooType = Object({
            'foo': Integer(),
            'bar': BarType,
        }, constructor=Foo, immutable=True)

        foo = Foo(123, Bar('hello', False))

        result = FooType.load_into(foo, {'bar': {'baz': 'goodbye'}})

        assert result is not foo
        assert result.bar is not foo.bar

    def test_loading_values_into_nested_object_of_immutable_object_does_not_modify_original_objects(self):
        class Foo:
            def __init__(self, foo, bar):
                self.foo = foo
                self.bar = bar

        class Bar:
            def __init__(self, baz, bam):
                self.baz = baz
                self.bam = bam

        BarType = Object({
            'baz': String(),
            'bam': Boolean(),
        }, constructor=Bar)

        FooType = Object({
            'foo': Integer(),
            'bar': BarType,
        }, constructor=Foo, immutable=True)

        foo = Foo(123, Bar('hello', False))

        result = FooType.load_into(foo, {'bar': {'baz': 'goodbye'}})

        assert foo.bar.baz == 'hello'

    def test_loading_values_into_nested_objects_with_inplace_False_does_not_modify_original_objects(self):
        class Foo:
            def __init__(self, foo, bar):
                self.foo = foo
                self.bar = bar

        class Bar:
            def __init__(self, baz, bam):
                self.baz = baz
                self.bam = bam

        BarType = Object({
            'baz': String(),
            'bam': Boolean(),
        }, constructor=Bar)

        FooType = Object({
            'foo': Integer(),
            'bar': BarType,
        }, constructor=Foo)

        foo = Foo(123, Bar('hello', False))

        result = FooType.load_into(foo, {'bar': {'baz': 'goodbye'}}, inplace=False)

        assert foo.bar.baz == 'hello'
        assert result.bar.baz == 'goodbye'

    def test_loading_values_into_existing_objects_ignores_missing_fields(self):
        obj = AttributeDummy(foo='hello', bar=123)

        Object({'foo': String(), 'bar': Integer()})\
            .load_into(obj, {'foo': 'goodbye'})

        assert obj.foo == 'goodbye'
        assert obj.bar == 123

    def test_loading_MISSING_into_existing_object_does_not_do_anything(self):
        obj = AttributeDummy(foo='hello', bar=123)
        Object({'foo': String()}).load_into(AttributeDummy(), MISSING)

        assert obj.foo == 'hello'
        assert obj.bar == 123

    def test_loading_None_into_existing_objects_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Object({'foo': String()}).load_into(AttributeDummy(), None)
        assert exc_info.value.messages == Type.default_error_messages['required']

    def test_loading_None_into_field_of_existing_object_passes_None_to_field(self):
        obj = AttributeDummy()
        field = SpyField(Any())

        data = {'foo': None, 'bar': 456}

        Object({'foo': field, 'bar': Integer()}).load_into(obj, data)

        assert field.loaded_into == (obj, 'foo', data)

    def test_loading_values_into_existing_objects_raises_ValidationError_if_data_contains_errors(self):
        obj = AttributeDummy()
        obj.foo = 'hello'
        obj.bar = 123

        with pytest.raises(ValidationError) as exc_info:
            Object({'foo': String(), 'bar': Integer()})\
                .load_into(obj, {'foo': 123})
        assert exc_info.value.messages == \
            {'foo': String.default_error_messages['invalid']}

    def test_loading_values_into_existing_objects_raises_ValidationError_if_validator_fails(self):
        obj = AttributeDummy()
        obj.foo = 'hello'
        obj.bar = 123

        error = 'Bad object'
        with pytest.raises(ValidationError) as exc_info:
            Object({'foo': String(), 'bar': Integer()},
                   validate=constant_fail_validator(error))\
                .load_into(obj, {'foo': 'goodbye'})
        assert exc_info.value.messages == error

    def test_loading_values_into_existing_objects_annotates_field_errors_with_field_names(self):
        error = 'My error'
        with pytest.raises(ValidationError) as exc_info:
            Object({'foo': String(),
                    'bar': Integer(validate=constant_fail_validator(error))})\
                .load_into(AttributeDummy(), {'bar': 111})
        assert exc_info.value.messages == {'bar': error}

    def test_loading_values_into_existing_nested_objects(self):
        class Foo:
            def __init__(self, bar):
                self.bar = bar

        class Bar:
            def __init__(self, baz):
                self.baz = baz

        class Baz:
            def __init__(self, bam):
                self.bam = bam

        BazType = Object({'bam': Integer()}, constructor=Baz)
        BarType = Object({'baz': BazType}, constructor=Bar)
        FooType = Object({'bar': BarType}, constructor=Foo)

        foo = Foo(bar=Bar(baz=Baz(123)))
        result = FooType.load_into(foo, {'bar': {'baz': {'bam': 456}}})

        assert result is foo
        assert result.bar.baz.bam == 456

    def test_loading_values_into_existing_object_when_nested_object_does_not_exist(self):
        class Foo:
            def __init__(self, bar):
                self.bar = bar

        class Bar:
            def __init__(self, baz):
                self.baz = baz

        class Baz:
            def __init__(self, bam):
                self.bam = bam

        BazType = Object({'bam': Integer()}, constructor=Baz)
        BarType = Object({'baz': BazType}, constructor=Bar)
        FooType = Object({'bar': BarType}, constructor=Foo)

        foo = Foo(bar=None)
        result = FooType.load_into(foo, {'bar': {'baz': {'bam': 456}}})

        assert result is foo
        assert result.bar.baz.bam == 456

    def test_validating_data_for_existing_objects_returns_None_if_data_is_valid(self):
        obj = AttributeDummy()
        obj.foo = 'hello'
        obj.bar = 123

        assert Object({'foo': String(), 'bar': Integer()})\
            .validate_for(obj, {'foo': 'goodbye'}) is None

    def test_validating_data_for_existing_objects_returns_errors_if_data_contains_errors(self):
        obj = AttributeDummy()
        obj.foo = 'hello'
        obj.bar = 123

        invalid = String.default_error_messages['invalid']

        assert Object({'foo': String(), 'bar': Integer()})\
                .validate_for(obj, {'foo': 123}) == {'foo': invalid}

    def test_validating_data_for_existing_objects_returns_errors_if_validator_fails(self):
        obj = AttributeDummy()
        obj.foo = 'hello'
        obj.bar = 123

        error = 'Bad object'
        assert Object({'foo': String(), 'bar': Integer()},
                   validate=constant_fail_validator(error))\
                .validate_for(obj, {'foo': 'goodbye'}) == error

    def test_validating_data_for_existing_objects_does_not_modify_original_objects(self):
        obj = AttributeDummy()
        obj.foo = 'hello'
        obj.bar = 123

        Object({'foo': String(), 'bar': Integer()})\
            .validate_for(obj, {'foo': 'goodbye'})

        assert obj.foo == 'hello'
        assert obj.bar == 123

    def test_dumping_object_attributes(self):
        MyData = namedtuple('MyData', ['foo', 'bar'])
        assert Object({'foo': String(), 'bar': Integer()})\
            .dump(MyData('hello', 123)) == {'foo': 'hello', 'bar': 123}

    def test_dumping_calls_field_dump_passing_field_name_and_whole_object(self):
        foo_field = SpyField(String())
        bar_field = SpyField(Integer())
        MyData = namedtuple('MyData', ['foo', 'bar'])
        obj = MyData('hello', 123)
        Object({'foo': foo_field, 'bar': bar_field}).dump(obj)
        assert foo_field.dumped == ('foo', obj)
        assert bar_field.dumped == ('bar', obj)

    def test_dumping_passes_context_to_inner_type_dump(self):
        foo_type = SpyType()
        bar_type = SpyType()
        context = object()
        Object({'foo': foo_type, 'bar': bar_type})\
            .dump(AttributeDummy(), context)
        assert foo_type.dump_context == context
        assert bar_type.dump_context == context

    def test_dumping_inherited_fields(self):
        Type1 = Object({'foo': String()})
        Type2 = Object(Type1, {'bar': Integer()})
        Type3 = Object(Type2, {'baz': Boolean()})
        MyData = namedtuple('MyData', ['foo', 'bar', 'baz'])
        assert Type3.dump(MyData(foo='hello', bar=123, baz=True)) == \
            {'foo': 'hello', 'bar': 123, 'baz': True}

    def test_dumping_multiple_inherited_fields(self):
        Type1 = Object({'foo': String()})
        Type2 = Object({'bar': Integer()})
        Type3 = Object([Type1, Type2], {'baz': Boolean()})
        MyData = namedtuple('MyData', ['foo', 'bar', 'baz'])
        assert Type3.dump(MyData(foo='hello', bar=123, baz=True)) == \
            {'foo': 'hello', 'bar': 123, 'baz': True}

    def test_dumping_only_specified_fields_of_base_classes(self):
        Type1 = Object({'foo': String()})
        Type2 = Object({'bar': String()})
        Type3 = Object([Type1, Type2], {'baz': Integer(), 'bam': Integer()},
                       only=['foo'])
        MyData = namedtuple('MyData', ['foo', 'bar', 'baz', 'bam'])
        assert Type3.dump(MyData(foo='hello', bar='goodbye', baz=123, bam=456)) == \
            {'foo': 'hello', 'baz': 123, 'bam': 456}

    def test_dumping_only_specified_fields_does_not_affect_own_fields(self):
        Type1 = Object({'foo': String()})
        Type2 = Object({'bar': String()})
        Type3 = Object([Type1, Type2], {'baz': Integer(), 'bam': Integer()},
                       only=['foo', 'baz'])
        assert 'baz' in Type3.fields
        MyData = namedtuple('MyData', ['foo', 'bar', 'baz', 'bam'])
        assert Type3.dump(MyData(foo='hello', bar='goodbye', baz=123, bam=456)) == \
            {'foo': 'hello', 'baz': 123, 'bam': 456}

    def test_dumping_all_but_specified_base_class_fields(self):
        Type1 = Object({'foo': String()})
        Type2 = Object({'bar': String()})
        Type3 = Object([Type1, Type2], {'baz': Integer(), 'bam': Integer()},
                       exclude=['foo'])
        MyData = namedtuple('MyData', ['foo', 'bar', 'baz', 'bam'])
        assert Type3.dump(MyData(foo='hello', bar='goodbye', baz=123, bam=456)) == \
            {'bar': 'goodbye', 'baz': 123, 'bam': 456}

    def test_dumping_all_but_specified_fields_does_not_affect_own_fields(self):
        Type1 = Object({'foo': String()})
        Type2 = Object({'bar': String()})
        Type3 = Object([Type1, Type2], {'baz': Integer(), 'bam': Integer()},
                       exclude=['foo', 'baz'])
        assert 'baz' in Type3.fields
        MyData = namedtuple('MyData', ['foo', 'bar', 'baz', 'bam'])
        assert Type3.dump(MyData(foo='hello', bar='goodbye', baz=123, bam=456)) == \
            {'bar': 'goodbye', 'baz': 123, 'bam': 456}

    def test_shortcut_for_specifying_constant_fields(self):
        MyType = Object({'foo': 'hello'})
        assert MyType.dump({}) == {'foo': 'hello'}

    def test_dumping_fields_in_declared_order_if_ordered_is_True(self):
        assert list(Object([('bar', Integer()), ('foo', String())], ordered=True)\
            .dump(AttributeDummy()).keys()) == ['bar', 'foo']
        assert list(Object(OrderedDict([('foo', String()), ('bar', Integer())]), ordered=True)\
            .dump(AttributeDummy()).keys()) == ['foo', 'bar']


class TestOptional:
    def test_loading_value_calls_load_of_inner_type(self):
        inner_type = SpyType()
        Optional(inner_type).load('foo')
        assert inner_type.loaded == 'foo'

    def test_loading_missing_value_returns_None(self):
        assert Optional(Any()).load(MISSING) == None

    def test_loading_None_returns_None(self):
        assert Optional(Any()).load(None) == None

    def test_loading_missing_value_does_not_call_inner_type_load(self):
        inner_type = SpyType()
        Optional(inner_type).load(None)
        assert not inner_type.load_called

    def test_loading_None_does_not_call_inner_type_load(self):
        inner_type = SpyType()
        Optional(inner_type).load(MISSING)
        assert not inner_type.load_called

    def test_loading_passes_context_to_inner_type_load(self):
        inner_type = SpyType()
        context = object()
        Optional(inner_type).load('foo', context)
        assert inner_type.load_context == context

    def test_overriding_missing_value_on_load(self):
        assert Optional(Any(), load_default='foo').load(MISSING) == 'foo'

    def test_overriding_None_value_on_load(self):
        assert Optional(Any(), load_default='foo').load(None) == 'foo'

    def test_using_function_to_override_value_on_load(self):
        result = Optional(Any(), load_default=random_string).load(None)
        assert isinstance(result, str)

    def test_loading_passes_context_to_override_function(self):
        class Spy:
            def __init__(self):
                self.context = None
                self.called = False

            def generate_value(self, context):
                self.called = True
                self.context = context
                return 123

        spy = Spy()
        context = object()

        Optional(Any(), load_default=spy.generate_value).load(None, context)

        assert spy.called is True
        assert spy.context is context

    def test_dumping_value_calls_dump_of_inner_type(self):
        inner_type = SpyType()
        Optional(inner_type).dump('foo')
        assert inner_type.dumped == 'foo'

    def test_dumping_missing_value_returns_None(self):
        assert Optional(Any()).dump(MISSING) == None

    def test_dumping_None_returns_None(self):
        assert Optional(Any()).dump(None) == None

    def test_dumping_missing_value_does_not_call_inner_type_dump(self):
        inner_type = SpyType()
        Optional(inner_type).dump(MISSING)
        assert not inner_type.dump_called

    def test_dumping_None_does_not_call_inner_type_dump(self):
        inner_type = SpyType()
        Optional(inner_type).dump(None)
        assert not inner_type.dump_called

    def test_dumping_passes_context_to_inner_type_dump(self):
        inner_type = SpyType()
        context = object()
        Optional(inner_type).dump('foo', context)
        assert inner_type.dump_context == context

    def test_overriding_missing_value_on_dump(self):
        assert Optional(Any(), dump_default='foo').dump(MISSING) == 'foo'

    def test_overriding_None_value_on_dump(self):
        assert Optional(Any(), dump_default='foo').dump(None) == 'foo'

    def test_using_function_to_override_value_on_dump(self):
        result = Optional(Any(), dump_default=random_string).dump(None)
        assert isinstance(result, str)

    def test_dumping_passes_context_to_override_function(self):
        class Spy:
            def __init__(self):
                self.context = None
                self.called = False

            def generate_value(self, context):
                self.called = True
                self.context = context
                return 123

        spy = Spy()
        context = object()

        Optional(Any(), dump_default=spy.generate_value).dump(None, context)

        assert spy.called is True
        assert spy.context is context


class ProxyNameDescriptionTestsMixin(object):
    """Mixin that adds tests for proxying name and description attributes
    to an inner type.
    Host class should define `tested_type` properties.
    """
    def test_name(self):
        assert self.tested_type(Type(name='foo')).name == 'foo'

    def test_description(self):
        assert self.tested_type(Type(description='Just a description')).description \
            == 'Just a description'


class TestLoadOnly(ProxyNameDescriptionTestsMixin):
    tested_type = LoadOnly

    def test_loading_returns_inner_type_load_result(self):
        inner_type = SpyType(load_result='bar')
        assert LoadOnly(inner_type).load('foo') == 'bar'
        assert inner_type.load_called

    def test_loading_passes_context_to_inner_type_load(self):
        inner_type = SpyType()
        context = object()
        LoadOnly(inner_type).load('foo', context)
        assert inner_type.load_context == context

    def test_dumping_always_returns_missing(self):
        assert LoadOnly(Any()).dump('foo') == MISSING

    def test_dumping_does_not_call_inner_type_dump(self):
        inner_type = SpyType()
        LoadOnly(inner_type).dump('foo')
        assert not inner_type.dump_called


class TestDumpOnly(ProxyNameDescriptionTestsMixin):
    tested_type = DumpOnly

    def test_loading_always_returns_missing(self):
        assert DumpOnly(Any()).load('foo') == MISSING

    def test_loading_does_not_call_inner_type_dump(self):
        inner_type = SpyType()
        DumpOnly(inner_type).load('foo')
        assert not inner_type.load_called

    def test_dumping_returns_inner_type_dump_result(self):
        inner_type = SpyType(dump_result='bar')
        assert DumpOnly(inner_type).dump('foo') == 'bar'
        assert inner_type.dump_called

    def test_dumping_passes_context_to_inner_type_dump(self):
        inner_type = SpyType()
        context = object()
        DumpOnly(inner_type).dump('foo', context)
        assert inner_type.dump_context == context


class TestTransform(ProxyNameDescriptionTestsMixin):
    tested_type = Transform

    def test_loading_calls_pre_load_with_original_value(self):
        class Callbacks():
            def pre_load(self, data):
                self.pre_loaded = data
                return data
        callbacks = Callbacks()
        Transform(SpyType(), pre_load=callbacks.pre_load).load('foo')
        assert callbacks.pre_loaded == 'foo'

    def test_loading_calls_inner_type_load_with_result_of_pre_load(self):
        inner_type = SpyType()
        transform = Transform(inner_type, pre_load=lambda foo: 'bar').load('foo')
        assert inner_type.loaded == 'bar'

    def test_loading_calls_post_load_with_result_of_inner_type_load(self):
        inner_type = SpyType()
        transform = Transform(inner_type,
                              post_load=lambda foo: foo + 'bar').load('foo')
        assert inner_type.loaded == 'foo'
        assert transform == 'foobar'

    def test_transform_passes_context_to_inner_type_load(self):
        inner_type = SpyType()
        context = object()
        transform = Transform(inner_type).load('foo', context)
        assert inner_type.load_context == context

    def test_transform_passes_context_to_pre_load(self):
        inner_type = SpyType()
        context = object()
        transform = Transform(inner_type,
                              pre_load=lambda foo, context: [foo, context])
        assert transform.load('foo', context) == ['foo', context]

    def test_transform_passes_context_to_post_load(self):
        inner_type = SpyType()
        context = object()
        transform = Transform(inner_type,
                              post_load=lambda foo, context: [foo,context])
        assert transform.load('foo', context) == ['foo', context]

    def test_dumping_calls_pre_dump_with_original_value(self):
        class Callbacks():
            def pre_dump(self, data):
                self.pre_dumped = data
                return data
        callbacks = Callbacks()
        Transform(SpyType(), pre_dump=callbacks.pre_dump).dump('foo')
        assert callbacks.pre_dumped == 'foo'

    def test_dumping_calls_inner_type_dump_with_result_of_pre_dump(self):
        inner_type = SpyType()
        transform = Transform(inner_type, pre_dump=lambda foo: 'bar').dump('foo')
        assert inner_type.dumped == 'bar'

    def test_dumping_calls_post_dump_with_result_of_inner_type_dump(self):
        inner_type = SpyType()
        transform = Transform(inner_type,
                              post_dump=lambda foo: foo + 'bar').dump('foo')
        assert transform == 'foobar'

    def test_transform_passes_context_to_inner_type_dump(self):
        inner_type = SpyType()
        context = object()
        transform = Transform(inner_type).dump('foo', context)
        assert inner_type.dump_context == context

    def test_transform_passes_context_to_pre_dump(self):
        inner_type = SpyType()
        context = object()
        transform = Transform(inner_type,
                              pre_dump=lambda foo, context: [foo, context])
        assert transform.dump('foo', context) == ['foo', context]

    def test_transform_passes_context_to_post_dump(self):
        inner_type = SpyType()
        context = object()
        transform = Transform(inner_type,
                              post_dump=lambda foo, context: [foo,context])
        assert transform.dump('foo', context) == ['foo', context]


class TestValidatedType:
    def test_returns_subclass_of_given_type(self):
        base_type = String
        assert issubclass(validated_type(base_type), base_type)

    def test_returns_type_that_has_single_given_validator(self):
        OddInteger = validated_type(Integer, validate=is_odd_validator())
        assert OddInteger().validate(1) is None
        assert OddInteger().validate(2) == is_odd_validator.message

    def test_accepts_context_unaware_validators(self):
        error_message = 'Value should be odd'
        def context_unaware_is_odd_validator(value):
            if value % 2 == 0:
                raise ValidationError(error_message)

        OddInteger = validated_type(Integer, validate=context_unaware_is_odd_validator)
        assert OddInteger().validate(1) is None
        assert OddInteger().validate(2) == error_message

    def test_returns_type_that_has_multiple_given_validators(self):
        MyInteger = validated_type(Integer, validate=[divisible_by_validator(3),
                                                      divisible_by_validator(5)])
        my_type = MyInteger()
        assert my_type.validate(1) == ['Value should be divisible by 3',
                                       'Value should be divisible by 5']
        assert my_type.validate(3) == 'Value should be divisible by 5'
        assert my_type.validate(5) == 'Value should be divisible by 3'
        assert my_type.validate(15) is None

    def test_specifying_more_validators_on_type_instantiation(self):
        MyInteger = validated_type(Integer, validate=divisible_by_validator(3))
        my_type = MyInteger(validate=divisible_by_validator(5))
        assert my_type.validate(1) == ['Value should be divisible by 3',
                                       'Value should be divisible by 5']
        assert my_type.validate(3) == 'Value should be divisible by 5'
        assert my_type.validate(5) == 'Value should be divisible by 3'
        assert my_type.validate(15) is None

    def test_new_type_accepts_same_constructor_arguments_as_base_type(self):
        class MyType(Type):
            def __init__(self, foo='foo', *args, **kwargs):
                super(MyType, self).__init__(*args, **kwargs)
                self.foo = foo

        MyValidatedType = validated_type(MyType)
        assert MyValidatedType().foo == 'foo'
        assert MyValidatedType(foo='bar').foo == 'bar'
