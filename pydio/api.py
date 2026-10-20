# ---------------------------------------------------------------------------
# pydio/api.py
#
# Copyright (C) 2021 - 2025 Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
#
# This file is part of PyDIO library and is released under the terms of the
# MIT license: http://opensource.org/licenses/mit-license.php.
#
# See LICENSE.txt for details.
# ---------------------------------------------------------------------------
"""An all-in-one module for making imports easier.

You can use this in your code to create one-line imports. For example,
instead of adding multiple PyDIO imports to your application, you can do
this instead:

.. testcode::

    from pydio.api import Injector, Provider
"""

from .injector import Injector
from .keys import Variant
from .provider import Provider

__all__ = [
    "Injector",
    "Provider",
    "Variant",
]
