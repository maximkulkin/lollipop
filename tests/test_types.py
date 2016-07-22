import pytest
from zephyr.types import MISSING, ValidationError, Type, String, Integer, Boolean, \
    List, Dict, Field, AttributeField, MethodField, FunctionField, ConstantField, \
    Object
from zephyr.utils import merge_errors
from collections import namedtuple


def validator(predicate, message='Something went wrong'):
    def validate(value):
        if not predicate(value):
            raise ValidationError(message)

    return validate


def constant_succeed_validator():
    """Returns validator that always succeeds"""
    return validator(lambda _: True)


def constant_fail_validator(message):
    """Returns validator that always fails with given message"""
    return validator(lambda _: False, message)


def is_odd_validator():
    """Returns validator that checks if integer is odd"""
    return validator(lambda x: x % 2 == 1, 'Value should be odd')


class TestString:
    def test_loading_string_value(self):
        assert String().load('foo') == 'foo'

    def test_loading_missing_value_raises_required_error(self):
        with pytest.raises(ValidationError) as exc_info:
            String().load(MISSING)
        assert exc_info.value.messages == String.default_error_messages['required']

    def test_loading_None_raises_required_error(self):
        with pytest.raises(ValidationError) as exc_info:
            String().load(None)
        assert exc_info.value.messages == String.default_error_messages['required']

    def test_loading_non_string_value_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            String().load(123)
        assert exc_info.value.messages == \
            String.default_error_messages['invalid_type'].format(expected='string')

    def test_loading_does_not_raise_ValidationError_if_validators_succeed(self):
        assert String(validate=[constant_succeed_validator(),
                                constant_succeed_validator()]).load('foo') == 'foo'

    def test_loading_raises_ValidationError_if_validator_fails(self):
        message1 = 'Something went wrong'
        with pytest.raises(ValidationError) as exc_info:
            String(validate=constant_fail_validator(message1)).load('foo')
        assert exc_info.value.messages == message1

    def test_loading_raises_ValidationError_with_combined_messages_if_multiple_validators_fail(self):
        message1 = 'Something went wrong 1'
        message2 = 'Something went wrong 2'
        with pytest.raises(ValidationError) as exc_info:
            String(validate=[constant_fail_validator(message1),
                             constant_fail_validator(message2)]).load('foo')
        assert exc_info.value.messages == merge_errors(message1, message2)

    def test_dumping_string_value(self):
        assert String().dump('foo') == 'foo'

    def test_dumping_missing_value_raises_required_error(self):
        with pytest.raises(ValidationError) as exc_info:
            String().dump(MISSING)
        assert exc_info.value.messages == String.default_error_messages['required']

    def test_dumping_None_raises_required_error(self):
        with pytest.raises(ValidationError) as exc_info:
            String().dump(None)
        assert exc_info.value.messages == String.default_error_messages['required']

    def test_dumping_non_string_value_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            String().dump(123)
        assert exc_info.value.messages == \
            String.default_error_messages['invalid_type'].format(expected='string')


class TestInteger:
    def test_loading_integer_value(self):
        assert Integer().load(123) == 123

    def test_loading_long_value(self):
        value = 10000000000000000000000000000000000000
        assert Integer().load(value) == value

    def test_loading_missing_value_raises_required_error(self):
        with pytest.raises(ValidationError) as exc_info:
            Integer().load(MISSING)
        assert exc_info.value.messages == Integer.default_error_messages['required']

    def test_loading_None_raises_required_error(self):
        with pytest.raises(ValidationError) as exc_info:
            Integer().load(None)
        assert exc_info.value.messages == Integer.default_error_messages['required']

    def test_loading_non_integer_value_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Integer().load("123")
        assert exc_info.value.messages == \
            Integer.default_error_messages['invalid_type'].format(expected='integer')

    def test_loading_does_not_raise_ValidationError_if_validators_succeed(self):
        assert Integer(validate=[constant_succeed_validator(),
                                 constant_succeed_validator()]).load(123) == 123

    def test_loading_raises_ValidationError_if_validator_fails(self):
        message1 = 'Something went wrong'
        with pytest.raises(ValidationError) as exc_info:
            Integer(validate=constant_fail_validator(message1)).load(123)
        assert exc_info.value.messages == message1

    def test_loading_raises_ValidationError_with_combined_messages_if_multiple_validators_fail(self):
        message1 = 'Something went wrong 1'
        message2 = 'Something went wrong 2'
        with pytest.raises(ValidationError) as exc_info:
            Integer(validate=[constant_fail_validator(message1),
                              constant_fail_validator(message2)]).load(123)
        assert exc_info.value.messages == merge_errors(message1, message2)

    def test_dumping_integer_value(self):
        assert Integer().dump(123) == 123

    def test_dumping_long_value(self):
        value = 10000000000000000000000000000000000000
        assert Integer().dump(value) == value

    def test_dumping_missing_value_raises_required_error(self):
        with pytest.raises(ValidationError) as exc_info:
            Integer().load(MISSING)
        assert exc_info.value.messages == Integer.default_error_messages['required']

    def test_dumping_None_raises_required_error(self):
        with pytest.raises(ValidationError) as exc_info:
            Integer().load(MISSING)
        assert exc_info.value.messages == Integer.default_error_messages['required']

    def test_dumping_non_integer_value_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Integer().dump("123")
        assert exc_info.value.messages == \
            Integer.default_error_messages['invalid_type'].format(expected='integer')


