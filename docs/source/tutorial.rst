.. ----------------------------------------------------------------------------
.. docs/source/tutorial.rst
..
.. Copyright (C) 2021 Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
..
.. This file is part of PyDio library documentation
.. and is released under the terms of the MIT license:
.. http://opensource.org/licenses/mit-license.php.
..
.. See LICENSE.txt for details.
.. ----------------------------------------------------------------------------

Tutorial
========

Introduction
------------

When you develop application in accordance to SOLID principles, then most
likely you start by writing use cases at first, supported by dozens of
abstractions instead of final implementations. But that abstractions have to
be implemented at some point in time. And most likely, you will have to
implement at least 2 implementations for each: one for testing/development
purposes, and one for production use. When number of use cases grows, then
number of abstractions needed grows as well. That leads to more and more
complications in configuration part of application being developed. Finally,
you find yourself in a place, where some kind of tool is needed to manage
that part of application. And PyDio is one of such tools.

