class Constant:

    def __init__(self, name):
        self._name = name

    def __repr__(self):
        return self._name

    def __eq__(self, other):
        return self is other

    def __ne__(self, other):
        return not self.__eq__(other)
