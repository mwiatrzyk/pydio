from __future__ import annotations

from types import TracebackType
from typing import Any, AsyncGenerator, Awaitable, Callable, Generator

from pydio.v1.interface import AsyncResourceDisposerLike, ResourceDisposerLike, SupportsAsyncInject, SupportsInject


class ConstantFactory:
    """Factory used for creating constants.

    It always produces same object as the given one, with a constant disposer
    that does nothing.
    """

    def __init__(self, value: Any):
        self.__value = value
        self.__disposer = self._Disposer()

    def create(self, injector: SupportsInject | SupportsAsyncInject) -> tuple[Any, ResourceDisposerLike]:
        return self.__value, self.__disposer

    class _Disposer:
        def dispose(
            self,
            exc_type: type[BaseException] | None = None,
            exc: BaseException | None = None,
            tb: TracebackType | None = None,
        ):
            pass


class FunctionFactory:
    """Factory that calls given target function each time it is invoked and
    returns whatever the target function returns as produced object.

    Each call to factory may result in a different object being returned, but
    disposer remains the same at it is always a no-op for function-based
    factories.
    """

    def __init__(self, target: Callable[[SupportsInject | SupportsAsyncInject], Any]):
        self.__target = target
        self.__disposer = self._Disposer()

    def create(self, injector: SupportsInject | SupportsAsyncInject) -> tuple[Any, ResourceDisposerLike]:
        return self.__target(injector), self.__disposer

    class _Disposer:
        def dispose(
            self,
            exc_type: type[BaseException] | None = None,
            exc: BaseException | None = None,
            tb: TracebackType | None = None,
        ):
            pass


class GeneratorFactory:
    """Factory that uses given generator function to create objects.

    This kind of factory can have exactly one ``yield`` statement used instead
    of ``return`` and can be used to create objects with user-defined shutdown
    logic. For example, these kind of factories can be used to create shared
    database sessions with commit/rollback in teardown phase.

    This is similar to pytest's fixtures.
    """

    def __init__(self, target: Callable[[SupportsInject | SupportsAsyncInject], Any]):
        self.__target = target

    def create(self, injector: SupportsInject | SupportsAsyncInject) -> tuple[Any, ResourceDisposerLike]:
        gen = self.__target(injector)
        obj = next(gen)
        return obj, self._Disposer(gen)

    class _Disposer:
        def __init__(self, gen: Generator[Any, None, None]) -> None:
            self.__gen = gen

        def dispose(
            self,
            exc_type: type[BaseException] | None = None,
            exc: BaseException | None = None,
            tb: TracebackType | None = None,
        ):
            try:
                if exc_type is not None:
                    self.__gen.throw(exc_type, exc, tb)
                next(self.__gen)
                raise TypeError(f"Generator {self.__gen!r} must only yield once")
            except StopIteration:
                self.__gen.close()


class AsyncFunctionFactory:
    """Similar to :class:`FunctionFactory`, but for coroutine functions."""

    def __init__(self, target: Callable[[SupportsAsyncInject], Awaitable[Any]]):
        self.__target = target
        self.__disposer = self._Disposer()

    async def create(self, injector: SupportsAsyncInject) -> tuple[Any, AsyncResourceDisposerLike]:
        obj = await self.__target(injector)
        return obj, self.__disposer

    class _Disposer:
        async def dispose(
            self,
            exc_type: type[BaseException] | None = None,
            exc: BaseException | None = None,
            tb: TracebackType | None = None,
        ):
            pass


class AsyncGeneratorFactory:
    """Similar to :class:`GeneratorFactory`, but for async generators."""

    def __init__(self, target: Callable[[SupportsAsyncInject], AsyncGenerator[Any, None]]):
        self.__target = target

    async def create(self, injector: SupportsAsyncInject) -> tuple[Any, AsyncResourceDisposerLike]:
        gen = self.__target(injector)
        obj = await gen.__anext__()
        return obj, self._Disposer(gen)

    class _Disposer:
        def __init__(self, gen: AsyncGenerator[Any, None]):
            self.__gen = gen

        async def dispose(
            self,
            exc_type: type[BaseException] | None = None,
            exc: BaseException | None = None,
            tb: TracebackType | None = None,
        ):
            try:
                if exc_type is not None:
                    await self.__gen.athrow(exc_type, exc, tb)
                await self.__gen.__anext__()
                raise TypeError(f"Async generator {self.__gen!r} must only yield once")
            except StopAsyncIteration:
                await self.__gen.aclose()
