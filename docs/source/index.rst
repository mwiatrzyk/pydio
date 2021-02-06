.. ----------------------------------------------------------------------------
.. docs/source/index.rst
..
.. Copyright (C) 2021 Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
..
.. This file is part of PyDio library documentation
.. and is released under the terms of the MIT license:
.. http://opensource.org/licenses/mit-license.php.
..
.. See LICENSE.txt for details.
.. ----------------------------------------------------------------------------

Welcome to PyDio's documentation!
=================================

.. image:: https://img.shields.io/pypi/v/PyDio
    :target: https://pypi.org/project/PyDio/
.. image:: https://img.shields.io/pypi/l/PyDio
    :target: https://pypi.org/project/PyDio/
.. image:: https://img.shields.io/pypi/dm/PyDio
    :target: https://pypi.org/project/PyDio/
.. image:: https://codecov.io/gl/zef1r/pydio/branch/master/graph/badge.svg?token=6EVGTI0KZ0
    :target: https://codecov.io/gl/zef1r/pydio

About PyDio
-----------

PyDio is a dependency injection library for Python.

It aims to be simple, yet still powerful, allowing you to feed dependencies
inside your application in a flexible way. PyDio design is based on simple
assumption, that dependency injection can be achieved using simple
**key-to-function** map, where **key** specifies **type of object** you want
to inject and **function** is a **factory** function that creates
**instances** of that type.

In PyDio, this is implemented using **providers** and **injectors**. You use
providers to configure your **key-to-function** mapping, and then you use
injectors to perform a **lookup** of a specific key and creation of the final
object.

Here's a simple example:

.. testcode::

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

.. testcode::
    :hide:

    main()

And if you now call ``main()`` function, then the output will be following:

.. testoutput::

    Hello, world!

Key features
------------

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

User's Guide
------------

.. toctree::
    :maxdepth: 3

    installation
    tutorial
    api
    changelog
    license
