from pytest import raises
from contextlib import contextmanager
from lollipop.validators import Predicate, Range, Length, NoneOf, AnyOf, Regexp, \
    Unique, Each
from lollipop.errors import ValidationError
import re


@contextmanager
def not_raises(exception_type):
    try:
        yield
    except exception_type as err:
        raise AssertionError(
            "Did raise exception {0} when it should not!".format(
                repr(exception_type)
            )
        )
    except Exception as err:
        raise AssertionError(
            "An unexpected exception {0} raised.".format(repr(err))
        )


class TestPredicate:
    def test_matching_values(self):
        with not_raises(ValidationError):
            Predicate(lambda x: x in ['foo', 'bar', 'baz'])('foo')

        with not_raises(ValidationError):
            Predicate(lambda x: x in ['foo', 'bar', 'baz'])('bar')

    def test_raising_ValidationError_if_predicate_returns_False(self):
        with raises(ValidationError) as exc_info:
            Predicate(lambda x: x in ['foo', 'bar'])('baz')
        assert exc_info.value.messages == Predicate.default_error_messages['invalid']

    def test_customizing_validation_error(self):
        message = 'Invalid data'
        with raises(ValidationError) as exc_info:
            Predicate(lambda x: x in ['foo', 'bar'], message)('baz')
        assert exc_info.value.messages == message

    def test_passing_context_to_predicate(self):
        class NonLocal:
            context = None

        def validator(value, context=None):
            NonLocal.context = context
            return True

        my_context = object()
        Predicate(validator)('foo', my_context)
        assert NonLocal.context == my_context


class TestRange:
    def test_matching_min_value(self):
        with not_raises(ValidationError):
            Range(min=1)(1)

        with not_raises(ValidationError):
            Range(min=1)(2)

    def test_raising_ValidationError_when_matching_min_value_and_given_value_is_less(self):
        with raises(ValidationError) as exc_info:
            Range(min=1)(0)
        assert exc_info.value.messages == \
            Range.default_error_messages['min'].format(min=1)

    def test_customzing_min_error_message(self):
        message = 'Value {data} should be at least {min}'
        with raises(ValidationError) as exc_info:
            Range(min=1, error_messages={'min': message})(0)
        assert exc_info.value.messages == message.format(data=0, min=1)

    def test_matching_max_value(self):
        with not_raises(ValidationError):
            Range(max=1)(1)

        with not_raises(ValidationError):
            Range(max=1)(0)

    def test_raising_ValidationError_when_matching_max_value_and_given_value_is_greater(self):
        with raises(ValidationError) as exc_info:
            Range(max=1)(2)
        assert exc_info.value.messages == \
            Range.default_error_messages['max'].format(max=1)

    def test_customzing_max_error_message(self):
        message = 'Value {data} should be at most {max}'
        with raises(ValidationError) as exc_info:
            Range(max=1, error_messages={'max': message})(2)
        assert exc_info.value.messages == message.format(data=2, max=1)

    def test_matching_range(self):
        with not_raises(ValidationError):
            Range(min=1, max=5)(1)

        with not_raises(ValidationError):
            Range(min=1, max=5)(3)

        with not_raises(ValidationError):
            Range(min=1, max=5)(5)

    def test_raising_ValidationError_when_matching_range_and_given_value_is_less(self):
        with raises(ValidationError) as exc_info:
            Range(min=1, max=5)(0)
        assert exc_info.value.messages == \
            Range.default_error_messages['range'].format(min=1, max=5)

    def test_raising_ValidationError_when_matching_range_and_given_value_is_greater(self):
        with raises(ValidationError) as exc_info:
            Range(min=1, max=5)(6)
        assert exc_info.value.messages == \
            Range.default_error_messages['range'].format(min=1, max=5)

    def test_customzing_range_error_message(self):
        message = 'Value {data} should be between {min} and {max}'
        with raises(ValidationError) as exc_info:
            Range(min=1, max=5, error_messages={'range': message})(0)
        assert exc_info.value.messages == message.format(data=0, min=1, max=5)

    def test_customizing_all_error_messages_at_once(self):
        message = 'Value is invalid'

        with raises(ValidationError) as exc_info:
            Range(min=1, error=message)(0)
        assert exc_info.value.messages == message

        with raises(ValidationError) as exc_info:
            Range(max=1, error=message)(2) == message
        assert exc_info.value.messages == message

        with raises(ValidationError) as exc_info:
            Range(min=1, max=5, error=message)(0) == message
        assert exc_info.value.messages == message


