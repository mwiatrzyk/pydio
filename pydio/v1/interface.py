"""Module containing interface definitions like protocols and ABCs.

Types from here are meant to be used as base classes (when ABCs are used), or
for structural typing (in case of protocols).
"""

from __future__ import annotations

import inspect
from types import TracebackType
from typing import (
    Any,
    AsyncGenerator,
    Awaitable,
    Callable,
    Generator,
    Generic,
    Protocol,
    TypeVar,
    Union,
)

from typing_extensions import TypeIs

from pydio.v1 import _export_list, _utils

__all__ = export = _export_list.ExportList(
    ["FuncResult", "AsyncFuncResult", "FuncType", "AsyncFuncType", "AnyFuncType", "ScopeType", "EnvType"]
)  # type: ignore

_unset = object()

T = TypeVar("T")

T_co = TypeVar("T_co", covariant=True)

#: Type alias for :obj:`FuncType` result.
FuncResult = Union[T, Generator[T, None, None]]

#: Type alias for :obj:`AsyncFuncType` result.
AsyncFuncResult = Union[Awaitable[T], AsyncGenerator[T, None]]

#: Type alias for supported user-defined callables.
FuncType = Callable[[Union["SupportsInject", "SupportsAsyncInject"]], FuncResult[T]]

#: Type alias for supported user-defined async callables.
AsyncFuncType = Callable[["SupportsAsyncInject"], AsyncFuncResult[T]]

#: Union of :obj:`FuncType` and :obj:`AsyncFuncType`.
# AnyFuncType = Union[FuncType[T], AsyncFuncType[T]]
AnyFuncType = Callable[[Union["SupportsInject", "SupportsAsyncInject"]], Union[FuncResult[T], AsyncFuncResult[T]]]

#: Type alias for scope type.
ScopeType = tuple[str, ...]

#: Type alias for environment type.
EnvType = Union[str, None]


@export
class ResourceDisposerLike(Protocol):
    """Protocol that defines the interface for the resource disposers."""

    def dispose(
        self,
        exc_type: type[BaseException] | None = None,
        exc: BaseException | None = None,
        tb: TracebackType | None = None,
    ) -> None:
        """Drop associated resource.

        :param exc_type:
            The type of exception or ``None`` if no exception.

        :param exc:
            The exception object or ``None`` if no exception.

        :param tb:
            The traceback object or ``None`` if no exception.
        """
        ...


@export
class ResourceFactoryLike(Generic[T_co], Protocol):
    """Protocol that defines resource factories.

    Each resource factory is responsible for creating resources (objects) that
    are instances of registered types.
    """

    def create(self, injector: SupportsInject | SupportsAsyncInject) -> tuple[T_co, ResourceDisposerLike]:
        """Create resource object along with associated disposer.

        The object returned is meant to be returned by injector, while disposer
        is meant to be used by injector to dispose the object on injector's
        shutdown.

        :param injector:
            The injector to use.

            This object is passed to user-defined function and can be used to
            inject resource's dependencies that are needed to create object to
            return.
        """
        ...


@export
class AsyncResourceDisposerLike(Protocol):
    """Async version of :class:`ResourceDisposer` protocol."""

    async def dispose(
        self,
        exc_type: type[BaseException] | None = None,
        exc: BaseException | None = None,
        tb: TracebackType | None = None,
    ) -> None:
        """Async version of :meth:`ResourceDisposer.dispose` method."""


@export
class AsyncResourceFactoryLike(Generic[T_co], Protocol):
    """Async version of :class:`ResourceConstructor` protocol."""

    async def create(self, injector: SupportsAsyncInject) -> tuple[T_co, AsyncResourceDisposerLike]:
        """Async version of :meth:`ResourceConstructor.construct` method."""
        ...


@export
class SupportsInject(Protocol):
    """Protocol defining non-async dependency injection interface."""

    def inject(self, typ: type[T] | Any) -> T:
        """Inject instance of given type for current scope and environment.

        :param typ:
            The type to inject.
        """
        ...


@export
class SupportsAsyncInject(Protocol):
    """Async version of :class:`SupportsInject` protocol."""

    async def inject(self, typ: type[T] | Any) -> T:
        """Async version of :meth:`SupportsInject.inject` method."""
        ...


@export
class InjectorLike(SupportsInject, Protocol):
    """Protocol defining interface for synchronous injectors.

    Injectors implementing this interface are meant to be used in non-async
    environment, with non-async resource factories only; if async one is found
    during lookup, :exc:`pydio.v1.exc.IncompatibleFactoryProvidedError` is
    raised.

    Injectors must be closed when no longer needed to invoke resource disposal
    action for all resources that were injected at least once. Closing injector
    can be done manually, by calling :meth:`close`, or automatically via
    context manager (if injector was used as a context manager).
    """

    def __enter__(self) -> "InjectorLike":
        """Enter context manager created for this injector."""
        ...

    def __exit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None
    ) -> None:
        """Exit context manager created for this injector."""
        ...

    def scoped(self, name: str) -> "InjectorLike":
        """Create a scoped injector.

        :param name:
            The name of the child scope.
        """
        ...

    def is_closed(self) -> bool:
        """Check if this injector is closed."""
        ...

    def close(self) -> None:
        """Close this injector.

        Calling this method disposes all resources and closes all scoped
        injectors that were created by this injector.
        """
        ...


