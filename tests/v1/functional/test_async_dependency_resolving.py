from typing import Annotated

import pytest

from mockify.api import Return

from pydio.v1.api import ProviderLike, Provider, AsyncInjector, SupportsAsyncInject, provides

from tests.v1.functional.types import UserType, HostType, PortType, Config

ConfigPassthrough = Annotated[Config, "passthrough"]
ConfigManual = Annotated[Config, "manual"]
ConfigAuto = Annotated[Config, "auto"]


@pytest.fixture
def provider(generic_mock):
    provider = Provider()

    @provides(provider, UserType)
    def make_user():
        return generic_mock.make_user()

    @provides(provider, HostType)
    def make_host():
        return generic_mock.make_host()

    @provides(provider, PortType)
    def make_port():
        return generic_mock.make_port()

    @provides(provider, ConfigPassthrough, mode="passthrough")
    async def make_config_passthrough_sync(injector: SupportsAsyncInject):
        return Config(
            await injector.inject(UserType),
            await injector.inject(HostType),
            await injector.inject(PortType),
        )

    @provides(provider, ConfigManual, mode="manual")
    async def make_config_manual_sync(injector: SupportsAsyncInject):
        return Config(
            await injector.inject(UserType),
            await injector.inject(HostType),
            await injector.inject(PortType),
        )

    @provides(provider, ConfigAuto, mode="auto")
    async def make_config_auto_sync(user: UserType, host: HostType, port: PortType):
        return Config(user, host, port)

    return provider


@pytest.mark.parametrize(
    "typ",
    [
        ConfigPassthrough,
        ConfigManual,
        ConfigAuto,
    ],
)
async def test_inject_with_dependency_resolving(provider: ProviderLike, typ, generic_mock):
    injector = AsyncInjector(provider)
    generic_mock.make_user.expect_call().will_once(Return("root"))
    generic_mock.make_host.expect_call().will_once(Return("127.0.0.1"))
    generic_mock.make_port.expect_call().will_once(Return(8080))
    assert (await injector.inject(typ)) == Config("root", "127.0.0.1", 8080)
