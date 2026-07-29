from __future__ import annotations

from typing import Any

from pydio.v1.interface import AsyncResourceDisposerLike, ResourceDisposerLike, SupportsAsyncInject, SupportsInject


class ResourceFactoryStub:
    def __init__(self, create_mock) -> None:
        self.__create_mock = create_mock

    def create(self, injector: SupportsInject | SupportsAsyncInject) -> tuple[Any, ResourceDisposerLike]:
        return self.__create_mock(injector)


class AsyncResourceFactoryStub:
    def __init__(self, create_mock) -> None:
        self.__create_mock = create_mock

    async def create(self, injector: SupportsAsyncInject) -> tuple[Any, AsyncResourceDisposerLike]:
        return self.__create_mock(injector)
