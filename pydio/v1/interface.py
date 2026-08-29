"""Module containing interface definitions like protocols and ABCs.

Types from here are meant to be used as base classes (when ABCs are used), or
for structural typing (in case of protocols).
"""

from __future__ import annotations

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
    ["FuncResult", "AsyncFuncResult", "FuncType", "AsyncFuncType", "AnyInjector", "AnyFuncType", "ScopeType", "EnvType"]
)  # type: ignore

_unset = object()

T = TypeVar("T")

T_co = TypeVar("T_co", covariant=True)

#: Type alias representing possible return value type of the user-defined
#: synchronous factory function.
FuncResult = Union[T, Generator[T, None, None]]

#: Type alias representing possible return value type of the user-defined async
#: factory function.
AsyncFuncResult = Union[Awaitable[T], AsyncGenerator[T, None]]

#: Type alias representing supported user-defined synchronous callables.
FuncType = Callable[[Union["SupportsInject", "SupportsAsyncInject"]], FuncResult[T]]

#: Type alias representing supported user-defined async callables.
AsyncFuncType = Callable[["SupportsAsyncInject"], AsyncFuncResult[T]]

#: Type alias representing any injector.
AnyInjector = Union["SupportsInject", "SupportsAsyncInject"]

#: Type alias representing all supported user-defined factory functions.
AnyFuncType = Callable[[AnyInjector], Union[FuncResult[T], AsyncFuncResult[T]]]

#: Type representing scope.
ScopeType = tuple[str, ...]

#: Type representing environment.
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
        """Exit context manager created for this injector.

        Exiting context manager is equivalent to calling :meth:`close` with
        same argument values.

        :param exc_type:
            The type of exception object or ``None`` if no exception was
            raised.

        :param exc:
            The exception object or ``None`` if no exception was raised.

        :param tb:
            The traceback object or ``None`` if no exception was raised.
        """
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

    def close(
        self,
        exc_type: type[BaseException] | None = None,
        exc: BaseException | None = None,
        tb: TracebackType | None = None,
        /,
    ) -> None:
        """Close this injector.

        It disposes all resources created by this injector and recursively
        closes all owned scoped injectors, if any. When called from context
        manager, or when manual ``try..except`` construct was used, it can also
        receive exception information to be propagated to underlying resource
        disposers.

        This method is idempotent.

        :param exc_type:
            The exception object type or ``None`` if no exception was raised.

        :param exc:
            The exception object or ``None`` if no exception was raised.

        :param tb:
            The traceback object or ``None`` if no exception was raised.
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
        """Enter async context manager for this injector."""
        ...

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None
    ) -> None:
        """Exit async context manager created for this injector.

        Exiting context manager is equivalent to calling :meth:`close` with
        same argument values.

        :param exc_type:
            The type of exception object or ``None`` if no exception was
            raised.

        :param exc:
            The exception object or ``None`` if no exception was raised.

        :param tb:
            The traceback object or ``None`` if no exception was raised.
        """
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
        """Check if this injector is closed."""
        ...

    async def close(
        self,
        exc_type: type[BaseException] | None = None,
        exc: BaseException | None = None,
        tb: TracebackType | None = None,
        /,
    ) -> None:
        """Close this injector.

        It disposes all resources created by this injector and recursively
        closes all owned scoped injectors, if any. When called from context
        manager, or when manual ``try..except`` construct was used, it can also
        receive exception information to be propagated to underlying resource
        disposers.

        This method is idempotent.

        :param exc_type:
            The exception object type or ``None`` if no exception was raised.

        :param exc:
            The exception object or ``None`` if no exception was raised.

        :param tb:
            The traceback object or ``None`` if no exception was raised.
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


@export
class AsyncRLockLike(Protocol):
    """Interface for async recursive locks.

    This locking primitive allows the lock to be re-acquired by its owner with
    just internal recursion counter to be increased, and released when it
    reaches down to 0.
    """

    async def __aenter__(self) -> None:
        """Enter context manager and acquire the lock."""
        ...

    async def __aexit__(self, exc_type, exc, tb):
        """Exit context manager and release the lock."""
        ...

    async def acquire(self) -> None:
        """Acquire the lock.

        Following rules apply:
        - if the lock has no owner, then current task acquires it and becomes
          its owner,
        - if the lock is owned by the current task, then it re-acquires it
          without waiting,
        - if the lock is owned by another task, then the current one awaits for
          being notified when the lock gets unlocked.

        Acquiring a lock should be fair, i.e. access should be granted in
        ``acquire()`` call order.
        """
        ...

    def release(self) -> None:
        """Release the lock.

        This method must be called on exit from a critical section and as many
        times as the :meth:`acquire` was called. When the topmost ``acquire()``
        was released, then it removes the current owner and signals to other
        task (if any) that it can now acquire the lock.

        Only previously acquired lock can be released and only by the current
        owner, or otherwise :exc:`RuntimeError` is raised.
        """
        ...

    def is_locked(self) -> bool:
        """Check if this lock is locked.

        If not locked, then any task can acquire it without blocking. If
        locked, then :meth:`is_owned` can be used to check if it is the current
        task who owns the lock.
        """
        ...

    def is_owned(self) -> bool:
        """Check if this lock is owned by the current async task.

        This can be used to check if :meth:`acquire` would block or not.
        """
        ...


@export
class AsyncBackendLike(Protocol):
    """Protocol defining async backend interface required by PyDIO.

    This allows PyDIO to work with any async library for as long as this
    interface is implemented for it. Built-in implementations are defined in
    :mod:`pydio.v1.async_backends` module.
    """

    def create_rlock(self) -> AsyncRLockLike:
        """Create an async recursive lock.

        See :class:`AsyncRLockLike` for more details.
        """
        ...


@export
def is_resource_factory(obj: Any, typ: type[T] | None = None) -> TypeIs[ResourceFactoryLike[T]]:
    """Check if given object implements :class:`ResourceFactoryLike`
    protocol.

    :param obj:
        The object to check.

    :param typ:
        The type of objects that are expected to be produced by returned
        factory.

        This is optional and is only used to infer ``T``.
    """
    _utils.not_used(typ)
    return _utils.has_method(obj, "create")


@export
def is_async_resource_factory(obj: Any, typ: type[T] | Any | None = None) -> TypeIs[AsyncResourceFactoryLike[T]]:
    """Check if given object implements :class:`AsyncResourceFactoryLike`
    protocol.

    :param obj:
        The object to check.

    :param typ:
        The expected resource type.

        This is optional and is only used to infer ``T``.
    """
    _utils.not_used(typ)
    return _utils.has_coroutine_method(obj, "create")


@export
def is_async_resource_disposer(obj: Any) -> TypeIs[AsyncResourceDisposerLike]:
    """Check if given object implements :class:`AsyncResourceFactoryLike`
    protocol.

    :param obj:
        The object to check.
    """
    return _utils.has_coroutine_method(obj, "dispose")


@export
def supports_inject(obj: Any) -> TypeIs[SupportsInject]:
    """Check if given object implements :class:`SupportsInject` interface.

    :param obj:
        The object to check.
    """
    return _utils.has_method(obj, "inject")


@export
def supports_async_inject(obj: Any) -> TypeIs[SupportsAsyncInject]:
    """Check if given object implements :class:`SupportsAsyncInject` interface.

    :param obj:
        The object to check.
    """
    return _utils.has_coroutine_method(obj, "inject")
