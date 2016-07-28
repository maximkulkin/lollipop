from lollipop.errors import ValidationError, ErrorMessagesMixin
from lollipop.compat import string_types
from lollipop.utils import call_with_context
import re


class Validator(ErrorMessagesMixin, object):
    """Base class for all validators.

    Validator is used by types to validate data during deserialization. Validator
    class should define `__call__` method with either one or two arguments. In both
    cases, first argument is value being validated. In case of two arguments, the
    second one is the context. If given value fails validation, `__call__` method
    should raise :exc:`~lollipop.errors.ValidationError`. Return value is always
    ignored.
    """

    def __call__(self, value, context=None):
        """Validate value. In case of errors, raise
        :exc:`~lollipop.errors.ValidationError`. Return value is always ignored.
        """
        raise NotImplemented()


class Predicate(Validator):
    """Validator that succeeds if given predicate returns True.

    :param callable predicate: Predicate that takes value and returns True or False.
        One- and two-argument predicates are supported. First argument in both cases
        is value being validated. In case of two arguments, the second one is
        context.
    :param str error: Error message in case of validation error.
        Can be interpolated with ``data``.
    """

    default_error_messages = {
        'invalid': 'Invalid data',
    }

    def __init__(self, predicate, error=None, **kwargs):
        super(Predicate, self).__init__(**kwargs)
        self.predicate = predicate
        if error is not None:
            self._error_messages['invalid'] = error
        self.error = error

    def __call__(self, value, context=None):
        if not call_with_context(self.predicate, context, value):
            self._fail('invalid', data=value)

    def __repr__(self):
        return '<{klass} predicate={predicate} error={error}>'.format(
            klass=self.__class__.__name__,
            predicate=self.predicate, error=self.error,
        )


class Range(Validator):
    """Validator that checks value is in given range.

    :param int min: Minimum length. If not provided, minimum won't be checked.
    :param int max: Maximum length. If not provided, maximum won't be checked.
    :param str error: Error message in case of validation error.
        Can be interpolated with ``data``, ``min`` or ``max``.
    """

    default_error_messages = {
        'min': 'Value should be at least {min}',
        'max': 'Value should be at most {max}',
        'range': 'Value should be at least {min} and at most {max}',
    }

    def __init__(self, min=None, max=None, **kwargs):
        super(Range, self).__init__(**kwargs)
        self.min = min
        self.max = max

    def _fail(self, key, **kwargs):
        super(Range, self)._fail(key, min=self.min, max=self.max, **kwargs)

    def __call__(self, value):
        if self.min is not None and self.max is not None:
            if value < self.min or value > self.max:
                self._fail('range', data=value)
        elif self.min is not None:
            if value < self.min:
                self._fail('min', data=value)
        elif self.max is not None:
            if value > self.max:
                self._fail('max', data=value)

    def __repr__(self):
        return '<{klass} {properties}>'.format(
            klass= self.__class__.__name__,
            properties=' '.join(['%s=%s' % (k, repr(v))
                                 for k, v in iteritems({'min': self.min,
                                                        'max': self.max})
                                 if v is not None])
        )


class Length(Validator):
    """Validator that checks value length (using ``len()``) to be in given range.

    :param int exact: Exact length. If provided, ``min`` and ``max`` are not checked.
        If not provided, ``min`` and ``max`` checks are performed.
    :param int min: Minimum length. If not provided, minimum length won't be checked.
    :param int max: Maximum length. If not provided, maximum length won't be checked.
    :param str error: Error message in case of validation error.
        Can be interpolated with ``data``, ``length``, ``exact``, ``min`` or ``max``.
    """
    default_error_messages = {
        'exact': 'Length should be {exact}',
        'min': 'Length should be at least {min}',
        'max': 'Length should be at most {max}',
        'range': 'Length should be at least {min} and at most {max}',
    }

    def __init__(self, exact=None, min=None, max=None, **kwargs):
        super(Length, self).__init__(**kwargs)
        self.exact = exact
        self.min = min
        self.max = max

    def _fail(self, key, **kwargs):
        super(Length, self)._fail(key, exact=self.exact, min=self.min, max=self.max,
                                  **kwargs)

    def __call__(self, value):
        length = len(value)
        if self.exact is not None:
            if length != self.exact:
                self._fail('exact', data=value, length=length)
        elif self.min is not None and self.max is not None:
            if length < self.min or length > self.max:
                self._fail('range', data=value, length=length)
        elif self.min is not None:
            if length < self.min:
                self._fail('min', data=value, length=length)
        elif self.max is not None:
            if length > self.max:
                self._fail('max', data=value, length=length)

    def __repr__(self):
        if self.exact is not None:
            return '<{klass} exact={exact}>'.format(
                klass=self.__class__.__name__,
                exact=self.exact
            )
        else:
            super(Length, self).__repr__()


class NoneOf(Validator):
    """Validator that succeeds if ``value`` is not a member of given ``values``.

    :param iterable values: A sequence of invalid values.
    :param str error: Error message in case of validation error.
        Can be interpolated with ``data`` and ``values``.
    """

    default_error_messages = {
        'invalid': 'Invalid data',
    }

    def __init__(self, values, error=None, **kwargs):
        super(NoneOf, self).__init__(**kwargs)
        self.values = values
        if error is not None:
            self._error_messages['invalid'] = error

    def __call__(self, value):
        if value in self.values:
            self._fail('invalid', data=value, values=self.values)

    def __repr__(self):
        return '<{klass} {values}>'.format(
            klass=self.__class__.__name__,
            values=repr(self.values),
        )


class AnyOf(Validator):
    """Validator that succeeds if ``value`` is a member of given ``choices``.

    :param iterable choices: A sequence of allowed values.
    :param str error: Error message in case of validation error.
        Can be interpolated with ``data`` and ``choices``.
    """

    default_error_messages = {
        'invalid': 'Invalid choice',
    }

    def __init__(self, choices, error=None, **kwargs):
        super(AnyOf, self).__init__(**kwargs)
        self.choices = choices
        if error is not None:
            self._error_messages['invalid'] = error

    def __call__(self, value):
        if value not in self.choices:
            self._fail('invalid', data=value, choices=self.choices)

    def __repr__(self):
        return '<{klass} {choices}>'.format(
            klass=self.__class__.__name__,
            choices=repr(self.choices),
        )


class Regexp(Validator):
    """Validator that succeeds if ``value`` matches given ``regex``.

    :param str regexp: Regular expression string.
    :param int flags: Regular expression flags, e.g. re.IGNORECASE.
        Not used if regexp is not a string.
    :param str error: Error message in case of validation error.
        Can be interpolated with ``data`` and ``regexp``.
    """

    default_error_messages = {
        'invalid': 'String does not match expected pattern',
    }

    def __init__(self, regexp, flags=0, error=None, **kwargs):
        super(Regexp, self).__init__(**kwargs)
        if isinstance(regexp, string_types):
            regexp = re.compile(regexp, flags)
        self.regexp = regexp
        if error is not None:
            self._error_messages['invalid'] = error

    def __call__(self, value):
        if self.regexp.match(value) is None:
            self._fail('invalid', data=value, regexp=self.regexp.pattern)

    def __repr__(self):
        return '<{klass} {regexp}>'.format(
            klass=self.__class__.__name__,
            regexp=self.regexp.pattern,
        )
