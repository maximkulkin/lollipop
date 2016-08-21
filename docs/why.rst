.. _why:

Why lollipop?
=============

There is so much good libraries for object serialization and validation. Why another
one? Here are few reasons.

Agnostic
--------
The library does not make any assumptions (other than standard practices in Python
development) about structure of objects being serialized/deserialized. It makes it
usable in wide variety of frameworks and applications.

Composability
-------------
The library consists of small building blocks that can be either used on their own
or be composed into a complex data definition schemas. Be it a primitive type
descriptor, a schema, validator - they all expose a small and simple interface,
which allows easy composition and extension.

Separation of responsibilities
------------------------------
As in UNIX design, all building blocks focus on their particular task and strive
to be best at it. That helps keeping interfaces simple. Type descriptors serialize
particular types and that's it: no optional values, no pre/post processing, no
dump/load-only. Everything else can be added on top of them.

It's all about objects
----------------------
All your schema is just objects composed together. No (meta)classes, decorators,
black magic. That makes it very easy to work with them, including understanding
them, extending them, writing new combinators, generating new schemas right in
runtime.

Validation
----------
Validation is one of key use cases, so flexibility for reporting errors is given
a great attention. Reporting single error, multiple errors for the same field,
reporting errors for multiple fields at the same time is possible. See
:ref:`validation` for details.

In-place updates
----------------
Most of other libraries require all fields for validation to proceed and generally
can only construct new objects ignoring use cases when users want to update existing
objects. See :ref:`inplace_updates` for more information.
