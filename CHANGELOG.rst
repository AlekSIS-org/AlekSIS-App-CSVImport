Changelog
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog`_,
and this project adheres to `Semantic Versioning`_.

`2.0b0`_ - 2021-05-21
---------------------

Added
~~~~~

* Introduce a generic, customisable CSV importer based on import templates and field types.
* Add import templates for Pedasos (students, teachers, classes, courses, parents).

Removed
~~~~~~~

* Remove integrated support for SchILD import due to missing testing options.

`1.0a2`_ - 2019-11-11
---------------------

Fixed
~~~~~

* Handle PhoneNumberParseErrors gracefully.


`1.0a1`_ - 2019-09-17
---------------------

New features
~~~~~~~~~~~~

* Deactivate persons that are set to inactive in SchILD.

Changed
~~~~~~~

* Show number of created and deactivated persons after import.

Fixed
~~~~~

* Use bootstrap buttons everywhere.

.. _Keep a Changelog: https://keepachangelog.com/en/1.0.0/
.. _Semantic Versioning: https://semver.org/spec/v2.0.0.html

.. _1.0a1: https://edugit.org/Teckids/AlekSIS/AlekSIS-App-CSVImport/-/tags/1.0a1
.. _1.0a2: https://edugit.org/Teckids/AlekSIS/AlekSIS-App-CSVImport/-/tags/1.0a2
.. _2.0b0: https://edugit.org/Teckids/AlekSIS/AlekSIS-App-CSVImport/-/tags/2.0b0
