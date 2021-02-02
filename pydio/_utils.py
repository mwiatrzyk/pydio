import itertools
import collections.abc

_next_id = itertools.count()


class Constant(collections.abc.Hashable):

    def __init__(self, name):
        self._id = next(_next_id)
        self._name = name

    def __repr__(self):
        return self._name

    def __hash__(self):
        return hash((self._id, self._name))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and\
            self._id == other._id and\
            self._name == other._name

    def __ne__(self, other):
        return not self.__eq__(other)
