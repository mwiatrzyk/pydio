from typing import Annotated

import pytest

from pydio.v1.api import (
    ProviderLike,
    Provider,
    Injector,
    AsyncInjector,
    provides,
    inject_annotated,
    async_inject_annotated,
)

UserNameType = Annotated[str, "username"]
HostNameType = Annotated[str, "hostname"]


@pytest.fixture
def provider():
    provider = Provider()

    @provides(provider, UserNameType)
    def make_username():
        return "root"

    @provides(provider, HostNameType)
    def make_hostname():
        return "localhost"

    return provider


def test_injector_can_inject_annotated_types(provider: ProviderLike):
    injector = Injector(provider)
    username = inject_annotated(injector, str, "username")
    hostname = inject_annotated(injector, str, "hostname")
    assert username == "root"
    assert hostname == "localhost"


async def test_async_injector_can_inject_variants(provider: ProviderLike):
    injector = AsyncInjector(provider)
    username = await async_inject_annotated(injector, str, "username")
    hostname = await async_inject_annotated(injector, str, "hostname")
    assert username == "root"
    assert hostname == "localhost"
