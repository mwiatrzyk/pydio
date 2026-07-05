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

from pydio.v1 import _export_list

__all__ = export = _export_list.ExportList(["UserFactoryType", "ScopeType", "EnvType"])  # type: ignore

T = TypeVar("T")

T_co = TypeVar("T_co", covariant=True)

#: Type alias for user callables that are registered in provider.
FuncType = Callable[
    [Union["SupportsInject", "SupportsAsyncInject"]],
    Union[T, Awaitable[T], Generator[T, None, None], AsyncGenerator[T, None]],
]

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
    ):
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
    ):
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
    """Protocol defining interface for injectors."""


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
