# lollipop

[![Build Status](https://travis-ci.org/maximkulkin/lollipop.svg)](https://travis-ci.org/maximkulkin/lollipop)
[![Documentation Status](https://readthedocs.org/projects/lollipop/badge/?version=latest)](http://lollipop.readthedocs.io/en/latest/?badge=latest)

Data serialization and validation library

Example

```python
from lollipop.types import Object, String, Date
from lollipop.validators import Length
from datetime import date

Person = namedtuple('Person', ['name'])
Book = namedtuple('Book', ['title', 'author'])

PersonType = Object({
    'name': String(validate=Length(min=1)),
}, constructor=Person)

BookType = Object({
    'title': String(),
    'pubish_date': Date(),
    'author': PersonType,
}, constructor=Book)

BookType.dump(
    Book(title='Moby-Dick',
         publish_date=date(1854, 11, 14),
         author=Person(name='Herman Melville'))
)
# => {'title': 'Moby-Dick',
#     'publish_date': '1854-11-14',
#     'author': {
#         'name': 'Herman Melville'
#     }}

BookType.load({'title': 'Moby-Dick', 'publish_date': '1854-11-14',
               'author': {'name': 'Herman Melville'}})
# => Book(title='Moby-Dick', publish_date=date(1854, 11, 14),
#         author=User(name='Herman Melville'))

BookType.validate({'title': 'Moby-Dick', 'author': {'name': ''}})
# => {'author': {'name': 'Length should be at least 1'},
      'publish_date': 'Value is required'}
```

## Installation

```
pip install lollipop
```

## Requirements

* Python >= 2.6 or <= 3.5

## License

MIT licensed. See the bundled [LICENSE](LICENSE) file for more details.
