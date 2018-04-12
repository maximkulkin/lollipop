Changelog
---------

1.1.7 (2018-04-12)
++++++++++++++++++

* Fix Dict missing keys validation on load which resulted in multiple errors
* Fix missing Modifier export

1.1.6 (2018-01-25)
++++++++++++++++++

* Change List to not accept strings (as lists of one char strings)
* Fix DictWithDefault values() method not conforming to Mapping API
* Fix numeric types validation to not accept stringified numbers
* Improve documentation on how to customize error messages
* Fix missing IndexField export
* Fix load_into handling DumpOnly fields
* Simplify Type APIs by removing args and kwargs

1.1.5 (2017-06-26)
++++++++++++++++++

* Add support for loading extra attributes for Objects
* Update Dict to require presence of fixed keys
* Add IndexField to extract data from dict-like objects

1.1.4 (2017-06-08)
++++++++++++++++++

* Add support for serializing sequences and mappings other than list and dict
* Change Tuple type to return tuples on load()

1.1.3 (2017-05-10)
++++++++++++++++++

* Fix exports for Date, Time and DateTime types
* Update Object type default constructor to return object-like value

1.1.2 (2017-03-28)
++++++++++++++++++

* Make all builtin validators context-aware
* Make validators part of public type interface
* Fix repr for Length validator

1.1.1 (2017-03-07)
++++++++++++++++++

* Add "name" and "description" fields to types
* Updated modifier types to proxy unknown attributes to inner types

1.1 (2017-02-07)
++++++++++++++++

* Improved repr() for type objects to allow figuring out schema by just printing it
* Updated Dict type to allow transforming/validating dictionary keys
* Fixed/updated custom type documentation

1.0.4 (2017-02-02)
++++++++++++++++++

* Fix Transform type not being exported
  (thanks to Vladimir Bolshakov <https://github.com/vovanbo>)
* Declare support for Python 3.6
  (thanks to Vladimir Bolshakov <https://github.com/vovanbo>)

1.0.3 (2016-12-18)
++++++++++++++++++

* Add validated_type to list of exported functions
* Fix context awareness for manually added validators

1.0.2 (2016-11-29)
++++++++++++++++++

* Improved callbacks performance by prebaking context awareness

1.0.1 (2016-11-27)
++++++++++++++++++

* Fixed broken object resolved field caching thus improving performance

1.0 (2016-09-26)
++++++++++++++++

* Added inheritance of Object type settings (e.g. constructors, allow_extra_fields, etc.)
* Added support for ordering Object type attributes
* Updated Optional to support generating load_default/dump_default values instead of
  using fixed values. E.g. you can have your "id" field to default to auto-generated UUID.
* Added type registry with delayed type resolving. This allows having types that
  reference each other (e.g. Person being author to multiple Books and Book having
  author)
* Updated Object only/exclude to not affect own fields
* Added Transform modifier type
* Added validated_type() function to simplify creation of new types that are actually
  just existing type with an extra validator(s).
* Fixed Object.load_into processing of None values
* Fixed Object.load_into not annotating errors with field names
* Fixed typos in Tuple type, added tests

0.3 (2016-08-23)
++++++++++++++++

* Bugfixes and documentation improvements.
* Added Unique and Each list validators.
* Added support for calculated attribute/method names in AttributeField and MethodField.
* Added support for updating objects in-place.
* Converted ConstantField to Constant type modifier.

0.2 (2016-08-11)
++++++++++++++++

* Added object schema inheritance: objects can inherit fields from other objects.
* Added support for customizing error messages in Fields.
* Changed ConstantField to validate value to be the same on load.
* Added OneOf type to express polymorphic types or type alternatives.

0.1 (2016-07-28)
++++++++++++++++

* Initial release.
