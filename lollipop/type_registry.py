from lollipop.types import Type


__all__ = [
    'TypeRegistry',
]


class TypeRef(Type):
    def __init__(self, get_type):
        super(TypeRef, self).__init__()
        self._get_type = get_type
        self._inner_type = None

    @property
    def inner_type(self):
        if self._inner_type is None:
            self._inner_type = self._get_type()
        return self._inner_type

    def load(self, *args, **kwargs):
        return self.inner_type.load(*args, **kwargs)

    def dump(self, *args, **kwargs):
        return self.inner_type.dump(*args, **kwargs)

    def __hasattr__(self, name):
        return hasattr(self.inner_type, name)

    def __getattr__(self, name):
        return getattr(self.inner_type, name)


class TypeRegistry(object):
    """Storage for type instances with ability to get type instance proxy with
    delayed type resolution for implementing mutual cross-references.

    Example: ::

        TYPES = TypeRegistry()

        PersonType = TYPES.add('Person', lt.Object({
            'name': lt.String(),
            'books': lt.List(lt.Object(TYPES['Book'], exclude='author')),
        }, constructor=Person))

        BookType = TYPES.add('Book', lt.Object({
            'title': lt.String(),
            'author': lt.Object(TYPES['Person'], exclude='books'),
        }, constructor=Book))
    """
    def __init__(self):
        super(TypeRegistry, self).__init__()
        self._types = {}

    def add(self, name, a_type):
        if name in self._types:
            raise ValueError('Type with name "%s" is already registered' % name)
        self._types[name] = a_type
        return a_type

    def _get(self, name):
        if name not in self._types:
            raise KeyError('Type with name "%s" is not registered' % name)
        return self._types[name]

    def get(self, name):
        return TypeRef(lambda: self._get(name))

    def __getitem__(self, key):
        return self.get(key)
