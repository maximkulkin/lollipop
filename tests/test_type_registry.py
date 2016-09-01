import pytest
from lollipop.types import Type
from lollipop.type_registry import TypeRegistry


class SpyType(Type):
    def load(self, data, context=None):
        self.loaded = data

    def dump(self, value, context=None):
        self.dumped = value


class TestTypeRegistry:
    def test_storing_and_getting_type(self):
        my_type = SpyType()
        registry = TypeRegistry()
        registry.add('type1', my_type)
        registry.get('type1').load('foo')
        assert my_type.loaded == 'foo'

    def test_getting_type_before_storing(self):
        registry = TypeRegistry()
        my_type = registry.get('type1')
        registry.add('type1', SpyType())

        my_type.load('foo')
        assert my_type.loaded == 'foo'

    def test_raising_KeyError_if_using_unknown_type(self):
        registry = TypeRegistry()
        my_type = registry.get('type1')

        with pytest.raises(KeyError):
            my_type.load('foo')

    def test_raising_ValueError_if_adding_type_that_already_exists(self):
        registry = TypeRegistry()
        registry.add('type1', SpyType())
        with pytest.raises(ValueError):
            registry.add('type1', SpyType())

    def test_getting_type_via_getitem(self):
        my_type = SpyType()
        registry = TypeRegistry()
        registry.add('type1', my_type)
        registry['type1'].load('foo')
        assert my_type.loaded == 'foo'
