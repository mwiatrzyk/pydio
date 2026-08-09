import dataclasses
from typing import Annotated

import pytest

from pydio.v1.api import ProviderLike, Provider, Injector, AsyncInjector, SupportsInject, SupportsAsyncInject, provides

UserNameType = Annotated[str, "username"]
HostNameType = Annotated[str, "hostname"]
PortType = Annotated[int, "port"]


@dataclasses.dataclass
class Config:
    username: str
    hostname: str
    port: int


ConfigAutoSync = Annotated[Config, "auto", "sync"]
ConfigManualSync = Annotated[Config, "manual", "sync"]
ConfigPassthroughSync = Annotated[Config, "passthrough", "sync"]
ConfigAutoAsync = Annotated[Config, "auto", "async"]
ConfigManualAsync = Annotated[Config, "manual", "async"]
ConfigPassthroughAsync = Annotated[Config, "passthrough", "async"]


@pytest.fixture
def provider():
    provider = Provider()

    @provides(provider, UserNameType)
    def make_username():
        return "root"

    @provides(provider, HostNameType)
    def make_hostname():
        return "127.0.0.1"

    @provides(provider, PortType)
    def make_port():
        return 8080

    @provides(provider, ConfigAutoSync, mode="auto")
    def make_config_auto_sync(username: UserNameType, hostname: HostNameType, port: PortType):
        return Config(username, hostname, port)

    @provides(provider, ConfigManualSync, mode="manual")
    def make_config_manual_sync(injector: SupportsInject):
        return Config(
            injector.inject(UserNameType),
            injector.inject(HostNameType),
            injector.inject(PortType),
        )

    @provides(provider, ConfigPassthroughSync, mode="passthrough")
    def make_config_passthrough_sync(injector: SupportsInject):
        return Config(
            injector.inject(UserNameType),
            injector.inject(HostNameType),
            injector.inject(PortType),
        )

    @provides(provider, ConfigAutoAsync, mode="auto")
    async def make_config_auto_async(username: UserNameType, hostname: HostNameType, port: PortType):
        return Config(username, hostname, port)

    @provides(provider, ConfigManualAsync, mode="manual")
    async def make_config_manual_async(injector: SupportsAsyncInject):
        return Config(
            await injector.inject(UserNameType),
            await injector.inject(HostNameType),
            await injector.inject(PortType),
        )

    @provides(provider, ConfigPassthroughAsync, mode="passthrough")
    async def make_config_passthrough_async(injector: SupportsAsyncInject):
        return Config(
            await injector.inject(UserNameType),
            await injector.inject(HostNameType),
            await injector.inject(PortType),
        )

    return provider


@pytest.mark.parametrize("typ", [
    ConfigAutoSync,
    ConfigManualSync,
    ConfigPassthroughSync,
])
def test_inject_with_dependency_resolving(provider: ProviderLike, typ):
    injector = Injector(provider)
    assert injector.inject(typ) == Config("root", "127.0.0.1", 8080)


@pytest.mark.parametrize("typ", [
    ConfigAutoAsync,
    ConfigManualAsync,
    ConfigPassthroughAsync,
])
async def test_async_inject_with_dependency_resolving(provider: ProviderLike, typ):
    injector = AsyncInjector(provider)
    assert (await injector.inject(typ)) == Config("root", "127.0.0.1", 8080)