class TestBoolean:
    def test_loading_boolean_value(self):
        assert Boolean().load(True) == True
        assert Boolean().load(False) == False

    def test_loading_missing_value_raises_required_error(self):
        with pytest.raises(ValidationError) as exc_info:
            Boolean().load(MISSING)
        assert exc_info.value.messages == Boolean.default_error_messages['required']

    def test_loading_None_raises_required_error(self):
        with pytest.raises(ValidationError) as exc_info:
            Boolean().load(None)
        assert exc_info.value.messages == Boolean.default_error_messages['required']

    def test_loading_non_boolean_value_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Boolean().load("123")
        assert exc_info.value.messages == \
            Boolean.default_error_messages['invalid_type'].format(expected='boolean')

    def test_loading_does_not_raise_ValidationError_if_validators_succeed(self):
        assert Boolean(validate=[constant_succeed_validator(),
                                 constant_succeed_validator()]).load(True) == True

    def test_loading_raises_ValidationError_if_validator_fails(self):
        message1 = 'Something went wrong'
        with pytest.raises(ValidationError) as exc_info:
            Boolean(validate=constant_fail_validator(message1)).load(True)
        assert exc_info.value.messages == message1

    def test_loading_raises_ValidationError_with_combined_messages_if_multiple_validators_fail(self):
        message1 = 'Something went wrong 1'
        message2 = 'Something went wrong 2'
        with pytest.raises(ValidationError) as exc_info:
            Boolean(validate=[constant_fail_validator(message1),
                              constant_fail_validator(message2)]).load(True)
        assert exc_info.value.messages == merge_errors(message1, message2)

    def test_dumping_boolean_value(self):
        assert Boolean().dump(True) == True
        assert Boolean().dump(False) == False

    def test_dumping_missing_value_raises_required_error(self):
        with pytest.raises(ValidationError) as exc_info:
            Boolean().load(MISSING)
        assert exc_info.value.messages == Boolean.default_error_messages['required']

    def test_dumping_None_raises_required_error(self):
        with pytest.raises(ValidationError) as exc_info:
            Boolean().load(MISSING)
        assert exc_info.value.messages == Boolean.default_error_messages['required']

    def test_dumping_non_boolean_value_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Boolean().dump("123")
        assert exc_info.value.messages == \
            Boolean.default_error_messages['invalid_type'].format(expected='boolean')


