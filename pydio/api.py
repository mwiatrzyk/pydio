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
"""A module containing aliases to most commonly used classes.

Use this if you don't want to import directly from submodules or if you want
to have single-line import statements inside your code.
"""
from .injector import Injector
from .provider import Provider
from .variant import Variant

__all__ = [
    'Injector',
    'Provider',
    'Variant',
]
