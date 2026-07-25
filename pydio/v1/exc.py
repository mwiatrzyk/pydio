"""Module that contains all PyDIO-specific exception types."""

from __future__ import annotations

from typing import Any, Callable

from pydio.v1 import _export_list, _utils
from pydio.v1.interface import EnvType, ScopeType, SupportsAsyncInject, SupportsInject

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
class AsyncInjectorRequiredError(PyDIOError):
    """Raised when factory requires async injector but non-async was given."""

    #: The factory function.
    func: Callable

    def __init__(self, func: Callable):
        super().__init__()
        self.func = func

    @property
    def func_filename(self) -> str:
        return self.func.__code__.co_filename

    @property
    def func_lineno(self) -> int:
        return self.func.__code__.co_firstlineno

    def __str__(self) -> str:
        # TODO: Better error formatting, and maybe some more info to be included.
        sig = _utils.get_func_signature(self.func)
        sig_str = f"{self.func.__name__}{sig}{sig.return_annotation}"
        rows = [f"For factory {self.func.__name__!r} defined in {self.func_filename}, line {self.func_lineno}"]
        data = {
            "Factory signature": sig_str,
        }
        _utils.format_detailed_error(rows, data, indent_char="  ")
        return "\n".join(rows)


@export
class IncompatibleInjectorUsedError(PyDIOError):
    """Raised when async injector was tried to be used by a non-async factory,
    or non-async injector was tried to be used by an async factory."""

    #: The factory that was called.
    factory: Callable

    #: The incompatible injector that was tried to be used.
    injector: SupportsInject | SupportsAsyncInject

    def __init__(self, factory: Callable, injector: SupportsInject | SupportsAsyncInject):
        super().__init__()
        self.factory = factory
        self.injector = injector

    def __str__(self) -> str:
        return "Incompatible injector used"


@export
class FactoryLookupError(PyDIOError):
    """Base class for factory lookup errors."""

    #: The looked up type.
    typ: Any

    def __init__(self, typ: Any):
        super().__init__()
        self.typ = typ


@export
class FactoryNotFoundError(FactoryLookupError):
    """Raised when no factory matching given type and environment could be
    found.

    This means that either the type is completely missing, or that existing
    factories are set neither for the given exact environment, nor the default
    one.
    """

    #: The environment names tried.
    env: EnvType

    def __init__(self, typ: Any, env: EnvType):
        super().__init__(typ)
        self.env = env

    def __str__(self) -> str:
        return f"No factory found for: typ={self.typ!r}, env={self.env!r}"


@export
class OutOfScopeError(FactoryLookupError):
    """Raised when factory for a given type and environment exists, but under
    unrelated scope.

    Please refer to the :ref:`using-scopes` to read more about scoping.
    """

    #: The environment used.
    env: EnvType

    #: The current scope.
    scope: ScopeType

    #: The existing scopes.
    existing_scopes: tuple[ScopeType, ...]

    def __init__(self, typ: Any, env: EnvType, scope: ScopeType, existing: tuple[ScopeType, ...]):
        super().__init__(typ)
        self.env = env
        self.scope = scope
        self.existing_scopes = existing

    def __str__(self) -> str:
        existing_str = ", ".join(repr(x) for x in self.existing_scopes)
        return f"None of the existing scopes {{{existing_str}}} can be used for: typ={self.typ!r}, env={self.env!r}, scope={self.scope!r}"


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
