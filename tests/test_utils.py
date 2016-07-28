from lollipop.utils import call_with_context


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
