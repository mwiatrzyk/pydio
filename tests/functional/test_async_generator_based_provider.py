# ---------------------------------------------------------------------------
# tests/functional/test_async_generator_based_provider.py
#
# Copyright (C) 2021 - 2023 Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
#
# This file is part of PyDio library and is released under the terms of the
# MIT license: http://opensource.org/licenses/mit-license.php.
#
# See LICENSE.txt for details.
# ---------------------------------------------------------------------------
import pytest
from mockify.actions import Return, Raise

from pydio.api import Injector, Provider


@pytest.fixture
def provider(mock):

    async def make_obj():
        value = mock.begin()
        try:
            yield value
        except Exception as e:
            mock.failed(e)
        else:
            mock.end()

    provider = Provider()
    provider.register_func('obj', make_obj)
    return provider


@pytest.fixture
def injector(provider):
    return Injector(provider)


@pytest.mark.asyncio
async def test_create_and_close_explicitly(injector, mock):
    mock.begin.expect_call().will_once(Return(123))
    obj = await injector.inject('obj')
    assert obj == 123
    mock.end.expect_call()
    await injector.close()


@pytest.mark.asyncio
async def test_create_and_close_via_context_manager(injector, mock):
    async with injector:
        mock.begin.expect_call().will_once(Return(123))
        mock.end.expect_call()
        obj = await injector.inject('obj')
        assert obj == 123


@pytest.mark.asyncio
async def test_factory_function_is_called_only_once(injector, mock):
    mock.begin.expect_call().will_once(Return(123))
    async with injector:
        mock.end.expect_call()
        for _ in range(3):
            assert (await injector.inject('obj')) == 123


@pytest.mark.asyncio
async def test_when_exception_is_raised_when_under_context_manager_then_factory_is_properly_disposed(
    injector, mock
):
    exc = ValueError('an error')
    with pytest.raises(ValueError) as excinfo:
        mock.begin.expect_call().will_once(Return(123))
        async with injector:
            obj = await injector.inject('obj')
            assert obj == 123
            mock.failed.expect_call(exc)
            raise exc
    assert excinfo.value is exc


@pytest.mark.asyncio
async def test_properly_close_injector_when_exception_is_raised_in_teardown_phase(mock):
    provider = Provider()

    @provider.provides('first')
    async def make_first():
        yield 1
        mock.first.done()

    @provider.provides('second')
    async def make_second():
        yield 2
        mock.second.done()

    @provider.provides('third')
    async def make_third():
        yield 3
        mock.third.done()

    with pytest.raises(ValueError) as excinfo:
        async with Injector(provider) as injector:
            assert not injector.is_closed()
            assert (await injector.inject('first')) == 1
            assert (await injector.inject('second')) == 2
            assert (await injector.inject('third')) == 3
            mock.first.done.expect_call().will_once(Raise(ValueError('an error')))
            mock.second.done.expect_call()
            mock.third.done.expect_call()
    assert str(excinfo.value) == 'an error'
    assert injector.is_closed()
