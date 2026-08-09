import contextlib

import pytest

from mockify.api import Return, Raise

from pydio.v1.api import Provider, AsyncInjector, IncompleteClosingError, provides

from tests.v1.functional.types import HostType, PortType


async def test_error_raised_under_injector_context_manager_is_propagated_to_all_used_generator_based_factories(
    generic_mock, mode
):
    provider = Provider()

    @provides(provider, HostType, mode=mode)
    async def make_host():
        try:
            yield generic_mock.make_host()
        except Exception as e:
            generic_mock.make_host_fail(e)
        finally:
            generic_mock.make_host_done()

    @provides(provider, PortType, mode=mode)
    async def make_port():
        try:
            yield generic_mock.make_port()
        except Exception as e:
            generic_mock.make_port_fail(e)
        finally:
            generic_mock.make_port_done()

    exc = ValueError("an error")
    with contextlib.suppress(type(exc)):
        generic_mock.make_host_fail.expect_call(exc)
        generic_mock.make_port_fail.expect_call(exc)
        async with AsyncInjector(provider) as injector:
            generic_mock.make_host.expect_call().will_once(Return("localhost"))
            generic_mock.make_host_done.expect_call()
            assert (await injector.inject(HostType)) == "localhost"
            generic_mock.make_port.expect_call().will_once(Return(9999))
            generic_mock.make_port_done.expect_call()
            assert (await injector.inject(PortType)) == 9999
            raise exc


async def test_error_raised_by_factory_is_re_thrown_by_inject_and_propagated_to_all_used_generator_based_factories(
    generic_mock, mode
):
    provider = Provider()

    @provides(provider, HostType, mode=mode)
    async def make_host():
        return generic_mock.make_host()

    @provides(provider, PortType, mode=mode)
    async def make_port():
        try:
            yield 8888
        except Exception as e:
            generic_mock.make_port_fail(e)

    exc = ValueError("an error")
    with pytest.raises(type(exc), match=str(exc)):
        generic_mock.make_port_fail.expect_call(exc)
        async with AsyncInjector(provider) as injector:
            assert (await injector.inject(PortType)) == 8888
            generic_mock.make_host.expect_call().will_once(Raise(exc))
            await injector.inject(HostType)


async def test_when_generator_based_factory_throws_during_teardown_then_other_resources_are_closed_normally_and_injector_closing_ends_with_error(
    generic_mock, mode
):
    provider = Provider()

    @provides(provider, HostType, mode=mode)
    async def make_host():
        yield "localhost"
        generic_mock.make_host_done()

    @provides(provider, PortType, mode=mode)
    async def make_port():
        yield 8888
        generic_mock.make_port_done()

    exc = ValueError("an error")
    generic_mock.make_host_done.expect_call().will_once(Raise(exc))
    generic_mock.make_port_done.expect_call()
    generic_mock.all_checks_passed.expect_call()
    with pytest.raises(IncompleteClosingError) as excinfo:
        async with AsyncInjector(provider) as root:
            assert (await root.inject(HostType)) == "localhost"
            assert (await root.inject(PortType)) == 8888
            generic_mock.all_checks_passed()
    assert excinfo.value.dispose_errors == {HostType: exc}


async def test_when_several_generator_based_factories_throw_during_teardown_then_other_are_closed_normally_and_injector_closing_ends_with_error(
    generic_mock, mode
):
    provider = Provider()

    @provides(provider, HostType, mode=mode)
    async def make_host():
        yield "localhost"
        generic_mock.make_host_done()

    @provides(provider, PortType, mode=mode)
    async def make_port():
        yield 8888
        generic_mock.make_port_done()

    @provides(provider, str, mode=mode)
    async def make_dummy():
        yield "dummy"
        generic_mock.make_dummy_done()

    first = ValueError("first error")
    second = ValueError("second error")
    generic_mock.make_host_done.expect_call().will_once(Raise(first))
    generic_mock.make_port_done.expect_call().will_once(Raise(second))
    generic_mock.make_dummy_done.expect_call()
    generic_mock.all_checks_passed.expect_call()
    with pytest.raises(IncompleteClosingError) as excinfo:
        async with AsyncInjector(provider) as root:
            assert (await root.inject(HostType)) == "localhost"
            assert (await root.inject(PortType)) == 8888
            assert (await root.inject(str)) == "dummy"
            generic_mock.all_checks_passed()
    assert excinfo.value.dispose_errors == {HostType: first, PortType: second}
