# ---------------------------------------------------------------------------
# tests/unit/test_injector.py
#
# Copyright (C) 2021 - 2023 Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
#
# This file is part of PyDio library and is released under the terms of the
# MIT license: http://opensource.org/licenses/mit-license.php.
#
# See LICENSE.txt for details.
# ---------------------------------------------------------------------------
import pytest
from mockify.actions import Return
from mockify.mock import ABCMock

from pydio.base import IUnboundFactoryRegistry
from pydio.injector import Injector


class TestInjectorErrors:

    def test_no_provider_found_error(self):
        uut = Injector.NoProviderFoundError(key='spam', env='testing')
        assert str(uut) == "No provider found for: key='spam', env='testing'"

    def test_out_of_scope_error(self):
        uut = Injector.OutOfScopeError(
            key='foo', scope='first', required_scope='second'
        )
        assert str(
            uut
        ) == "Cannot inject 'foo' due to scope mismatch: 'second' (required) != 'first' (owned)"


class TestInjector:

    @pytest.fixture
    def provider(self):
        return ABCMock('provider', IUnboundFactoryRegistry)

    @pytest.fixture
    def uut(self, provider):
        return Injector(provider)

    def test_create_scoped_injector_with_env(self, uut):
        app = uut.scoped('app', env='testing')
        assert app.env == 'testing'
        assert uut.env is None

    def test_when_env_is_given_to_root_injector_then_scoped_injector_cannot_be_created_with_different_env(
        self, provider
    ):
        uut = Injector(provider, env='testing')
        with pytest.raises(ValueError) as excinfo:
            uut.scoped('other', env='production')
        assert str(
            excinfo.value
        ) == "scoped() got an invalid value for parameter 'env': expected 'testing' or None, got 'production'"

    def test_scoped_injector_can_be_created_with_env_if_value_is_same_as_for_parent(
        self, provider
    ):
        uut = Injector(provider, env='testing')
        uut.scoped('app', env='testing')

    def test_scoped_injector_inherits_environment_from_parent(self, uut):
        app = uut.scoped('app', env='testing')
        other = app.scoped('other')
        assert app.env == 'testing'
        assert other.env == 'testing'
        assert uut.env is None

    def test_when_injector_is_closed_then_child_injectors_are_closed_as_well(
        self, uut, provider
    ):
        provider.has_awaitables.expect_call().will_repeatedly(Return(False))
        app = uut.scoped('app')
        uut.close()
        assert uut.is_closed()
        assert app.is_closed()

    @pytest.mark.asyncio
    async def test_when_injector_using_async_provider_is_closed_then_child_are_closed_as_well(
        self, uut, provider
    ):
        provider.has_awaitables.expect_call().will_repeatedly(Return(True))
        app = uut.scoped('app')
        await uut.close()
        assert uut.is_closed()
        assert app.is_closed()
