# ---------------------------------------------------------------------------
# tests/functional/test_async_generator_based_provider.py
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

provider = Provider()


@provider.provides('database')
def make_database():
    return Mock('database')


@provider.provides('connection')
async def make_connection(injector: Injector):
    database = injector.inject('database')
    connection = database.connect()
    yield connection
    connection.close()


class TestAsyncGeneratorBasedProvider:

    @pytest.fixture
    def injector(self):
        return Injector(provider)

    @pytest.mark.asyncio
    async def test_injector_should_properly_create_and_close_instances_provided_by_async_generators(
        self, injector
    ):
        connection = Mock('connection')
        database = injector.inject('database')
        database.connect.expect_call().will_once(Return(connection))
        with satisfied(database):
            assert await injector.inject('connection') is connection
        connection.close.expect_call().times(1)
        with satisfied(connection):
            await injector.close()
