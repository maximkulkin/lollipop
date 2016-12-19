Changelog
---------

1.0.3 (2016-12-18)
++++++++++++++++++

* Fixed usage of validators when you add them after type was created
* Fixed validated_type() not being public API

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
