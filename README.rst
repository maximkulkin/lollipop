********
lollipop
********

.. image:: https://img.shields.io/pypi/l/lollipop.svg
    :target: https://github.com/maximkulkin/lollipop/blob/master/LICENSE
    :alt: License: MIT

.. image:: https://img.shields.io/travis/maximkulkin/lollipop.svg
    :target: https://travis-ci.org/maximkulkin/lollipop
    :alt: Build Status

.. image:: https://readthedocs.org/projects/lollipop/badge/?version=latest
    :target: http://lollipop.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://img.shields.io/pypi/v/lollipop.svg
    :target: https://pypi.python.org/pypi/lollipop
    :alt: PyPI

Data serialization and validation library

.. code-block:: python

    from lollipop.types import Object, String, Date
    from lollipop.validators import Length
    from collections import namedtuple
    from datetime import date

    Person = namedtuple('Person', ['name'])
    Book = namedtuple('Book', ['title', 'publish_date', 'author'])

    PersonType = Object({
        'name': String(validate=Length(min=1)),
    }, constructor=Person)

    BookType = Object({
        'title': String(),
        'publish_date': Date(),
        'author': PersonType,
    }, constructor=Book)

    BookType.dump(
        Book(
            title='Harry Potter and the Philosopher\'s Stone',
            publish_date=date(1997, 06, 26),
            author=Person(name='J. K. Rowling')
        )
    )
    # => {'title': 'Harry Potter and the Philosopher\'s Stone',
    #     'publish_date': '1997-06-26',
    #     'author': {'name': 'J. K. Rowling'}}

    BookType.load({'title': 'Harry Potter and the Philosopher\'s Stone',
                   'publish_date': '1997-06-26',
                   'author': {'name': 'J. K. Rowling'}})
    # => Book(title='Harry Potter and the Philosopher\'s Stone',
    #         publish_date=date(1997, 06, 26),
    #         author=User(name='J. K. Rowling'))

    BookType.validate({
        'title': 'Harry Potter and the Philosopher\'s Stone',
        'author': {'name': ''},
    })
    # => {'author': {'name': 'Length should be at least 1'},
    #     'publish_date': 'Value is required'}


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
