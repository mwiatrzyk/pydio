"""Module that contains all PyDIO-specific exception types."""

from __future__ import annotations

from typing import Any, Callable, Mapping, Set

from pydio.v1 import _export_list, _utils
from pydio.v1.interface import (
    AsyncResourceFactoryLike,
    EnvType,
    ResourceFactoryLike,
    ScopeType,
    SupportsAsyncInject,
    SupportsInject,
)

__all__ = export = _export_list.ExportList()  # type: ignore


@export
class PyDIOError(Exception):
    """Base class for all exceptions that PyDIO library may raise."""


@export
class UserFactoryError(PyDIOError):
    """Base class for errors that may be raised if user-defined factory
    functions are wrongly declared, or if their execution is not possible
    without adjustments."""

    #: The user factory function.
    func: Callable

    #: The text explaining why this exception was raised.
    reason: str

    #: Additional context information.
    #:
    #: Used to pass additional data to be displayed to the user when this
    #: exception is raised.
    #:
    #: This will be empty dict if none was provided.
    extra_info: dict

    def __init__(self, func: Callable, reason: str, /, **extra_info: Any):
        super().__init__()
        self.func = func
        self.reason = reason
        self.extra_info = extra_info


@export
class UserFactoryDeclarationError(UserFactoryError):
    """Raised when user-defined resource factory function that is tried to be
    registered in PyDIO is found to have invalid declaration.

    This usually means that factory needs adjustments to make it usable for the
    current injection mode.
    """

    def __init__(self, func: Callable, reason: str, /, **extra_info: Any):
        super().__init__(func, reason, **extra_info)

    def __str__(self) -> str:
        rows = [
            "Invalid declaration of resource factory "
            f"{_utils.get_func_name(self.func)!r} located in "
            f"{_utils.get_func_location(self.func)}:"
        ]
        data = {
            "Reason": self.reason,
            "Details": {
                "Factory signature": _utils.get_func_signature(self.func),
                "Extra information": self.extra_info,
            },
        }
        _utils.format_detailed_error(rows, data, indent_char="  ")
        return "\n".join(rows)


@export
class UserFactoryPreconditionError(UserFactoryError):
    """Error raised when resource factory precondition check failed.

    This is always raised before even user-provided resource factory function
    starts and is used to signal that the factory has unmet preconditions that
    prevented it from being called. For example, an async factory requires
    async injector to inject its dependencies, but a non-async one was found
    instead.
    """

    #: The injector used.
    injector: SupportsInject | SupportsAsyncInject

    def __init__(
        self,
        func: Callable,
        injector: SupportsInject | SupportsAsyncInject,
        reason: str,
        /,
        **extra_info: Any,
    ):
        super().__init__(func, reason, **extra_info)
        self.injector = injector

    def __str__(self) -> str:
        rows = [
            "Precondition check failed for resource factory "
            f"{_utils.get_func_name(self.func)!r} located in "
            f"{_utils.get_func_location(self.func)}:"
        ]
        data = {
            "Reason": self.reason,
            "Details": {
                "Factory signature": _utils.get_func_signature(self.func),
                "Injector object used": self.injector,
                "Extra information": self.extra_info,
            },
        }
        _utils.format_detailed_error(rows, data, indent_char="  ")
        return "\n".join(rows)


@export
class ResourceFactoryLookupError(PyDIOError):
    """Base class for resource factory lookup errors."""

    #: The type for which the factory was requested.
    typ: Any

    #: The scope from where the factory was requested.
    scope: ScopeType

    #: The environment for which the factory was requested.
    env: EnvType

    def __init__(self, typ: Any, scope: ScopeType, env: EnvType):
        super().__init__()
        self.typ = typ
        self.scope = scope
        self.env = env

    def format_query(self) -> str:
        return f"typ={self.typ!r}, scope={self.scope!r}, env={self.env!r}"


@export
class ResourceFactoryNotFoundError(ResourceFactoryLookupError):
    """Raised when no resource factory matching given query was found.

    This is raised when trying to reach an unregistered factory for a given
    type, or if existing factories are registered for a different environments
    than the required one.
    """

    def __str__(self) -> str:
        return f"No resource factory found for query: {self.format_query()}"


@export
class OutOfScopeError(ResourceFactoryLookupError):
    """Raised when factory for a given type and environment exists, but is
    tried to be reached from an unrelated scope.

    Please refer to the :ref:`using-scopes` to read more about scoping.
    """

    #: The set with existing scopes found during lookup.
    existing_scopes: Set[ScopeType]

    def __init__(self, typ: Any, scope: ScopeType, env: EnvType, existing_scopes: Set[ScopeType]):
        super().__init__(typ, scope, env)
        self.existing_scopes = existing_scopes

    def __str__(self) -> str:
        rows = [f"No resource factory could be accessed from the current scope for query: {self.format_query()}"]
        data = {
            "Current scope": self.scope,
            "Existing scopes": self.existing_scopes,
        }
        _utils.format_detailed_error(rows, data, indent_char="  ")
        return "\n".join(rows)