class TestList:
    def test_loading_list_value(self):
        assert List(String()).load(['foo', 'bar', 'baz']) == ['foo', 'bar', 'baz']

    def test_loading_missing_value_raises_required_error(self):
        with pytest.raises(ValidationError) as exc_info:
            List(String()).load(MISSING)
        assert exc_info.value.messages == List.default_error_messages['required']

    def test_loading_None_raises_required_error(self):
        with pytest.raises(ValidationError) as exc_info:
            List(String()).load(None)
        assert exc_info.value.messages == List.default_error_messages['required']

    def test_loading_non_list_value_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            List(String()).load('1, 2, 3')
        assert exc_info.value.messages == \
            List.default_error_messages['invalid_type'].format(expected='list')

    def test_loading_list_value_with_items_of_incorrect_type_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            List(String()).load([1, '2', 3])
        message = List.default_error_messages['invalid_type'].format(expected='string')
        assert exc_info.value.messages == {0: message, 2: message}

    def test_loading_list_value_with_items_that_have_validation_errors_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            List(Integer(validate=is_odd_validator())).load([1, 2, 3])
        assert exc_info.value.messages == {1: 'Value should be odd'}

    def test_loading_does_not_raise_ValidationError_if_validators_succeed(self):
        assert List(String(), validate=[constant_succeed_validator(),
                                        constant_succeed_validator()])\
            .load(['1', '2', '3']) == ['1', '2', '3']

    def test_loading_raises_ValidationError_if_validator_fails(self):
        message = 'Something went wrong'
        with pytest.raises(ValidationError) as exc_info:
            List(String(), validate=constant_fail_validator(message))\
                .load(['foo', 'bar'])
        assert exc_info.value.messages == message

    def test_loading_raises_ValidationError_with_combined_messages_if_multiple_validators_fail(self):
        message1 = 'Something went wrong 1'
        message2 = 'Something went wrong 2'
        with pytest.raises(ValidationError) as exc_info:
            List(String(), validate=[constant_fail_validator(message1),
                                     constant_fail_validator(message2)])\
                .load(['foo', 'bar'])
        assert exc_info.value.messages == merge_errors(message1, message2)

    def test_loading_does_not_validate_whole_list_if_items_have_errors(self):
        message1 = 'Something went wrong'
        def validate(value):
            validate.called += 1
        validate.called = 0
        with pytest.raises(ValidationError) as exc_info:
            List(Integer(validate=is_odd_validator()),
                 validate=[constant_fail_validator(message1)]).load([1, 2, 3])
        assert validate.called == 0

    def test_dumping_list_value(self):
        assert List(String()).dump(['foo', 'bar', 'baz']) == ['foo', 'bar', 'baz']

    def test_dumping_missing_value_raises_required_error(self):
        with pytest.raises(ValidationError) as exc_info:
            List(String()).dump(MISSING)
        assert exc_info.value.messages == List.default_error_messages['required']

    def test_dumping_missing_value_raises_required_error(self):
        with pytest.raises(ValidationError) as exc_info:
            List(String()).dump(None)
        assert exc_info.value.messages == List.default_error_messages['required']

    def test_dumping_non_list_value_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            List(String()).dump('1, 2, 3')
        assert exc_info.value.messages == \
            List.default_error_messages['invalid_type'].format(expected='list')

    def test_dumping_list_value_with_items_of_incorrect_type_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            List(String()).dump([1, '2', 3])
        message = List.default_error_messages['invalid_type'].format(expected='string')
        assert exc_info.value.messages == {0: message, 2: message}


class TestDict:
    def test_loading_dict_with_values_of_the_same_type(self):
        assert Dict(Integer()).load({'foo': 123, 'bar': 456}) == \
            {'foo': 123, 'bar': 456}

    def test_loading_dict_with_values_of_different_types(self):
        value = {'foo': 1, 'bar': 'hello', 'baz': True}
        assert Dict({'foo': Integer(), 'bar': String(), 'baz': Boolean()})\
            .load(value) == value

    def test_loading_missing_value_raises_required_error(self):
        with pytest.raises(ValidationError) as exc_info:
            Dict(Integer()).load(MISSING)
        assert exc_info.value.messages == Dict.default_error_messages['required']

    def test_loading_None_raises_required_error(self):
        with pytest.raises(ValidationError) as exc_info:
            Dict(Integer()).load(None)
        assert exc_info.value.messages == Dict.default_error_messages['required']

    def test_loading_non_dict_value_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Dict(Integer()).load(['1', '2'])
        assert exc_info.value.messages == \
            Dict.default_error_messages['invalid_type'].format(expected='dict')

    def test_loading_dict_with_items_of_incorrect_type_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Dict(Integer()).load({'foo': 1, 'bar': '2'})
        message = Dict.default_error_messages['invalid_type'].format(expected='integer')
        assert exc_info.value.messages == {'bar': message}

    def test_loading_dict_with_items_that_have_validation_errors_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Dict(Integer(validate=is_odd_validator())).load({'foo': 1, 'bar': 2})
        assert exc_info.value.messages == {'bar': 'Value should be odd'}

    def test_loading_does_not_raise_ValidationError_if_validators_succeed(self):
        assert Dict(Integer(), validate=[constant_succeed_validator(),
                                         constant_succeed_validator()])\
            .load({'foo': 1, 'bar': 2}) == {'foo': 1, 'bar': 2}

    def test_loading_raises_ValidationError_if_validator_fails(self):
        message = 'Something went wrong'
        with pytest.raises(ValidationError) as exc_info:
            Dict(Integer(), validate=constant_fail_validator(message))\
                .load({'foo': 1, 'bar': 2})
        assert exc_info.value.messages == message

    def test_loading_raises_ValidationError_with_combined_messages_if_multiple_validators_fail(self):
        message1 = 'Something went wrong 1'
        message2 = 'Something went wrong 2'
        with pytest.raises(ValidationError) as exc_info:
            Dict(Integer(), validate=[constant_fail_validator(message1),
                                      constant_fail_validator(message2)])\
                .load({'foo': 1, 'bar': 2})
        assert exc_info.value.messages == merge_errors(message1, message2)

    def test_loading_does_not_validate_whole_list_if_items_have_errors(self):
        message1 = 'Something went wrong'
        def validate(value):
            validate.called += 1
        validate.called = 0
        with pytest.raises(ValidationError) as exc_info:
            Dict(Integer(validate=is_odd_validator()),
                 validate=[constant_fail_validator(message1)]).load([1, 2, 3])
        assert validate.called == 0

    def test_dumping_dict_with_values_of_the_same_type(self):
        assert Dict(Integer()).dump({'foo': 123, 'bar': 456}) == \
            {'foo': 123, 'bar': 456}

    def test_dumping_dict_with_values_of_different_types(self):
        value = {'foo': 1, 'bar': 'hello', 'baz': True}
        assert Dict({'foo': Integer(), 'bar': String(), 'baz': Boolean()})\
            .load(value) == value

    def test_dumping_missing_value_raises_required_error(self):
        with pytest.raises(ValidationError) as exc_info:
            Dict(Integer()).dump(MISSING)
        assert exc_info.value.messages == Dict.default_error_messages['required']

    def test_dumping_missing_value_raises_required_error(self):
        with pytest.raises(ValidationError) as exc_info:
            Dict(String()).dump(None)
        assert exc_info.value.messages == Dict.default_error_messages['required']

    def test_dumping_non_dict_value_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Dict(()).dump('1, 2, 3')
        assert exc_info.value.messages == \
            Dict.default_error_messages['invalid_type'].format(expected='dict')

    def test_dumping_dict_with_items_of_incorrect_type_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Dict(Integer()).dump({'foo': 1, 'bar': '2'})
        message = Dict.default_error_messages['invalid_type'].format(expected='integer')
        assert exc_info.value.messages == {'bar': message}


