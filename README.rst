.. image:: https://img.shields.io/pypi/v/PyDio   :alt: PyPI
.. image:: https://img.shields.io/pypi/l/PyDio   :alt: PyPI - License
.. image:: https://img.shields.io/pypi/dm/PyDio   :alt: PyPI - Downloads
.. image:: https://codecov.io/gl/zef1r/pydio/branch/master/graph/badge.svg?token=6EVGTI0KZ0
:target: https://codecov.io/gl/zef1r/pydio

=====
PyDio
=====

A simple and functional dependency injection toolkit for Python.

About
=====

PyDio aims to be as simple as possible, yet still powerful, allowing you to
feed dependencies inside your application in a flexible way. PyDio design is
based on simple assumption, that dependency injection can be achieved using
simple **key-to-function** map, where **key** specifies **type of object**
you want to inject and **function** is a **factory** function that creates
**instances** of that type.

In PyDio, this is implemented using **providers** and **injectors**. You use
providers to configure your **key-to-function** mapping, and then you use
injectors to perform a **lookup** of a specific key and creation of the final
object.

Here's a simple example::

    import abc

    from pydio.api import Provider, Injector

    provider = Provider()

    @provider.provides('greet')
    def make_greet():
        return 'Hello, world!'

    def main():
        injector = Injector(provider)
        greet_message = injector.inject('greet')
        print(greet_message)

And if you now call ``main()`` function, then the output will be following::

    Hello, world!

Key features
============

* Support for any hashable keys: class objects, strings, ints etc.
* Support for any type of object factories: function, coroutine, generator,
  asynchronous generator.
* Automatic resource management via generator-based factories
  (similar to pytest's fixtures)
* Multiple environment support: testing, development, production etc.
* Limiting created object's lifetime to user-defined scopes: global,
  application, use-case etc.
* No singletons used, so there is no global state...
* ...but you still can create global injector on your own if you need it :-)

Installation
============

You can install PyDio using one of following methods:

1) From PyPI (for stable releases)::

    $ pip install PyDio

2) From test PyPI (for stable and development releases)::

    $ pip install -i https://test.pypi.org/simple/ PyDio

3) Directly from source code repository (for all releases)::

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