@export
class AsyncInjectorLike(SupportsAsyncInject, Protocol):
    """Protocol defining interface for asynchronous injectors.

    Unlike synchronous :class:`InjectorLike`, classes that implement this
    interface can operate on both asynchronous and synchronous resource
    factories.
    """

    async def __aenter__(self) -> "AsyncInjectorLike":
        """Enter context manager for this injector."""
        ...

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None
    ) -> None:
        """Exit context manager created for this injector."""
        ...

    def scoped(self, name: str) -> "AsyncInjectorLike":
        """Create a scoped injector inside this injector.

        The created injector extends its parent's scope, so when parent
        injector's scope is ``('foo',)``, the scope of a new scoped injector,
        assuming ``'bar'`` given as a name, would become ``('foo', 'bar')``.

        :param name:
            The name to be added to current scope.
        """
        ...

    def is_closed(self) -> bool:
        """Check if this injector is closed.

        This method will return ``True`` when either of these two events
        happened:

        - :meth:`close` was called,
        - context manager created for this injector ended.
        """
        ...

    async def close(self) -> None:
        """Dispose all managed resources and close the injector.

        If this injector has scoped injectors associated, then those are closed
        as well recursively.
        """
        ...


@export
class SupportsRequireFactory(Protocol):
    """Protocol defining interface to deliver resource factories."""

    def require_factory(
        self, typ: type[T] | Any, *, scope: ScopeType = ScopeType(), env: EnvType = None
    ) -> ResourceFactoryLike[T] | AsyncResourceFactoryLike[T]:
        """Require a resource factory for given params.

        Returns async or non-async factory on successful lookup, or otherwise
        raises :exc:`pydio.v1.exc.FactoryLookupError` (or one of its subclasses)
        otherwise.

        :param typ:
            The type to look factory for.

        :param scope:
            The current scope.

        :param env:
            The current environment name.
        """
        ...


@export
class SupportsRegisterFactory(Protocol):
    """Protocol defining interface to register resource factories."""

    def register_factory(
        self,
        typ: type[T] | Any,
        factory: ResourceFactoryLike[T] | AsyncResourceFactoryLike[T],
        *,
        scope: ScopeType = ScopeType(),
        env: EnvType = None,
    ) -> None:
        """Register a resource factory for the given params.

        On success, when the factory is registered, ``None`` is returned.
        On failure, when existing factory for same type, scope and environment
        is found, :exc:`pydio.v1.exc.FactoryAlreadyExistsError` is raised.

        :param typ:
            The type to register factory for.

        :param factory:
            The factory to register for a type.

        :param scope:
            The scope to register factory in.

        :param env:
            The environment to register factory for.
        """
        ...


@export
class ProviderLike(SupportsRegisterFactory, SupportsRequireFactory, Protocol):
    """Protocol defining interface for providers.

    It combines factory registry and lookup capabilities.
    """


class AsyncLockLike(Protocol):
    """Interface for async locks."""

    async def __aenter__(self) -> None: ...

    async def __aexit__(self, exc_type, exc, tb): ...


@export
class AsyncBackendLike(Protocol):
    """Protocol defining async backend interface required by PyDIO."""

    def create_lock(self) -> AsyncLockLike:
        """Create async lock.

        Used to guard resource from simultaneous access from two different
        coroutines.
        """
        ...


@export
def is_async_resource_factory(obj: Any, typ: type[T] | None = None) -> TypeIs[AsyncResourceFactoryLike[T]]:
    """Check if given object implements :class:`AsyncResourceFactoryLike`
    protocol.

    :param obj:
        The object to check.

    :param typ:
        The expected resource type.

        This is optional and is only used to infer ``T``.
    """
    bound_create = getattr(obj, "create", _unset)
    if bound_create is _unset:
        return False
    unbound_create = type(obj).create
    _utils.not_used(typ)
    return inspect.iscoroutinefunction(unbound_create)


@export
def is_async_resource_disposer(obj: Any) -> TypeIs[AsyncResourceDisposerLike]:
    """Check if given object implements :class:`AsyncResourceFactoryLike`
    protocol.

    :param obj:
        The object to check.
    """
    bound_dispose = getattr(obj, "dispose", _unset)
    if bound_dispose is _unset:
        return False
    unbound_dispose = type(obj).dispose
    return inspect.iscoroutinefunction(unbound_dispose)
