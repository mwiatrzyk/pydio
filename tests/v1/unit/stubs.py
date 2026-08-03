from __future__ import annotations

from types import TracebackType
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


class ResourceDisposerStub:
    def __init__(self, dispose_mock) -> None:
        self.__dispose_mock = dispose_mock

    def dispose(
        self,
        exc_type: type[BaseException] | None = None,
        exc: BaseException | None = None,
        tb: TracebackType | None = None,
    ) -> None:
        self.__dispose_mock(exc_type, exc, tb)
        return None


class AsyncResourceDisposerStub:
    def __init__(self, dispose_mock) -> None:
        self.__dispose_mock = dispose_mock

    async def dispose(
        self,
        exc_type: type[BaseException] | None = None,
        exc: BaseException | None = None,
        tb: TracebackType | None = None,
    ) -> None:
        self.__dispose_mock(exc_type, exc, tb)
        return None