class TestLength:
    def test_matching_exact_value(self):
        with not_raises(ValidationError):
            Length(exact=2)([1, 2])

    def test_raising_ValidationError_when_matching_exact_value_and_given_value_does_not_match(self):
        with raises(ValidationError) as exc_info:
            Length(exact=3)([1, 2])
        assert exc_info.value.messages == \
            Length.default_error_messages['exact'].format(exact=3)

    def test_customizing_exact_error_message(self):
        message = 'Value {data} length is not {exact}'
        with raises(ValidationError) as exc_info:
            Length(exact=3, error_messages={'exact': message})([1, 2])
        assert exc_info.value.messages == message.format(data=[1, 2], exact=3)

    def test_matching_min_value(self):
        with not_raises(ValidationError):
            Length(min=1)([1])

        with not_raises(ValidationError):
            Length(min=1)([1, 2])

    def test_raising_ValidationError_when_matching_min_value_and_given_value_is_less(self):
        with raises(ValidationError) as exc_info:
            Length(min=1)([])
        assert exc_info.value.messages == \
            Length.default_error_messages['min'].format(min=1)

    def test_customzing_min_error_message(self):
        message = 'Length {length} of {data} should be at least {min}'
        with raises(ValidationError) as exc_info:
            Length(min=1, error_messages={'min': message})([])
        assert exc_info.value.messages == message.format(data=[], length=0, min=1)

    def test_matching_max_value(self):
        with not_raises(ValidationError):
            Length(max=1)([1])

        with not_raises(ValidationError):
            Length(max=1)([])

    def test_raising_ValidationError_when_matching_max_value_and_given_value_is_greater(self):
        with raises(ValidationError) as exc_info:
            Length(max=1)([1, 2])
        assert exc_info.value.messages == \
            Length.default_error_messages['max'].format(max=1)

    def test_customzing_max_error_message(self):
        message = 'Length {length} of {data} should be at most {max}'
        with raises(ValidationError) as exc_info:
            Length(max=1, error_messages={'max': message})([1, 2])
        assert exc_info.value.messages == \
            message.format(data=[1, 2], length=2, max=1)

    def test_matching_range(self):
        with not_raises(ValidationError):
            Length(min=1, max=5)([1])

        with not_raises(ValidationError):
            Length(min=1, max=5)([1, 2, 3])

        with not_raises(ValidationError):
            Length(min=1, max=5)([1, 2, 3, 4, 5])

    def test_raising_ValidationError_when_matching_range_and_given_value_is_less(self):
        with raises(ValidationError) as exc_info:
            Length(min=1, max=5)([])
        assert exc_info.value.messages == \
            Length.default_error_messages['range'].format(min=1, max=5)

    def test_raising_ValidationError_when_matching_range_and_given_value_is_greater(self):
        with raises(ValidationError) as exc_info:
            Length(min=1, max=5)([1, 2, 3, 4, 5, 6])
        assert exc_info.value.messages == \
            Length.default_error_messages['range'].format(min=1, max=5)

    def test_customzing_range_error_message(self):
        message = 'Length {length} of {data} should be between {min} and {max}'
        with raises(ValidationError) as exc_info:
            Length(min=1, max=5, error_messages={'range': message})([])
        assert exc_info.value.messages == \
            message.format(data=[], length=0, min=1, max=5)

    def test_customizing_all_error_messages_at_once(self):
        message = 'Value is invalid'

        with raises(ValidationError) as exc_info:
            Length(exact=1, error=message)([])
        assert exc_info.value.messages == message

        with raises(ValidationError) as exc_info:
            Length(min=1, error=message)([])
        assert exc_info.value.messages == message

        with raises(ValidationError) as exc_info:
            Length(max=1, error=message)([1, 2]) == message
        assert exc_info.value.messages == message

        with raises(ValidationError) as exc_info:
            Length(min=1, max=5, error=message)([]) == message
        assert exc_info.value.messages == message


class TestNoneOf:
    def test_matching_values_other_than_given_values(self):
        with not_raises(ValidationError):
            NoneOf(['foo', 'bar'])('baz')

    def test_raising_ValidationError_when_value_is_one_of_forbidden_values(self):
        with raises(ValidationError) as exc_info:
            NoneOf(['foo', 'bar'])('foo')
        assert exc_info.value.messages == NoneOf.default_error_messages['invalid']

    def test_customizing_error_message(self):
        message = 'Value {data} in {values}'
        with raises(ValidationError) as exc_info:
            NoneOf(['foo', 'bar'], error=message)('foo')
        assert exc_info.value.messages == message.format(data='foo',
                                                         values=['foo', 'bar'])