class SpyType(Type):
    def load(self, data):
        self.loaded = data
        return data

    def dump(self, value):
        self.dumped = value
        return value


class AttributeDummy:
    foo = 'hello'
    bar = 123


class TestAttributeField:
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


class MethodDummy:
    def foo(self):
        return 'hello'

    def bar(self):
        return 123

    baz = 'goodbye'


class TestMethodField:
    def test_loading_always_returns_missing(self):
        assert MethodField(SpyType(), 'foo')\
            .load('foo', {'foo': 'hello', 'bar': 123}) == MISSING

    def test_dumping_result_of_given_objects_method(self):
        assert MethodField(SpyType(), 'foo')\
            .dump('foo', MethodDummy()) == MethodDummy().foo()

    def test_dumping_result_of_objects_method_with_field_type(self):
        field_type = SpyType()
        assert MethodField(field_type, 'foo').dump('foo', MethodDummy())
        assert field_type.dumped == MethodDummy().foo()

    def test_dumping_result_of_a_different_obejcts_method(self):
        assert MethodField(SpyType(), method='bar')\
            .dump('foo', MethodDummy()) == MethodDummy().bar()

    def test_dumping_raises_ValueError_if_given_method_does_not_exist(self):
        with pytest.raises(ValueError):
            MethodField(SpyType()).dump('bam', MethodDummy())

    def test_dumping_raises_ValueError_if_given_method_is_not_callable(self):
        with pytest.raises(ValueError):
            MethodField(SpyType(), method='baz').dump('foo', MethodDummy())


class TestFunctionField:
    def test_loading_always_returns_missing(self):
        assert FunctionField(SpyType(), lambda name, obj: getattr(obj, name))\
            .load('foo', {'foo': 'hello', 'bar': 123}) == MISSING

    def test_dumping_result_of_function_call(self):
        assert FunctionField(SpyType(), lambda name, obj: getattr(obj, name))\
            .dump('foo', AttributeDummy()) == AttributeDummy().foo

    def test_dumping_result_of_objects_method_with_field_type(self):
        field_type = SpyType()
        FunctionField(field_type, lambda name, obj: getattr(obj, name))\
            .dump('foo', AttributeDummy())
        assert field_type.dumped == AttributeDummy().foo


class TestConstantField:
    def test_loading_always_returns_missing(self):
        assert ConstantField(SpyType(), 42)\
            .load('foo', {'foo': 'hello', 'bar': 123}) == MISSING

    def test_dumping_always_returns_given_value(self):
        assert ConstantField(SpyType(), 42)\
            .dump('foo', AttributeDummy()) == 42

    def test_dumping_given_constant_with_field_type(self):
        field_type = SpyType()
        ConstantField(field_type, 42).dump('foo', AttributeDummy())
        assert field_type.dumped == 42


