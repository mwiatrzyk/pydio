import pytest

from mockify.api import Return

from pydio.v1.api import Provider, Injector, AsyncInjector, provides

from tests.v1.functional.types import UserType, HostType, PortType, Config


@pytest.fixture
def inner_provider(generic_mock):
    user_provider = Provider()
    host_provider = Provider()
    port_provider = Provider()

    @provides(user_provider, UserType)
    def make_user():
        return generic_mock.make_user()

    @provides(host_provider, HostType)
    def make_host():
        return generic_mock.make_host()

    @provides(port_provider, PortType)
    def make_port():
        return generic_mock.make_port()

    provider = Provider()
    provider.attach(user_provider)
    provider.attach(host_provider)
    provider.attach(port_provider)
    return provider


@pytest.fixture
def config_provider():
    provider = Provider()

    @provides(provider, Config, mode="auto")
    def make_config(user: UserType, host: HostType, port: PortType):
        return Config(user, host, port)

    return provider


@pytest.fixture
def async_config_provider():
    provider = Provider()

    @provides(provider, Config, mode="auto")
    async def make_config(user: UserType, host: HostType, port: PortType):
        return Config(user, host, port)

    return provider


def test_inject_config(inner_provider: Provider, config_provider: Provider, generic_mock):
    root_provider = Provider()
    root_provider.attach(inner_provider)
    root_provider.attach(config_provider)
    injector = Injector(root_provider)
    generic_mock.make_user.expect_call().will_once(Return("root"))
    generic_mock.make_host.expect_call().will_once(Return("localhost"))
    generic_mock.make_port.expect_call().will_once(Return(9999))
    assert injector.inject(Config) == Config("root", "localhost", 9999)


async def test_async_inject_config(inner_provider: Provider, async_config_provider: Provider, generic_mock):
    root_provider = Provider()
    root_provider.attach(inner_provider)
    root_provider.attach(async_config_provider)
    injector = AsyncInjector(root_provider)
    generic_mock.make_user.expect_call().will_once(Return("root"))
    generic_mock.make_host.expect_call().will_once(Return("localhost"))
    generic_mock.make_port.expect_call().will_once(Return(9999))
    assert (await injector.inject(Config)) == Config("root", "localhost", 9999)
