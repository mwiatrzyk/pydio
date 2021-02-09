# ---------------------------------------------------------------------------
# pydio/variant.py
#
# Copyright (C) 2021 Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
#
# This file is part of PyDio library and is released under the terms of the
# MIT license: http://opensource.org/licenses/mit-license.php.
#
# See LICENSE.txt for details.
# ---------------------------------------------------------------------------
import collections.abc
import itertools
from typing import Hashable


class Variant(collections.abc.Hashable):
    """A special form of key that can have user-defined parameters attached.

    This class can be used if you need to use same key twice, but return
    different objects depending on additional parameters given (which can be
    accessed by object factory)

    :param key:
        The key to be wrapped

    :param kwargs:
        Additional parameters to be bound with given key
    """

    def __init__(self, key: Hashable, **kwargs: Hashable):
        self._key = key
        self._kwargs = kwargs

    @property
    def key(self):
        """Wrapped key."""
        return self._key

    @property
    def kwargs(self) -> dict:
        """Dict containing attached parameters."""
        return self._kwargs

    def __repr__(self):
        return "<Variant(key={self._key!r}, kwargs={self._kwargs!r})>".format(
            self=self
        )

    def __hash__(self):
        return hash(
            frozenset(itertools.chain([self._key], self._kwargs.items()))
        )

    def __eq__(self, other):
        return isinstance(other, self.__class__) and\
            self._key == other._key and\
            self._kwargs == other._kwargs

    def __ne__(self, other):
        return not self.__eq__(other)
