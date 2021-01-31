import abc


class IObject:

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class IFoo(IObject):
    pass


class Foo(IFoo):
    pass


class IBar(IObject):
    pass


class Bar(IBar):
    pass


class Baz(IObject):
    pass
