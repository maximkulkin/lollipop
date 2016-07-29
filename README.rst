********
lollipop
********

.. image:: https://travis-ci.org/maximkulkin/lollipop.svg
    :target: https://travis-ci.org/maximkulkin/lollipop
    :alt: Build Status

.. image:: https://readthedocs.org/projects/lollipop/badge/?version=latest
    :target: http://lollipop.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

Data serialization and validation library

.. code-block:: python

    from lollipop.types import Object, String, Date
    from lollipop.validators import Length
    from collections import namedtuple
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


Installation
============

::

    $ pip install lollipop


Documentation
=============

Documentation is available at http://lollipop.readthedocs.io/ .


Requirements
============

- Python >= 2.6 or <= 3.5


Project Links
=============

- Documentation: http://lollipop.readthedocs.io/
- PyPI: https://pypi.python.org/pypi/lollipop
- Issues: https://github.com/maximkulkin/lollipop/issues


License
=======

MIT licensed. See the bundled `LICENSE <https://github.com/maximkulkin/lollipop/blob/master/LICENSE>`_ file for more details.
