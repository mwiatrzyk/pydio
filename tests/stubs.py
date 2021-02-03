# ---------------------------------------------------------------------------
# tests/stubs.py
#
# Copyright (C) 2021 Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
#
# This file is part of PyDio library and is released under the terms of the
# MIT license: http://opensource.org/licenses/mit-license.php.
#
# See LICENSE.txt for details.
# ---------------------------------------------------------------------------
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
