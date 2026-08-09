"""Module that contains all PyDIO-specific exception types."""

from __future__ import annotations

import traceback
from typing import Any, Callable, Mapping

from pydio.v1 import _export_list, _utils
from pydio.v1.interface import (
    AsyncResourceFactoryLike,
    EnvType,
    ResourceFactoryLike,
    ScopeType,
    SupportsAsyncInject,
    SupportsInject,
    supports_async_inject,
)

__all__ = export = _export_list.ExportList()  # type: ignore


@export
class PyDIOError(Exception):
    """Base class for all exceptions that PyDIO library may raise."""


@export
class FactoryDeclarationError(PyDIOError):
    """Raised when user-defined factory function is incorrectly declared."""

    #: The user-defined factory with incorrect declaration.
    func: Callable

    #: The reason text.
    reason: str

    #: The hint text.
    hint: str | None

    def __init__(self, func: Callable, reason: str, *, hint: str | None = None):
        super().__init__()
        self.func = func
        self.reason = reason
        self.hint = hint

    @property
    def func_filename(self) -> str:
        return self.func.__code__.co_filename

    @property
    def func_lineno(self) -> int:
        return self.func.__code__.co_firstlineno

    @property
    def func_signature(self) -> str:
        return str(_utils.get_func_signature(self.func))

    def __str__(self) -> str:
        rows = [f"For factory declared in file {self.func_filename}, line {self.func_lineno}:"]
        data = {
            "reason": self.reason,
            "hint": self.hint,
            "details": {
                "func_signature": self.func_signature,
                "func.__qualname__": self.func.__qualname__,
                "func.__module__": self.func.__module__,
            },
        }
        _utils.format_detailed_error(rows, data, indent_char="  ")
        return "\n".join(rows)


@export
class IncompatibleInjectorUsedError(PyDIOError):
    """Raised when async injector was tried to be used by a non-async factory,
    or non-async injector was tried to be used by an async factory."""

    #: The factory function that was called.
    func: Callable

    #: The incompatible injector that was tried to be used.
    injector: SupportsInject | SupportsAsyncInject

    def __init__(self, func: Callable, injector: SupportsInject | SupportsAsyncInject):
        super().__init__()
        self.func = func
        self.injector = injector

    @property
    def func_filename(self) -> str:
        return self.func.__code__.co_filename

    @property
    def func_lineno(self) -> int:
        return self.func.__code__.co_firstlineno

    @property
    def func_location(self) -> str:
        return f"{self.func_filename}:{self.func_lineno}"

    @property
    def reason_text(self) -> str:
        if supports_async_inject(self.injector):
            return "Synchronous factory cannot use async injector"
        return "Async factory cannot use synchronous injector"

    @property
    def hint_text(self) -> str:
        if supports_async_inject(self.injector):
            return "Declare factory as `async def` or switch to synchronous injector"
        return "Drop `async` from factory declaration or switch to async injector"

    def __str__(self) -> str:
        rows = [self.reason_text]
        data = {
            "Hint": self.hint_text,
            "Details": {
                "Injector used": self.injector,
                "Factory function": self.func,
                "Factory function location": self.func_location,
            },
        }
        _utils.format_detailed_error(rows, data, indent_char="  ")
        return "\n".join(rows)


@export
class IncompatibleFactoryProvidedError(PyDIOError):
    """Raised when factory found for a requested type cannot be used by current
    injector.

    For example, synchronous injectors cannot create resources using async
    factories.
    """

    #: The injector that was used
    injector: SupportsInject | SupportsAsyncInject

    #: The incompatible factory found.
    factory: ResourceFactoryLike | AsyncResourceFactoryLike

    def __init__(
        self, injector: SupportsInject | SupportsAsyncInject, factory: ResourceFactoryLike | AsyncResourceFactoryLike
    ):
        super().__init__()
        self.injector = injector
        self.factory = factory

    def __str__(self) -> str:
        return (
            f"Injector {self.injector!r} found an incompatible resource factory {self.factory!r} that cannot be used."
        )


@export
class FactoryLookupError(PyDIOError):
    """Base class for factory lookup errors."""

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


@export
class FactoryNotFoundError(FactoryLookupError):
    """Raised when no factory matching given type and environment could be
    found.

    This means that either the type is completely missing, or that existing
    factories are set neither for the given exact environment, nor the default
    one.
    """

    def __str__(self) -> str:
        return f"No factory found for query: typ={self.typ!r}, scope={self.scope!r}, env={self.env!r}"


@export
class OutOfScopeError(FactoryLookupError):
    """Raised when factory for a given type and environment exists, but under
    unrelated scope.

    Please refer to the :ref:`using-scopes` to read more about scoping.
    """

    #: The existing scopes where factory was found.
    existing_scopes: tuple[ScopeType, ...]

    def __init__(self, existing_scopes: tuple[ScopeType, ...], **kwargs):
        super().__init__(**kwargs)
        self.existing_scopes = existing_scopes

    def __str__(self) -> str:
        existing_str = ", ".join(repr(x) for x in self.existing_scopes)
        return (
            f"None of the existing scopes {{{existing_str}}} "
            f"could match the current scope {self.scope!r} for query: typ={self.typ!r}, scope={self.scope!r}, env={self.env!r}"
        )


@export
class ScopeAlreadyExistsError(PyDIOError):
    """Raised when trying to create a scoped injector for an already existing
    scope.

    Since scopes are used to manage resource lifetimes, PyDIO enforces that
    only one injector can manage single scope, refusing to create another one.
    """

    #: The scope that was found existing.
    scope: ScopeType

    def __init__(self, scope: ScopeType):
        super().__init__()
        self.scope = scope


@export
class FactoryAlreadyExistsError(PyDIOError):
    """Raised when there is an existing factory found for given type, scope and
    environment."""

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
        return f"Factory already exists: typ={self.typ!r}, scope={self.scope!r}, env={self.env!r}"


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
        return f"Cannot execute operations on a closed injector {self.injector!r} object"


@export
class IncompleteClosingError(PyDIOError):
    """Raised when injector closing did not complete successfully due to one or
    more failures in generator-based resources teardown phase.

    This exception acts as exception group.
    """

    #: A type-to-exception map containing all teardown-phase exceptions caught.
    dispose_errors: Mapping[type | Any, BaseException]

    def __init__(self, dispose_errors: Mapping[type | Any, BaseException]):
        super().__init__()
        self.dispose_errors = dispose_errors

    def __str__(self) -> str:
        out = [f"Found {len(self.dispose_errors)} teardown error(-s):"]
        data = {}
        for typ, exc in self.dispose_errors.items():
            data[f"in factory for type {typ!r}"] = {
                "Exception": str(exc),
                "Traceback": traceback.format_tb(exc.__traceback__),
            }
        _utils.format_detailed_error(out, data, indent_char="  ")
        return "\n".join(out)  # TODO: Fix formatting.
