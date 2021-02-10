# ---------------------------------------------------------------------------
# tests/unit/test_factories.py
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

from pydio import _factories as factories


class TestGeneratorFactory:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.uut = factories.GeneratorFactory(self.make_connection)
        self.database = Mock('database')

    def make_connection(self):
        connection = self.database.connect()
        yield connection
        connection.close()

    def test_get_instance_always_returns_same_object(self):
        connection = Mock('connection')
        self.database.connect.expect_call().will_once(Return(connection))
        with satisfied(self.database):
            assert self.uut.get_instance() is connection
            assert self.uut.get_instance() is connection

    def test_closing_generator_factory_invokes_statement_after_yield(self):
        connection = Mock('connection')
        self.database.connect.expect_call().will_once(Return(connection))
        with satisfied(self.database):
            assert self.uut.get_instance() is connection
        connection.close.expect_call().times(1)
        with satisfied(connection):
            self.uut.close()

    def test_get_instance_returns_none_if_called_after_close(self):
        self.uut.close()
        assert self.uut.get_instance() is None


class TestAsyncGeneratorFactory:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.uut = factories.AsyncGeneratorFactory(self.make_connection)
        self.database = Mock('database')

    async def make_connection(self):
        connection = self.database.connect()
        yield connection
        connection.close()

    @pytest.mark.asyncio
    async def test_get_instance_always_returns_same_object(self):
        connection = Mock('connection')
        self.database.connect.expect_call().will_once(Return(connection))
        with satisfied(self.database):
            assert await self.uut.get_instance() is connection
            assert await self.uut.get_instance() is connection

    @pytest.mark.asyncio
    async def test_closing_generator_factory_invokes_statement_after_yield(
        self
    ):
        connection = Mock('connection')
        self.database.connect.expect_call().will_once(Return(connection))
        with satisfied(self.database):
            assert await self.uut.get_instance() is connection
        connection.close.expect_call().times(1)
        with satisfied(connection):
            await self.uut.close()

    @pytest.mark.asyncio
    async def test_get_instance_returns_none_if_called_after_close(self):
        await self.uut.close()
        assert await self.uut.get_instance() is None


class TestCoroutineFactory:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.uut = factories.CoroutineFactory(self.make_dummy_object)

    async def make_dummy_object(self):
        return [42]

    @pytest.mark.asyncio
    async def test_get_instance_always_returns_same_object(self):
        first = await self.uut.get_instance()
        second = await self.uut.get_instance()
        assert first is second
        assert first == [42]

    @pytest.mark.asyncio
    async def test_get_instance_returns_none_after_close(self):
        await self.uut.close()
        assert await self.uut.get_instance() is None


class TestFunctionFactory:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.uut = factories.FunctionFactory(self.make_dummy_object)

    def make_dummy_object(self):
        return [42]

    def test_get_instance_always_returns_same_object(self):
        first = self.uut.get_instance()
        second = self.uut.get_instance()
        assert first is second
        assert first == [42]

    def test_get_instance_returns_none_after_close(self):
        self.uut.close()
        assert self.uut.get_instance() is None


class TestInstanceFactory:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.uut = factories.InstanceFactory([42])

    def test_get_instance_always_returns_same_object(self):
        assert self.uut.get_instance() is self.uut.get_instance()
        assert self.uut.get_instance() == [42]

    def test_get_instance_returns_none_after_close(self):
        self.uut.close()
        assert self.uut.get_instance() is None
