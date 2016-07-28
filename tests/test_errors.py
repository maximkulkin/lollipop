from collections import namedtuple

import pytest

from lollipop.errors import ValidationError, ValidationErrorBuilder, merge_errors


CustomError = namedtuple('CustomError', ['code', 'message'])

class TestMergeErrors:

    def test_merging_none_and_string(self):
        assert 'error1' == merge_errors(None, 'error1')

    def test_merging_none_and_custom_error(self):
        assert CustomError(123, 'error1') == \
            merge_errors(None, CustomError(123, 'error1'))

    def test_merging_none_and_list(self):
        assert ['error1', 'error2'] == \
            merge_errors(None, ['error1', 'error2'])

    def test_merging_none_and_dict(self):
        assert {'field1': 'error1'} == \
            merge_errors(None, {'field1': 'error1'})

    def test_merging_string_and_none(self):
        assert 'error1' == merge_errors('error1', None)

    def test_merging_custom_error_and_none(self):
        assert CustomError(123, 'error1') == \
            merge_errors(CustomError(123, 'error1'), None)

    def test_merging_list_and_none(self):
        assert ['error1', 'error2'] == \
            merge_errors(['error1', 'error2'], None)

    def test_merging_dict_and_none(self):
        assert {'field1': 'error1'} == \
            merge_errors({'field1': 'error1'}, None)

    def test_merging_string_and_string(self):
        assert ['error1', 'error2'] == merge_errors('error1', 'error2')

    def test_merging_custom_error_and_string(self):
        assert [CustomError(123, 'error1'), 'error2'] == \
            merge_errors(CustomError(123, 'error1'), 'error2')

    def test_merging_string_and_custom_error(self):
        assert ['error1', CustomError(123, 'error2')] == \
            merge_errors('error1', CustomError(123, 'error2'))

    def test_merging_custom_error_and_custom_error(self):
        assert [CustomError(123, 'error1'), CustomError(456, 'error2')] == \
            merge_errors(CustomError(123, 'error1'), CustomError(456, 'error2'))

    def test_merging_string_and_list(self):
        assert ['error1', 'error2'] == merge_errors('error1', ['error2'])

    def test_merging_string_and_dict(self):
        assert {'_schema': 'error1', 'field1': 'error2'} == \
            merge_errors('error1', {'field1': 'error2'})

    def test_merging_string_and_dict_with_schema_error(self):
        assert {'_schema': ['error1', 'error2'], 'field1': 'error3'} == \
            merge_errors('error1', {'_schema': 'error2', 'field1': 'error3'})

    def test_merging_custom_error_and_list(self):
        assert [CustomError(123, 'error1'), 'error2'] == \
            merge_errors(CustomError(123, 'error1'), ['error2'])

    def test_merging_custom_error_and_dict(self):
        assert {'_schema': CustomError(123, 'error1'), 'field1': 'error2'} == \
            merge_errors(CustomError(123, 'error1'), {'field1': 'error2'})

    def test_merging_custom_error_and_dict_with_schema_error(self):
        assert {'_schema': [CustomError(123, 'error1'), 'error2'],
                'field1': 'error3'} == \
            merge_errors(CustomError(123, 'error1'),
                         {'_schema': 'error2', 'field1': 'error3'})

    def test_merging_list_and_string(self):
        assert ['error1', 'error2'] == merge_errors(['error1'], 'error2')

    def test_merging_list_and_custom_error(self):
        assert ['error1', CustomError(123, 'error2')] == \
            merge_errors(['error1'], CustomError(123, 'error2'))

    def test_merging_list_and_list(self):
        assert ['error1', 'error2'] == merge_errors(['error1'], ['error2'])

    def test_merging_list_and_dict(self):
        assert {'_schema': ['error1'], 'field1': 'error2'} == \
            merge_errors(['error1'], {'field1': 'error2'})

    def test_merging_list_and_dict_with_schema_error(self):
        assert {'_schema': ['error1', 'error2'], 'field1': 'error3'} == \
            merge_errors(['error1'], {'_schema': 'error2', 'field1': 'error3'})

    def test_merging_dict_and_string(self):
        assert {'_schema': 'error2', 'field1': 'error1'} == \
            merge_errors({'field1': 'error1'}, 'error2')

    def test_merging_dict_and_custom_error(self):
        assert {'_schema': CustomError(123, 'error2'), 'field1': 'error1'} == \
            merge_errors({'field1': 'error1'}, CustomError(123, 'error2'))

    def test_merging_dict_and_list(self):
        assert {'_schema': ['error2'], 'field1': 'error1'} == \
            merge_errors({'field1': 'error1'}, ['error2'])

    def test_merging_dict_and_dict(self):
        assert {'field1': 'error1',
                'field2': ['error2', 'error3'],
                'field3': 'error4'} == \
            merge_errors({'field1': 'error1', 'field2': 'error2'},
                         {'field2': 'error3', 'field3': 'error4'})

    def test_deep_merging_dicts(self):
        assert {'field1': {'field2': ['error1', 'error2']}} == \
            merge_errors({'field1': {'field2': 'error1'}},
                         {'field1': {'field2': 'error2'}})


class TestValidationErrorBuilder:

    def test_empty_errors(self):
        builder = ValidationErrorBuilder()
        assert None == builder.errors

    def test_adding_field_error(self):
        builder = ValidationErrorBuilder()
        builder.add_error('foo', 'error 1')
        assert {'foo': 'error 1'} == builder.errors

    def test_adding_multiple_errors(self):
        builder = ValidationErrorBuilder()
        builder.add_error('foo', 'error 1')
        builder.add_error('bar', 'error 2')
        builder.add_error('bam', 'error 3')
        assert {'foo': 'error 1', 'bar': 'error 2', 'bam': 'error 3'} == \
            builder.errors

    def test_adding_nested_errors(self):
        builder = ValidationErrorBuilder()
        builder.add_error('foo.bar', 'error 1')
        assert {'foo': {'bar': 'error 1'}} == builder.errors

    def test_adding_multiple_nested_errors(self):
        builder = ValidationErrorBuilder()
        builder.add_error('foo.bar', 'error 1')
        builder.add_error('foo.baz.bam', 'error 2')
        builder.add_error('quux', 'error 3')
        assert {'foo': {'bar': 'error 1', 'baz': {'bam': 'error 2'}},
                'quux': 'error 3'} == builder.errors

    def test_adding_merging_errors(self):
        builder = ValidationErrorBuilder()
        builder.add_errors({'foo': {'bar': 'error 1'}})
        builder.add_errors({'foo': {'baz': 'error 2'}})
        assert {'foo': {'bar': 'error 1', 'baz': 'error 2'}} == builder.errors

    def test_raise_errors_on_empty_builder_does_nothing(self):
        builder = ValidationErrorBuilder()
        builder.raise_errors()

    def test_raise_errors_on_non_empty_builder_raises_ValidationError(self):
        builder = ValidationErrorBuilder()
        builder.add_error('foo', 'error 1')
        with pytest.raises(ValidationError) as excinfo:
            builder.raise_errors()

        assert excinfo.value.messages == builder.errors
