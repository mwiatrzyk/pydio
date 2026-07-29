"""Module containing injector types."""

from __future__ import annotations

import threading
from types import TracebackType
from typing import Any, Literal

from pydio.v1 import _export_list, cast
from pydio.v1.exc import IncompatibleFactoryProvidedError, InjectorClosedError
from pydio.v1.interface import T, EnvType, InjectorLike, ScopeType, SupportsRequireFactory, ResourceDisposerLike

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
    ) -> Literal[False]:
        self.__dispose_all(exc_type, exc, tb)
        return False

    def __dispose_all(
        self,
        exc_type: type[BaseException] | None = None,
        exc: BaseException | None = None,
        tb: TracebackType | None = None,
    ):
        if self.__closed:
            return
        with self.__lock:
            for _, disposer in self.__cache.values():
                disposer.dispose(exc_type, exc, tb)
            for scoped_injector in self.__scoped.values():
                scoped_injector.__dispose_all(exc_type, exc, tb)
            self.__closed = True

    def __assert_not_closed(self):
        if self.__closed:
            raise InjectorClosedError(self)

    def scoped(self, name: str) -> "InjectorLike":
        self.__assert_not_closed()
        with self.__lock:
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
            found_factory = self.__provider.require_factory(typ, scope=self.__scope, env=self.__env)
            narrowed_factory = cast.as_resource_factory(found_factory, typ)
            if narrowed_factory is None:
                raise IncompatibleFactoryProvidedError(self, found_factory)
            obj, disposer = narrowed_factory.create(self)
            self.__cache[typ] = (obj, disposer)
            return obj

    def close(self) -> None:
        self.__dispose_all()


@export
class AsyncInjector:
    pass
