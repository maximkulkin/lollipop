from lollipop.utils import call_with_context, to_camel_case, to_snake_case, \
    constant, identity


class ObjMethodDummy:
    def __init__(self):
        self.args = None

    def foo(self, a, b, c):
        self.args = (a, b, c)
        return 42


class ObjCallableDummy:
    def __init__(self):
        self.args = None

    def __call__(self, a, b, c):
        self.args = (a, b, c)
        return 42


class ObjClassDummy:
    def __init__(self, a, b, c):
        self.args = (a, b, c)


class TestCallWithContext:
    def test_calls_function_with_given_arguments(self):
        class NonLocal:
            args = None

        def func(a, b, c):
            NonLocal.args = (a, b, c)
            return 42

        context = object()
        assert call_with_context(func, context, 1, 'foo', True) == 42
        assert NonLocal.args == (1, 'foo', True)

    def test_calls_function_with_extra_context_argument_if_function_accepts_more_arguments_than_given(self):
        class NonLocal:
            args = None

        def func(a, b, c):
            NonLocal.args = (a, b, c)
            return 42

        context = object()
        call_with_context(func, context, 1, 'foo')
        assert NonLocal.args == (1, 'foo', context)

    def test_calls_method_with_given_arguments(self):
        context = object()
        obj = ObjMethodDummy()
        assert call_with_context(obj.foo, context, 1, 'foo', True) == 42
        assert obj.args == (1, 'foo', True)

    def test_calls_method_with_extra_context_argument_if_function_accepts_more_arguments_than_given(self):
        context = object()
        obj = ObjMethodDummy()
        call_with_context(obj.foo, context, 1, 'foo')
        assert obj.args == (1, 'foo', context)

    def test_calls_callable_object_with_given_arguments(self):
        context = object()
        obj = ObjCallableDummy()
        assert call_with_context(obj, context, 1, 'foo', True) == 42
        assert obj.args == (1, 'foo', True)

    def test_calls_callable_object_with_extra_context_argument_if_function_accepts_more_arguments_than_given(self):
        context = object()
        obj = ObjCallableDummy()
        call_with_context(obj, context, 1, 'foo')
        assert obj.args == (1, 'foo', context)

    def test_calls_class_with_given_arguments(self):
        context = object()
        result = call_with_context(ObjClassDummy, context, 1, 'foo', True)
        assert result.args == (1, 'foo', True)

    def test_calls_class_with_extra_context_argument_if_function_accepts_more_arguments_than_given(self):
        context = object()
        result = call_with_context(ObjClassDummy, context, 1, 'foo')
        assert result.args == (1, 'foo', context)

    def test_calls_builtin_with_given_arguments(self):
        context = object()
        assert call_with_context(str, context, 123) == '123'


class TestToCamelCase:
    def test_converting_snake_case_to_camel_case(self):
        assert to_camel_case('foo_bar') == 'fooBar'
        assert to_camel_case('fooBar') == 'fooBar'
        assert to_camel_case('Foo_Bar') == 'Foo_Bar'


class TestToSnakeCase:
    def test_converting_camel_case_to_snake_case(self):
        assert to_snake_case('fooBar') == 'foo_bar'
        assert to_snake_case('foo_bar') == 'foo_bar'


class TestIdentity:
    def test_identity_returns_its_argument(self):
        assert identity(123) == 123
        assert identity('foo') == 'foo'


class TestConstant:
    def test_constant_returns_function_that_takes_any_arguments_and_always_returns_given_value(self):
        f = constant(123)
        assert f() == 123
        assert f(456) == 123
        assert f(1, 3, 5) == 123
        assert f(1, foo='bar') == 123
