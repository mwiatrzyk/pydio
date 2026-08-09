"""Module containing injector types."""

from __future__ import annotations

import threading
from types import TracebackType
from typing import Any

from pydio.v1 import _export_list
from pydio.v1.async_backends.asyncio import AsyncioBackend
from pydio.v1.exc import (
    ScopeAlreadyExistsError,
    IncompatibleFactoryProvidedError,
    InjectorAlreadyClosedError,
    IncompleteClosingError,
)
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
    """The synchronous injector class.

    This class implements :class:`pydio.v1.interface.InjectorLike` protocol
    and provides functionalities for creating and disposing resources using
    synchronous factories only. If the app is going to use ``async def``
    functions it is recommended to use :class:`AsyncInjector` class instead.

    When injector is created, it must receive resource factory provider which
    is used to find factories for a given type. Later, when resource object is
    created using that factory, it is cached in injector and kept until the
    injector is closed. Upon closing, injector closes all resources it created.

    Besides managing resources, each injector can also create nested injectors
    using :meth:`scoped` method. Such child injectors are also tightly coupled
    with their parent and, when parent closes, all child scoped injector are
    also closed.

    :param provider:
        The provider to use.

        It provides a stateless type-to-factory map that is used by injector to
        create resources.

    :param scope:
        The root scope for this injector.

        When this is set, the injector will only be able to access factories
        tagged with exact this scope, or its parent scope. Also, when scoped
        injectors are created via :meth:`scoped`, this scope is used as a
        parent scope for each of them.

        This defaults to root scope.

    :param env:
        The environment to use by this injector.

        Same as for scope, a matching factory, or a one with default
        environment, must exist. And, when creating scoped injectors using
        :meth:`scoped`, this exact environment is used by each scoped injector.

        This defaults to ``None``.
    """

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

    def __require_not_closed(self):
        if self.__closed:
            raise InjectorAlreadyClosedError(self)

    def scoped(self, name: str) -> "InjectorLike":
        """See :meth:`pydio.v1.interface.InjectorLike.scoped`."""
        self.__require_not_closed()
        with self.__lock:
            if name in self.__scoped:
                raise ScopeAlreadyExistsError(
                    (
                        *self.__scope,
                        name,
                    )
                )
            injector = self.__class__(self.__provider, scope=(*self.__scope, name), env=self.__env)
            self.__scoped[name] = injector
            return injector

    def is_closed(self) -> bool:
        """See :meth:`pydio.v1.interface.InjectorLike.is_closed`."""
        return self.__closed

    def inject(self, typ: type[T] | Any) -> T:
        """See :meth:`pydio.v1.interface.InjectorLike.inject`."""
        self.__require_not_closed()
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
        """See :meth:`pydio.v1.interface.InjectorLike.close`."""
        if self.__closed:
            return
        with self.__lock:
            if self.__closed:
                return
            dispose_errors = {}
            for typ, (_, disposer) in reversed(self.__cache.items()):
                try:
                    disposer.dispose(exc_type, exc, tb)
                except Exception as e:
                    dispose_errors[typ] = e
            for scoped_injector in self.__scoped.values():
                scoped_injector.close(exc_type, exc, tb)
            self.__closed = True
            if dispose_errors:
                raise IncompleteClosingError(dispose_errors)


@export
class AsyncInjector:
    """The asynchronous injector class.

    This class implements :class:`pydio.v1.interface.AsyncInjectorLike`
    protocol and provides functionalities for creating and disposing resources
    using both asynchronous and synchronous factories. The only restriction is
    that synchronous factories cannot have any dependencies set (so those must
    be a leaf dependencies), as resolving those would require calling
    asynchronous injector, which is impossible from synchronous factory.

    It is highly recommended to use this injector for apps that use ``async
    def`` functions.

    :param provider:
        See *provider* parameter of the :class:`Injector` class.

    :param scope:
        See *scope* parameter of the :class:`Injector` class.

    :param env:
        See *env* parameter of the :class:`Injector` class.

    :param async_backend:
        The async backend to use.

        This object must implement :class:`pydio.v1.interface.AsyncBackendLike`
        protocol and provide all async features that PyDIO needs to drive its
        async code. It is not needed normally, unless you are dealing with some
        sort of non-standard async library that does not play well with
        :mod:`asyncio` (which is the default here).

        The async API to implement is simple, as PyDIO tries to avoid using
        library-specific primitives and rely only on what Python provides via
        its keywords. However, some important ones (like locks) cannot be
        provided by Python on its own, and then this bridge comes into play.

        When not given, a default
        :class:`pydio.v1.async_backends.asyncio.AsyncioBackend` is used.
    """

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

    def __require_not_closed(self):
        if self.__closed:
            raise InjectorAlreadyClosedError(self)

    def scoped(self, name: str) -> "AsyncInjectorLike":
        """See :meth:`pydio.v1.interface.AsyncInjectorLike.scoped`."""
        self.__require_not_closed()
        if name in self.__scoped:
            raise ScopeAlreadyExistsError(
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
        """See :meth:`pydio.v1.interface.AsyncInjectorLike.inject`."""
        self.__require_not_closed()
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
        """See :meth:`pydio.v1.interface.AsyncInjectorLike.is_closed`."""
        return self.__closed

    async def close(
        self,
        exc_type: type[BaseException] | None = None,
        exc: BaseException | None = None,
        tb: TracebackType | None = None,
        /,
    ) -> None:
        """See :meth:`pydio.v1.interface.AsyncInjectorLike.close`."""
        if self.__closed:
            return
        async with self.__lock:
            if self.__closed:
                return
            dispose_errors = {}
            for typ, (_, disposer) in reversed(self.__cache.items()):
                try:
                    if is_async_resource_disposer(disposer):
                        await disposer.dispose(exc_type, exc, tb)
                    else:
                        disposer.dispose(exc_type, exc, tb)
                except Exception as e:
                    dispose_errors[typ] = e
            for scoped_injector in self.__scoped.values():
                await scoped_injector.close(exc_type, exc, tb)
            self.__closed = True
            if dispose_errors:
                raise IncompleteClosingError(dispose_errors)