class AlwaysMissingType(Type):
    def load(self, data):
        return MISSING

    def dump(self, value):
        return MISSING


class AlwaysInvalidType(Type):
    def __init__(self, error_message='Invalid'):
        super(AlwaysInvalidType, self).__init__()
        self.error_message = error_message

    def load(self, data):
        raise ValidationError(self.error_message)

    def dump(self, value):
        raise ValidationError(self.error_message)


class SpyField(Field):
    def load(self, name, data):
        self.loaded = (name, data)
        return data

    def dump(self, name, obj):
        self.dumped = (name, obj)
        return obj


class TestObject:
    def test_loading_dict_value(self):
        assert Object({'foo': String(), 'bar': Integer()})\
            .load({'foo': 'hello', 'bar': 123}) == {'foo': 'hello', 'bar': 123}

    def test_loading_missing_value_raises_required_error(self):
        with pytest.raises(ValidationError) as exc_info:
            Object({'foo': String(), 'bar': Integer()}).load(MISSING)
        assert exc_info.value.messages == Object.default_error_messages['required']

    def test_loading_None_raises_required_error(self):
        with pytest.raises(ValidationError) as exc_info:
            Object({'foo': String(), 'bar': Integer()}).load(None)
        assert exc_info.value.messages == Object.default_error_messages['required']

    def test_loading_non_dict_values_raises_ValidationError(self):
        with pytest.raises(ValidationError) as exc_info:
            Object({'foo': String(), 'bar': Integer()}).load(['hello', 123])
        assert exc_info.value.messages == \
            Object.default_error_messages['invalid_type'].format(expected='dict')

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

    def test_loading_does_not_raise_ValidationError_if_validators_succeed(self):
        assert Object({'foo': String(), 'bar': Integer()},
                      validate=[constant_succeed_validator(),
                                constant_succeed_validator()])\
            .load({'foo': 'hello', 'bar': 2}) == {'foo': 'hello', 'bar': 2}

    def test_loading_raises_ValidationError_if_validator_fails(self):
        message = 'Something went wrong'
        with pytest.raises(ValidationError) as exc_info:
            Object({'foo': String(), 'bar': Integer()},
                   validate=constant_fail_validator(message))\
                .load({'foo': 'hello', 'bar': 2})
        assert exc_info.value.messages == message

    def test_loading_raises_ValidationError_with_combined_messages_if_multiple_validators_fail(self):
        message1 = 'Something went wrong 1'
        message2 = 'Something went wrong 2'
        with pytest.raises(ValidationError) as exc_info:
            Object({'foo': String(), 'bar': Integer()},
                   validate=[constant_fail_validator(message1),
                             constant_fail_validator(message2)])\
                .load({'foo': 'hello', 'bar': 2})
        assert exc_info.value.messages == merge_errors(message1, message2)

    def test_loading_calls_field_load_passing_field_name_and_whole_data(self):
        foo_field = SpyField(String())
        bar_field = SpyField(Integer())
        data = {'foo': 'hello', 'bar': 123}
        Object({'foo': foo_field, 'bar': bar_field}).load(data)
        assert foo_field.loaded == ('foo', data)
        assert bar_field.loaded == ('bar', data)

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

    def test_dumping_object_attributes(self):
        MyData = namedtuple('MyData', ['foo', 'bar'])
        assert Object({'foo': String(), 'bar': Integer()})\
            .dump(MyData('hello', 123)) == {'foo': 'hello', 'bar': 123}

    def test_dumping_missing_value_raises_required_error(self):
        with pytest.raises(ValidationError) as exc_info:
            Object({'foo': String(), 'bar': Integer()}).dump(MISSING)
        assert exc_info.value.messages == Object.default_error_messages['required']

    def test_dumping_None_raises_required_error(self):
        with pytest.raises(ValidationError) as exc_info:
            Object({'foo': String(), 'bar': Integer()}).dump(None)
        assert exc_info.value.messages == Object.default_error_messages['required']

    def test_dumping_calls_field_dump_passing_field_name_and_whole_object(self):
        foo_field = SpyField(String())
        bar_field = SpyField(Integer())
        MyData = namedtuple('MyData', ['foo', 'bar'])
        obj = MyData('hello', 123)
        Object({'foo': foo_field, 'bar': bar_field}).dump(obj)
        assert foo_field.dumped == ('foo', obj)
        assert bar_field.dumped == ('bar', obj)
