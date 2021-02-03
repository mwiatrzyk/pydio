# ---------------------------------------------------------------------------
# tests/functional/test_coroutine_based_provider.py
#
# Copyright (C) 2021 Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
#
# This file is part of PyDio library and is released under the terms of the
# MIT license: http://opensource.org/licenses/mit-license.php.
#
# See LICENSE.txt for details.
# ---------------------------------------------------------------------------
import pytest
from mockify.actions import Return
from mockify.core import satisfied
from mockify.mock import Mock

from pydio.api import Injector, Provider
from tests.stubs import Foo, IFoo

provider = Provider()


@provider.provides('database')
def make_database():
    return Mock('database')


@provider.provides(IFoo)
async def make_foo():
    return Foo()


@provider.provides('connection')
def make_connection(injector: Injector):  # pylint: disable=redefined-outer-name
    db = injector.inject('database')
    connection = db.connect()
    yield connection
    connection.close()


class TestCoroutineBasedProvider:

    @pytest.fixture
    def injector(self):
        return Injector(provider)

    @pytest.mark.asyncio
    async def test_injector_should_properly_inject_coroutine_based_provider(
        self, injector
    ):
        obj = await injector.inject(IFoo)
        assert isinstance(obj, Foo)

    @pytest.mark.asyncio
    async def test_when_async_injectors_present_then_injector_close_becomes_a_coroutine(
        self, injector
    ):
        connection = Mock('connection')
        database = injector.inject('database')
        database.connect.expect_call().will_once(Return(connection))
        with satisfied(database):
            assert injector.inject('connection') is connection
        connection.close.expect_call().times(1)
        with satisfied(connection):
            await injector.close()
