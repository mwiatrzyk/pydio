# ---------------------------------------------------------------------------
# pydio/api.py
#
# Copyright (C) 2021 Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
#
# This file is part of PyDio library and is released under the terms of the
# MIT license: http://opensource.org/licenses/mit-license.php.
#
# See LICENSE.txt for details.
# ---------------------------------------------------------------------------
"""A module providing aliases to most common used classes.

You can use this in your code to create one-line imports. For example,
instead of doing this:

.. testcode::

    from pydio.injector import Injector
    from pydio.provider import Provider

You can do this:

.. testcode::

    from pydio.api import Injector, Provider

This is a replacement for commonly used ``from toolkit import Foo, Bar``
idiom, which is discouraged due to performance reasons.
"""
from .injector import Injector
from .provider import Provider
from .variant import Variant

__all__ = [
    'Injector',
    'Provider',
    'Variant',
]
