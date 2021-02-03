# ---------------------------------------------------------------------------
# tests/functional/test_provider_grouping.py
#
# Copyright (C) 2021 Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
#
# This file is part of PyDio library and is released under the terms of the
# MIT license: http://opensource.org/licenses/mit-license.php.
#
# See LICENSE.txt for details.
# ---------------------------------------------------------------------------
import pytest

from pydio.api import Injector, Provider
from tests.stubs import Bar, Foo, IBar, IFoo

foo_provider = Provider()
bar_provider = Provider()


@foo_provider.provides(IFoo)
def make_foo():
    return Foo()


@bar_provider.provides(IBar)
def make_bar():
    return Bar()


class TestProviderGrouping:

    @pytest.fixture
    def injector(self):
        provider = Provider()
        provider.attach(foo_provider)
        provider.attach(bar_provider)
        return Injector(provider)

    def test_injector_should_inject_properly_when_provider_grouping_is_used(
        self, injector
    ):
        assert isinstance(injector.inject(IFoo), Foo)
        assert isinstance(injector.inject(IBar), Bar)
