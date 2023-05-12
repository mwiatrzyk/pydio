# ---------------------------------------------------------------------------
# tests/functional/test_generator_based_provider.py
#
# Copyright (C) 2021 - 2023 Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
#
# This file is part of PyDio library and is released under the terms of the
# MIT license: http://opensource.org/licenses/mit-license.php.
#
# See LICENSE.txt for details.
# ---------------------------------------------------------------------------

import pytest
from mockify.actions import Raise, Return

from pydio.api import Injector, Provider


@pytest.fixture
def provider(mock):

    def make_obj():
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
    yield Injector(provider)


def test_inject_object_and_then_close_injector_explicitly(injector, mock):
    mock.begin.expect_call().will_once(Return(123))
    obj = injector.inject('obj')
    assert obj == 123
    mock.end.expect_call()
    injector.close()


def test_when_injecting_object_from_inside_context_manager_then_injector_is_closed_automatically(
    injector, mock
):
    with injector:
        mock.begin.expect_call().will_once(Return(123))
        obj = injector.inject('obj')
        assert obj == 123
        mock.end.expect_call()


def test_object_factory_function_is_called_only_once_per_injectors_lifetime(
    injector, mock
):
    retval = [1, 2, 3]
    mock.begin.expect_call().will_once(Return(retval))
    for _ in range(3):
        obj = injector.inject('obj')
        assert obj is retval


def test_when_exception_is_raised_when_under_context_manager_then_factory_is_properly_disposed(
    injector, mock
):
    exc = ValueError('an error')
    with pytest.raises(ValueError) as excinfo:
        mock.begin.expect_call().will_once(Return(123))
        with injector:
            obj = injector.inject('obj')
            assert obj == 123
            mock.failed.expect_call(exc)
            raise exc
    assert excinfo.value is exc


@pytest.mark.asyncio
async def test_properly_close_injector_when_exception_is_raised_in_teardown_phase(
    mock
):
    provider = Provider()

    @provider.provides('first')
    def make_first():
        yield 1
        mock.first.done()

    @provider.provides('second')
    def make_second():
        yield 2
        mock.second.done()

    @provider.provides('third')
    async def make_third():
        yield 3
        mock.third.done()

    with pytest.raises(ValueError) as excinfo:
        async with Injector(provider) as injector:
            assert not injector.is_closed()
            assert (injector.inject('first')) == 1
            assert (injector.inject('second')) == 2
            assert (await injector.inject('third')) == 3
            mock.first.done.expect_call().will_once(
                Raise(ValueError('an error'))
            )
            mock.second.done.expect_call()
            mock.third.done.expect_call()
    assert str(excinfo.value) == 'an error'
    assert injector.is_closed()
