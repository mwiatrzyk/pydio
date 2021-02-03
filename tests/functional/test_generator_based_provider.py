# ---------------------------------------------------------------------------
# tests/functional/test_generator_based_provider.py
#
# Copyright (C) 2021 Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
#
# This file is part of PyDio library and is released under the terms of the
# MIT license: http://opensource.org/licenses/mit-license.php.
#
# See LICENSE.txt for details.
# ---------------------------------------------------------------------------
from typing import Hashable

import pytest
from mockify.core import satisfied
from mockify.mock import Mock

from pydio.api import Injector, Provider
from tests.stubs import Foo, IFoo

provider = Provider()


@provider.provides('startup')
@provider.provides('teardown')
def make_startup(key: Hashable):
    return Mock(key)


@provider.provides(IFoo)
def make_foo(injector: Injector, key: Hashable):
    startup = injector.inject('startup')
    teardown = injector.inject('teardown')
    startup()
    yield Foo()
    teardown()


class TestGeneratorBasedProvider:

    @pytest.fixture
    def injector(self):
        return Injector(provider)

    def test_injector_should_inject_proper_object(self, injector):
        startup = injector.inject('startup')
        startup.expect_call().times(1)
        with satisfied(startup):
            assert isinstance(injector.inject(IFoo), Foo)

    def test_injector_should_always_inject_same_instance(self, injector):
        startup = injector.inject('startup')
        startup.expect_call().times(1)
        with satisfied(startup):
            first = injector.inject(IFoo)
        second = injector.inject(IFoo)
        assert first is second

    def test_when_injector_gets_closed_then_underlying_generator_proceeds_to_cleanup_phase(
        self, injector
    ):
        self.test_injector_should_always_inject_same_instance(injector)
        teardown = injector.inject('teardown')
        teardown.expect_call().times(1)
        with satisfied(teardown):
            injector.close()

    def test_use_injector_as_context_manager(self, injector):
        teardown = injector.inject('teardown')
        teardown.expect_call()
        with satisfied(teardown):
            with injector:
                startup = injector.inject('startup')
                startup.expect_call().times(1)
                with satisfied(startup):
                    injector.inject(IFoo)
