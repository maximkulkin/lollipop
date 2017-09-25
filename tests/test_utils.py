from lollipop.compat import iterkeys, itervalues, iteritems
from lollipop.utils import call_with_context, to_camel_case, to_snake_case, \
    constant, identity, OpenStruct, DictWithDefault
import pytest


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


class TestOpenStruct:
    def test_getting_values(self):
        o = OpenStruct({'foo': 'hello', 'bar': 123})
        assert o['foo'] == 'hello'
        assert o['bar'] == 123

    def test_getting_nonexisting_values_raises_KeyError(self):
        o = OpenStruct({'foo': 'hello', 'bar': 123})

        with pytest.raises(KeyError):
            x = o['baz']

    def test_setting_values(self):
        o = OpenStruct({'foo': 'hello'})
        o['foo'] = 'goodbye'
        o['bar'] = 111

        assert o['foo'] == 'goodbye'
        assert o['bar'] == 111

    def test_contains(self):
        o = OpenStruct({'foo': 'hello'})

        assert 'foo' in o
        assert 'bar' not in o

        o['bar'] = 123

        assert 'foo' in o
        assert 'bar' in o

    def test_deleting_values(self):
        o = OpenStruct({'foo': 'hello'})

        del o['foo']
        assert 'foo' not in o

        o['bar'] = 123
        del o['bar']
        assert 'bar' not in o

    def test_deleting_nonexisting_values_raises_KeyError(self):
        o = OpenStruct({'foo': 'hello'})

        with pytest.raises(KeyError):
            del o['bar']

    def test_keys(self):
        assert sorted(OpenStruct().keys()) == []

        o = OpenStruct({'foo': 1, 'bar': 2})
        assert sorted(o.keys()) == sorted(['foo', 'bar'])

        o['baz'] = 2
        assert sorted(o.keys()) == sorted(['foo', 'bar', 'baz'])

    def test_values(self):
        assert sorted(OpenStruct().values()) == []

        o = OpenStruct({'foo': 123})
        assert sorted(o.values()) == sorted([123])

        o['bar'] = 456
        assert sorted(o.values()) == sorted([123, 456])

    def test_items(self):
        assert sorted(OpenStruct().items()) == []

        o = OpenStruct({'foo': 'hello'})
        assert sorted(o.items()) == sorted([('foo', 'hello')])

        o['bar'] = 123
        assert sorted(o.items()) == sorted([('foo', 'hello'), ('bar', 123)])

    def test_iterkeys(self):
        assert sorted(iterkeys(OpenStruct())) == []

        o = OpenStruct({'foo': 123})
        assert sorted(iterkeys(o)) == sorted(o.keys())

        o['bar'] = 456
        assert sorted(iterkeys(o)) == sorted(o.keys())

    def test_itervalues(self):
        assert sorted(itervalues(OpenStruct())) == []

        o = OpenStruct({'foo': 'hello'})
        assert sorted(itervalues(o)) == sorted(o.values())

        o['bar'] = 'howdy'
        assert sorted(itervalues(o)) == sorted(o.values())

    def test_iteritems(self):
        assert sorted(iteritems(OpenStruct())) == []

        o = OpenStruct({'foo': 'hello'})
        assert sorted(iteritems(o)) == sorted(o.items())

        o['bar'] = 123
        assert sorted(iteritems(o)) == sorted(o.items())

    def test_length(self):
        assert len(OpenStruct()) == 0

        o = OpenStruct({'foo': 'hello'})
        assert len(o) == 1

        o['bar'] = 123
        assert len(o) == 2

    def test_iter(self):
        assert [x for x in OpenStruct()] == []

        o = OpenStruct({'foo': 'hello'})
        assert sorted([x for x in o]) == sorted(o.keys())

        o['bar'] = 123
        assert sorted([x for x in o]) == sorted(o.keys())

    def test_hasattr(self):
        o = OpenStruct({'foo': 'hello'})
        o['bar'] = 123

        assert hasattr(o, 'foo')
        assert hasattr(o, 'bar')
        assert not hasattr(o, 'baz')

    def test_getattr(self):
        o = OpenStruct({'foo': 'hello'})
        o['bar'] = 123

        assert o.foo == 'hello'
        assert o.bar == 123

    def test_getattr_on_nonexisting_key_raises_AttributeError(self):
        o = OpenStruct({'foo': 'hello'})

        with pytest.raises(AttributeError):
            x = o.baz

    def test_setattr(self):
        o = OpenStruct({'foo': 'hello'})

        o.foo = 'goodbye'
        o.bar = 123

        assert o.foo == 'goodbye'
        assert o.bar == 123
        assert o['foo'] == o.foo
        assert o['bar'] == o.bar

    def test_delattr(self):
        o = OpenStruct({'foo': 'hello'})
        o['bar'] = 123

        del o.foo
        assert not hasattr(o, 'foo')

        del o.bar
        assert not hasattr(o, 'bar')

    def test_delattr_on_nonexisting_key_raises_AttributeError(self):
        o = OpenStruct()

        with pytest.raises(AttributeError):
            del o.foo


class TestDictWithDefault:
    def test_getitem(self):
        d = DictWithDefault({'foo': 'hello', 'bar': '123'})
        assert d['foo'] == 'hello'
        assert d['bar'] == '123'

    def test_getitem_default(self):
        d = DictWithDefault({'foo': 'hello'}, default=123)
        assert d['bar'] == 123

    def test_setitem(self):
        d = DictWithDefault({'foo': 'hello'})
        assert 'bar' not in d
        d['bar'] = '123'
        assert 'bar' in d
        assert d['bar'] == '123'

    def test_delitem(self):
        d = DictWithDefault({'foo': 'hello', 'bar': 123})
        assert 'bar' in d
        del d['bar']
        assert 'bar' not in d

    def test_len(self):
        assert len(DictWithDefault({'a': 1, 'b': 5})) == 2
        assert len(DictWithDefault(default=3)) == 0
        assert len(DictWithDefault({'a': 1, 'b': 5}, default=3)) == 2

    def test_iter(self):
        assert sorted(list(DictWithDefault({'a': 1, 'b': 2}))) == ['a', 'b']

    def test_contains(self):
        d = DictWithDefault({'a': 1, 'b': 2})
        assert 'a' in d
        assert 'b' in d
        assert 'c' not in d

    def test_contains_with_default(self):
        d = DictWithDefault({'a': 1, 'b': 2}, default=123)
        assert 'a' in d
        assert 'b' in d
        assert 'c' not in d

    def test_keys(self):
        assert sorted(DictWithDefault({'a': 1, 'b': 2}).keys()) == ['a', 'b']

    def test_values(self):
        assert sorted(DictWithDefault({'a': 1, 'b': 2}).values()) == [1, 2]

    def test_get(self):
        assert DictWithDefault().get('foo') == None
        assert DictWithDefault(default=123).get('foo') == 123

    def test_get_with_custom_default(self):
        assert DictWithDefault().get('foo', 'hello') == 'hello'
        assert DictWithDefault(default=123).get('foo', 'hello') == 'hello'
