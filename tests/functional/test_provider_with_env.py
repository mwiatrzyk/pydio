# ---------------------------------------------------------------------------
# tests/functional/test_provider_with_env.py
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
from mockify.actions import Return
from mockify.mock import Mock

from pydio.api import Injector, Provider
from tests.stubs import IFoo

provider = Provider()


@provider.provides('mock')
def make_mock():
    return Mock('mock')


@provider.provides(IFoo)
def make_default_foo(injector: Injector, key: Hashable):
    return injector.inject('mock').make_default_foo(key)


@provider.provides(IFoo, env='testing')
def make_testing_foo(injector: Injector, key: Hashable, env: Hashable):
    return injector.inject('mock').make_testing_foo(key, env=env)


@provider.provides(IFoo, env='production')
def make_production_foo(injector: Injector, key: Hashable, env: Hashable):
    return injector.inject('mock').make_production_foo(key, env=env)


class TestProviderWithEnv:

    @pytest.fixture
    def default(self):
        return Injector(provider)

    @pytest.fixture
    def testing(self):
        return Injector(provider, env='testing')

    @pytest.fixture
    def production(self):
        return Injector(provider, env='production')

    def test_default_injector_will_inject_using_default_factory(self, default):
        mock = default.inject('mock')
        mock.make_default_foo.expect_call(IFoo).will_once(Return(42))
        assert default.inject(IFoo) == 42

    def test_testing_injector_will_inject_using_testing_factory(self, testing):
        mock = testing.inject('mock')
        mock.make_testing_foo.expect_call(IFoo,
                                          env='testing').will_once(Return(42))
        assert testing.inject(IFoo) == 42

    def test_production_injector_will_inject_using_production_factory(
        self, production
    ):
        mock = production.inject('mock')
        mock.make_production_foo.expect_call(IFoo, env='production').will_once(
            Return(42)
        )
        assert production.inject(IFoo) == 42

    def test_injector_with_non_existing_env_will_fall_back_to_default_factory(
        self
    ):
        injector = Injector(provider, env='not_existing')
        mock = injector.inject('mock')
        mock.make_default_foo.expect_call(IFoo).will_once(Return(42))
        assert injector.inject(IFoo) == 42
