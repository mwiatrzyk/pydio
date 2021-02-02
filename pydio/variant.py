import itertools
import collections.abc

from typing import Hashable


class Variant(collections.abc.Hashable):

    def __init__(self, key: Hashable, *args: Hashable, **kwargs: Hashable):
        self._key = key
        self._args = args
        self._kwargs = kwargs

    @property
    def key(self):
        return self._key

    @property
    def args(self):
        return self._args

    @property
    def kwargs(self):
        return self._kwargs

    def __repr__(self):
        return "<Variant(key={self._key!r}, args={self._args!r}, kwargs={self._kwargs!r})>".format(self=self)

    def __hash__(self):
        return hash(frozenset(itertools.chain([self._key], self._args, self._kwargs.items())))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and\
            self._key == other._key and\
            self._args == other._args and\
            self._kwargs == other._kwargs

    def __ne__(self, other):
        return not self.__eq__(other)
