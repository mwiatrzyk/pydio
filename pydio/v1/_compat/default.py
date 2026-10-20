from __future__ import annotations

import collections.abc
from types import TracebackType
from typing import Annotated, Any, AsyncGenerator, Awaitable, Callable, Generator, Hashable

from pydio.v1 import _export_list

__all__ = export = _export_list.ExportList()  # type: ignore


@export
def build_annotated(typ: Hashable, *args: Any) -> Any:
    return Annotated.__class_getitem__((typ, *args))  # type: ignore


@export
def throw(
    gen: Generator, exc_type: type[BaseException], exc: BaseException | None = None, tb: TracebackType | None = None
) -> Any:
    return gen.throw(exc_type, exc, tb)


@export
async def athrow(
    gen: AsyncGenerator, exc_type: type[BaseException], exc: BaseException | None, tb: TracebackType | None = None
) -> Any:
    return await gen.athrow(exc_type, exc, tb)


@export
class AsyncGeneratorProxy(collections.abc.AsyncGenerator):
    def __init__(self, factory: Callable[[], Awaitable[AsyncGenerator]]) -> None:
        self.__factory = factory
        self.__target: AsyncGenerator | None = None

    async def __require_target(self) -> AsyncGenerator:
        # FIXME: Is there a better way of achieving this?
        if self.__target is None:
            self.__target = await self.__factory()
        return self.__target

    async def asend(self, value: None) -> Any:
        target = await self.__require_target()
        return await target.asend(value)

    async def athrow(self, typ, val=None, tb=None, /) -> Any:
        target = await self.__require_target()
        return await target.athrow(typ, val, tb)


@export
class GeneratorProxy(collections.abc.Generator):
    def __init__(self, target: Generator) -> None:
        self.__target = target

    def send(self, value: None) -> Any:
        return self.__target.send(value)

    def throw(self, typ, val=None, tb=None) -> Any:
        return self.__target.throw(typ, val, tb)
