# ---------------------------------------------------------------------------
# tests/functional/test_basics.py
#
# Copyright (C) 2021 Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
#
# This file is part of PyDio library and is released under the terms of the
# MIT license: http://opensource.org/licenses/mit-license.php.
#
# See LICENSE.txt for details.
# ---------------------------------------------------------------------------
import pytest

from pydio import exc
from pydio.api import Injector, Provider
from tests.stubs import Bar, Baz, Foo, IBar, IFoo

provider = Provider()


@provider.provides(IFoo)
def make_foo():
    return Foo()


@provider.provides(IBar)
def make_bar():
    return Bar()


@provider.provides('baz')
def make_baz(injector: Injector):
    return Baz(foo=injector.inject(IFoo), bar=injector.inject(IBar))


class TestBasics:

    @pytest.fixture
    def injector(self):
        return Injector(provider)

    def test_injector_should_inject_expected_object(self, injector):
        assert isinstance(injector.inject(IFoo), Foo)

    def test_injector_should_always_inject_same_instance(self, injector):
        assert injector.inject(IFoo) is injector.inject(IFoo)

    def test_injector_should_raise_exception_if_invalid_key_was_given(
        self, injector
    ):
        with pytest.raises(Injector.NoProviderFoundError):
            injector.inject('dummy')

    def test_injector_can_perform_nested_injections_if_needed(self, injector):
        baz = injector.inject('baz')
        assert isinstance(baz, Baz)
        assert isinstance(baz.foo, Foo)
        assert isinstance(baz.bar, Bar)

    def test_injector_can_no_longer_be_used_after_close(self, injector):
        injector.close()
        with pytest.raises(exc.AlreadyClosedError):
            injector.inject(IFoo)
