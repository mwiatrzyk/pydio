.. image:: https://img.shields.io/pypi/v/PyDio   :alt: PyPI
.. image:: https://img.shields.io/pypi/l/PyDio   :alt: PyPI - License
.. image:: https://img.shields.io/pypi/dm/PyDio   :alt: PyPI - Downloads
.. image:: https://codecov.io/gl/zef1r/pydio/branch/master/graph/badge.svg?token=6EVGTI0KZ0

=====
PyDio
=====

A simple and functional dependency injection toolkit for Python.

About
=====

Dependency injection in Python is basically map lookup; you need **a key**
that will point you to either **an object** to be injected or **an object factory**
to be used to create object to be injected.

PyDio is designed to follow that simple assumption: it uses **providers**
that are sort of key-to-factory maps, and **injectors** that are used by
application to search for a factory to use.

Key features:

* Support for any hashable keys: classes, strings, ints etc.
* Support for any type of object factories: function, coroutine, generator,
  asynchronous generator.
* Automatic resource management via generator-based factories
  (similar to pytest's fixtures)
* Multiple environment support: testing, development, production etc.
* Limiting created object's lifetime to custom-defined scopes: global,
  application, use-case etc.
* No singletons used == no global state.

Installation
============

You can install PyDio using one of following methods:

1) From PyPI (only official releases)::

    $ pip install PyDio

2) From test PyPI (official + development releases)::

    $ pip install -i https://test.pypi.org/simple/ PyDio

3) Directly from source code repository (for not yet released versions)::

    $ pip install git+https://gitlab.com/zef1r/PyDio.git@[branch-or-tag]

Quickstart
==========

TBD

In the meantime, you can read functional tests: https://gitlab.com/zef1r/pydio/-/tree/master/tests/functional

License
=======

This project is released under the terms of the MIT license.

See ``LICENSE.txt`` for more details.

Author
======

Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