class TestAnyOf:
    def test_matching_given_values(self):
        with not_raises(ValidationError):
            AnyOf(['foo', 'bar'])('foo')

        with not_raises(ValidationError):
            AnyOf(['foo', 'bar'])('bar')

    def test_raising_ValidationError_when_value_is_other_than_given_values(self):
        with raises(ValidationError) as exc_info:
            AnyOf(['foo', 'bar'])('baz')
        assert exc_info.value.messages == AnyOf.default_error_messages['invalid']

    def test_customizing_error_message(self):
        message = 'Value {data} not in {choices}'
        with raises(ValidationError) as exc_info:
            AnyOf(['foo', 'bar'], error=message)('baz')
        assert exc_info.value.messages == message.format(data='baz',
                                                         choices=['foo', 'bar'])


class TestRegexp:
    def test_matching_by_string_regexp(self):
        with not_raises(ValidationError):
            Regexp('a+b')('aaab')

    def test_matching_by_string_regexp_with_flags(self):
        with not_raises(ValidationError):
            Regexp('a+b', re.IGNORECASE)('AaAB')

    def test_matching_by_regexp(self):
        with not_raises(ValidationError):
            Regexp(re.compile('a+b'))('aab')

    def test_matching_by_regexp_ignores_flags(self):
        with raises(ValidationError):
            Regexp(re.compile('a+b'), flags=re.IGNORECASE)('AAB')

    def test_raising_ValidationError_if_given_string_does_not_match_string_regexp(self):
        with raises(ValidationError) as exc_info:
            Regexp('a+b')('bbc')
        assert exc_info.value.messages == Regexp.default_error_messages['invalid']

    def test_raising_ValidationError_if_given_string_does_not_match_regexp(self):
        with raises(ValidationError) as exc_info:
            Regexp(re.compile('a+b'))('bbc')
        assert exc_info.value.messages == Regexp.default_error_messages['invalid']

    def test_customizing_error_message(self):
        message = 'Value {data} does not match {regexp}'
        with raises(ValidationError) as exc_info:
            Regexp('a+b', error=message)('bbc')
        assert exc_info.value.messages == message.format(data='bbc', regexp='a+b')


class TestUnique:
    def test_raising_ValidationError_if_value_is_not_collection(self):
        with raises(ValidationError) as exc_info:
            Unique()('foo')
        assert exc_info.value.messages == Unique.default_error_messages['invalid']

    def test_matching_empty_collection(self):
        with not_raises(ValidationError):
            Unique()([])

    def test_matching_collection_of_unique_values(self):
        with not_raises(ValidationError):
            Unique()(['foo', 'bar', 'baz'])

    def test_matching_collection_of_values_with_unique_custom_keys(self):
        class Foo:
            def __init__(self, foo):
                self.foo = foo

        with not_raises(ValidationError):
            Unique(lambda x: x.foo)([Foo('foo'), Foo('bar'), Foo('baz')])

    def test_raising_ValidationError_if_item_appears_more_than_once(self):
        with raises(ValidationError) as exc_info:
            Unique()(['foo', 'bar', 'foo'])
        assert exc_info.value.messages == Unique.default_error_messages['unique']

    def test_raising_ValidationError_if_custom_key_appears_more_than_once(self):
        class Foo:
            def __init__(self, foo):
                self.foo = foo

        with raises(ValidationError) as exc_info:
            Unique(lambda x: x.foo)([Foo('foo'), Foo('bar'), Foo('foo')])
        assert exc_info.value.messages == Unique.default_error_messages['unique']

    def test_customizing_error_message(self):
        class Foo:
            def __init__(self, foo):
                self.foo = foo

        message = 'Invalid data {data} with key {key}'
        x = Foo('foo')
        y = Foo('foo')
        with raises(ValidationError) as exc_info:
            Unique(lambda x: x.foo, error=message)([x, y])
        assert exc_info.value.messages == message.format(data=y, key='foo')


is_odd = Predicate(lambda x: x % 2 == 1, 'Value should be odd')
is_small = Predicate(lambda x: x <= 5, 'Value should be small')


class TestEach:
    def test_raising_ValidationError_if_value_is_not_collection(self):
        with raises(ValidationError) as exc_info:
            Each(lambda x: x)('foo')
        assert exc_info.value.messages == Each.default_error_messages['invalid']

    def test_matching_empty_collections(self):
        with not_raises(ValidationError):
            Each(is_odd)([])

    def test_matching_collections_each_elemenet_of_which_matches_given_validators(self):
        with not_raises(ValidationError):
            Each([is_odd, is_small])([1, 3, 5])

    def test_raising_ValidationError_if_single_validator_fails(self):
        with raises(ValidationError) as exc_info:
            Each(is_odd)([1, 2, 3])
        assert exc_info.value.messages == {1: 'Value should be odd'}

    def test_raising_ValidationError_if_any_item_fails_any_validator(self):
        with raises(ValidationError) as exc_info:
            Each([is_odd, is_small])([1, 2, 5, 7])
        assert exc_info.value.messages == {1: 'Value should be odd',
                                           3: 'Value should be small'}