@export
class IncompatibleResourceFactoryFoundError(ResourceFactoryLookupError):
    """Raised when factory found for a requested type cannot be used by current
    injector.

    For example, synchronous injectors cannot create resources using async
    factories.
    """

    #: The injector that was used
    injector: SupportsInject | SupportsAsyncInject

    #: The incompatible factory found.
    factory: ResourceFactoryLike | AsyncResourceFactoryLike

    #: The reason text.
    reason: str

    def __init__(
        self,
        typ: Any,
        scope: ScopeType,
        env: EnvType,
        injector: SupportsInject | SupportsAsyncInject,
        factory: ResourceFactoryLike | AsyncResourceFactoryLike,
        reason: str,
    ):
        super().__init__(typ, scope, env)
        self.injector = injector
        self.factory = factory
        self.reason = reason

    def __str__(self) -> str:
        rows = [f"Incompatible resource factory found for query: {self.format_query()}"]
        data = {
            "Reason": self.reason,
            "Details": {
                "Injector object": self.injector,
                "Resource factory object": self.factory,
            },
        }
        _utils.format_detailed_error(rows, data, indent_char="  ")
        return "\n".join(rows)


@export
class ScopedInjectorAlreadyExistsError(PyDIOError):
    """Raised when trying to create a scoped injector with a name that is
    already in use.

    Since scopes are used to manage resource lifetimes, PyDIO enforces that
    only one injector can manage single scope, refusing to create another one.

    Please refer to :ref:`using-scopes` for more details of how to use scoping.
    """

    #: The injector that refused to create scoped injector.
    injector: SupportsInject | SupportsAsyncInject

    #: The scope managed by :attr:`injector`.
    injector_scope: ScopeType

    #: The name of a scoped injector used.
    scoped_name: str

    def __init__(self, injector: SupportsInject | SupportsAsyncInject, injector_scope: ScopeType, scoped_name: str):
        super().__init__()
        self.injector = injector
        self.injector_scope = injector_scope
        self.scoped_name = scoped_name

    def __str__(self) -> str:
        rows = [f"Scoped injector named {self.scoped_name!r} already exists"]
        data = {
            "Details": {
                "Injector object": self.injector,
                "Injector scope": self.injector_scope,
            }
        }
        _utils.format_detailed_error(rows, data, indent_char="  ")
        return "\n".join(rows)


@export
class ResourceFactoryAlreadyExistsError(PyDIOError):
    """Raised when there is an existing resource factory found for given type,
    scope and environment."""

    #: The type with an already existing factory.
    typ: Any

    #: The scope associated with type.
    scope: ScopeType

    #: The environment associated with type.
    env: str | None

    def __init__(self, typ: Any, scope: ScopeType, env: str | None):
        super().__init__()
        self.typ = typ
        self.scope = scope
        self.env = env

    def __str__(self):
        return f"Resource factory already exists for: typ={self.typ!r}, scope={self.scope!r}, env={self.env!r}"


@export
class InjectorAlreadyClosedError(PyDIOError):
    """Raised when operation on an already closed injector is tried to be
    executed."""

    #: The closed injector that is tried to be used.
    injector: SupportsInject | SupportsAsyncInject

    def __init__(self, injector: SupportsInject | SupportsAsyncInject):
        super().__init__()
        self.injector = injector

    def __str__(self) -> str:
        return f"Cannot perform requested operation; the injector {self.injector!r} is already closed"


@export
class IncompleteClosingError(PyDIOError):
    """Raised when injector closing did not complete successfully due to one or
    more failures in generator-based resources teardown phase.

    This exception acts as exception group.
    """

    #: The injector object that failed to close successfully.
    injector: SupportsInject | SupportsAsyncInject

    #: A type-to-exception map containing all teardown-phase exceptions caught.
    dispose_errors: Mapping[Any, Exception]

    def __init__(self, injector: SupportsInject | SupportsAsyncInject, dispose_errors: Mapping[Any, Exception]):
        super().__init__()
        self.injector = injector
        self.dispose_errors = dispose_errors

    def __str__(self) -> str:
        rows = [
            f"Injector closing did not complete successfully with {len(self.dispose_errors)} resource disposal error(-s) found:"
        ]
        data = {
            "Details": {
                "Injector object": self.injector,
                "Errors found (during disposal)": [
                    {f"for type {typ!r}": exc} for typ, exc in self.dispose_errors.items()
                ],
            }
        }
        _utils.format_detailed_error(rows, data, indent_char="  ", recurse_list=True)
        return "\n".join(rows)
