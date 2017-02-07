from lollipop.compat import iteritems, string_types


__all__ = [
    'SCHEMA',
    'ValidationError',
    'ValidationErrorBuilder',
    'merge_errors',
]


#: Name of an error key for cases when you have both errors for the object and
#: for it's fields::
#:
#:     {'field1': 'Field error', '_schema': 'Whole object error'}
SCHEMA = '_schema'

MISSING_ERROR_MESSAGE = \
    'Error message "{error_key}" in class {class_name} does not exist'


class ValidationError(Exception):
    """Exception to report validation errors.

    Examples of valid error messages: ::

        raise ValidationError('Error')
        raise ValidationError(['Error 1', 'Error 2'])
        raise ValidationError({
            'field1': 'Error 1',
            'field2': {'subfield1': ['Error 2', 'Error 3']}
        })

    :param messages: Validation error messages. String, list of strings or dict
        where keys are nested fields and values are error messages.
    """
    def __init__(self, messages):
        super(ValidationError, self).__init__('Invalid data: %r' % messages)
        # TODO: normalize messages
        self.messages = messages


class ErrorMessagesMixin(object):
    def __init__(self, error_messages=None, *args, **kwargs):
        super(ErrorMessagesMixin, self).__init__(*args, **kwargs)
        self._error_messages = {}
        for cls in reversed(self.__class__.__mro__):
            self._error_messages.update(getattr(cls, 'default_error_messages', {}))
        self._error_messages.update(error_messages or {})

    def _fail(self, error_key, **kwargs):
        if error_key not in self._error_messages:
            msg = MISSING_ERROR_MESSAGE.format(
                class_name=self.__class__.__name__,
                error_key=error_key
            )
            raise ValueError(msg)

        msg = self._error_messages[error_key]
        if isinstance(msg, str):
            msg = msg.format(**kwargs)

        raise ValidationError(msg)


def merge_errors(errors1, errors2):
    """Deeply merges two error messages. Error messages can be
    string, list of strings or dict of error messages (recursively).
    Format is the same as accepted by :exc:`ValidationError`.
    Returns new error messages.
    """
    if errors1 is None:
        return errors2
    elif errors2 is None:
        return errors1

    if isinstance(errors1, list):
        if not errors1:
            return errors2

        if isinstance(errors2, list):
            return errors1 + errors2
        elif isinstance(errors2, dict):
            return dict(
                errors2,
                **{SCHEMA: merge_errors(errors1, errors2.get(SCHEMA))}
            )
        else:
            return errors1 + [errors2]
    elif isinstance(errors1, dict):
        if isinstance(errors2, list):
            return dict(
                errors1,
                **{SCHEMA: merge_errors(errors1.get(SCHEMA), errors2)}
            )
        elif isinstance(errors2, dict):
            errors = dict(errors1)
            for k, v in iteritems(errors2):
                if k in errors:
                    errors[k] = merge_errors(errors[k], v)
                else:
                    errors[k] = v
            return errors
        else:
            return dict(
                errors1,
                **{SCHEMA: merge_errors(errors1.get(SCHEMA), errors2)}
            )
    else:
        if isinstance(errors2, list):
            return [errors1] + errors2 if errors2 else errors1
        elif isinstance(errors2, dict):
            return dict(
                errors2,
                **{SCHEMA: merge_errors(errors1, errors2.get(SCHEMA))}
            )
        else:
            return [errors1, errors2]


class ValidationErrorBuilder(object):
    """Helper class to report multiple errors.

    Example: ::

        def validate_all(data):
            builder = ValidationErrorBuilder()
            if data['foo']['bar'] >= data['baz']['bam']:
                builder.add_error('foo.bar', 'Should be less than bam')
            if data['foo']['quux'] >= data['baz']['bam']:
                builder.add_fields('foo.quux', 'Should be less than bam')
            ...
            builder.raise_errors()
    """

    def __init__(self):
        self.errors = None

    def _make_error(self, path, error):
        parts = path.split('.', 1) if isinstance(path, string_types) else [path]

        if len(parts) == 1:
            return {path: error}
        else:
            return {parts[0]: self._make_error(parts[1], error)}

    def add_error(self, path, error):
        """Add error message for given field path.

        Example: ::

            builder = ValidationErrorBuilder()
            builder.add_error('foo.bar.baz', 'Some error')
            print builder.errors
            # => {'foo': {'bar': {'baz': 'Some error'}}}

        :param str path: '.'-separated list of field names
        :param str error: Error message
        """
        self.errors = merge_errors(self.errors, self._make_error(path, error))

    def add_errors(self, errors):
        """Add errors in dict format.

        Example: ::

            builder = ValidationErrorBuilder()
            builder.add_errors({'foo': {'bar': 'Error 1'}})
            builder.add_errors({'foo': {'baz': 'Error 2'}, 'bam': 'Error 3'})
            print builder.errors
            # => {'foo': {'bar': 'Error 1', 'baz': 'Error 2'}, 'bam': 'Error 3'}

        :param str, list or dict errors: Errors to merge
        """
        self.errors = merge_errors(self.errors, errors)

    def raise_errors(self):
        """Raise :exc:`ValidationError` if errors are not empty;
        do nothing otherwise.
        """
        if self.errors:
            raise ValidationError(self.errors)
