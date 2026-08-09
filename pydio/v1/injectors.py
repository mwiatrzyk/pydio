"""Module containing injector types."""

from __future__ import annotations

import asyncio
import threading
from types import TracebackType
from typing import Any

from pydio.v1 import _export_list
from pydio.v1.async_backends.asyncio import AsyncioBackend
from pydio.v1.exc import DuplicateScopeError, IncompatibleFactoryProvidedError, InjectorClosedError
from pydio.v1.interface import (
    T,
    AsyncBackendLike,
    AsyncInjectorLike,
    AsyncResourceDisposerLike,
    EnvType,
    InjectorLike,
    ScopeType,
    SupportsRequireFactory,
    ResourceDisposerLike,
    is_async_resource_disposer,
    is_async_resource_factory,
)

__all__ = export = _export_list.ExportList()  # type: ignore


@export
class Injector:
    def __init__(self, provider: SupportsRequireFactory, *, scope: ScopeType = ScopeType(), env: EnvType = None):
        self.__provider = provider
        self.__scope = scope
        self.__env = env
        self.__cache: dict[Any, tuple[Any, ResourceDisposerLike]] = {}
        self.__scoped: dict[str, "Injector"] = {}
        self.__lock = threading.RLock()
        self.__closed = False

    def __enter__(self) -> "InjectorLike":
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None
    ) -> None:
        self.close(exc_type, exc, tb)

    def __assert_not_closed(self):
        if self.__closed:
            raise InjectorClosedError(self)

    def scoped(self, name: str) -> "InjectorLike":
        self.__assert_not_closed()
        with self.__lock:
            if name in self.__scoped:
                raise DuplicateScopeError(
                    (
                        *self.__scope,
                        name,
                    )
                )
            injector = self.__class__(self.__provider, scope=(*self.__scope, name), env=self.__env)
            self.__scoped[name] = injector
            return injector

    def is_closed(self) -> bool:
        return self.__closed

    def inject(self, typ: type[T] | Any) -> T:
        self.__assert_not_closed()
        cached = self.__cache.get(typ)
        if cached is not None:
            return cached[0]
        with self.__lock:
            cached = self.__cache.get(typ)
            if cached is not None:
                return cached[0]
            factory = self.__provider.require_factory(typ, scope=self.__scope, env=self.__env)
            if is_async_resource_factory(factory, typ):
                raise IncompatibleFactoryProvidedError(self, factory)
            obj, disposer = factory.create(self)
            self.__cache[typ] = (obj, disposer)
            return obj

    def close(
        self,
        exc_type: type[BaseException] | None = None,
        exc: BaseException | None = None,
        tb: TracebackType | None = None,
        /,
    ) -> None:
        if self.__closed:
            return
        with self.__lock:
            for _, disposer in self.__cache.values():
                disposer.dispose(exc_type, exc, tb)
            for scoped_injector in self.__scoped.values():
                scoped_injector.close(exc_type, exc, tb)
            self.__closed = True


@export
class AsyncInjector:
    def __init__(
        self,
        provider: SupportsRequireFactory,
        *,
        scope: ScopeType = ScopeType(),
        env: EnvType = None,
        async_backend: AsyncBackendLike | None = None,
    ):
        self.__provider = provider
        self.__scope = scope
        self.__env = env
        self.__async_backend: AsyncBackendLike = async_backend or AsyncioBackend()
        self.__cache: dict[Any, tuple[Any, ResourceDisposerLike | AsyncResourceDisposerLike]] = {}
        self.__scoped: dict[str, "AsyncInjector"] = {}
        self.__lock = self.__async_backend.create_rlock()
        self.__closed = False

    async def __aenter__(self) -> "AsyncInjectorLike":
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None
    ) -> None:
        await self.close(exc_type, exc, tb)

    def __assert_not_closed(self):
        if self.__closed:
            raise InjectorClosedError(self)

    def scoped(self, name: str) -> "AsyncInjectorLike":
        self.__assert_not_closed()
        if name in self.__scoped:
            raise DuplicateScopeError(
                (
                    *self.__scope,
                    name,
                )
            )
        child = self.__class__(
            self.__provider, scope=(*self.__scope, name), env=self.__env, async_backend=self.__async_backend
        )
        self.__scoped[name] = child
        return child

    async def inject(self, typ: type[T] | Any) -> T:
        self.__assert_not_closed()
        cached = self.__cache.get(typ)
        if cached is not None:
            return cached[0]
        async with self.__lock:
            cached = self.__cache.get(typ)
            if cached is not None:
                return cached[0]
            found_factory = self.__provider.require_factory(typ, scope=self.__scope, env=self.__env)
            if is_async_resource_factory(found_factory, typ):
                obj, async_disposer = await found_factory.create(self)
                self.__cache[typ] = (obj, async_disposer)
                return obj
            obj, disposer = found_factory.create(self)
            self.__cache[typ] = (obj, disposer)
            return obj

    def is_closed(self) -> bool:
        return self.__closed

    async def close(
        self,
        exc_type: type[BaseException] | None = None,
        exc: BaseException | None = None,
        tb: TracebackType | None = None,
        /,
    ) -> None:
        if self.__closed:
            return
        async with self.__lock:
            for _, disposer in self.__cache.values():
                if is_async_resource_disposer(disposer):
                    await disposer.dispose(exc_type, exc, tb)
                else:
                    disposer.dispose(exc_type, exc, tb)
            for scoped_injector in self.__scoped.values():
                await scoped_injector.close(exc_type, exc, tb)
            self.__closed = True
