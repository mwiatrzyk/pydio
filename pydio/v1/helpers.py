from __future__ import annotations

import inspect
from typing import AsyncGenerator, Awaitable, Callable, Generator, Hashable, Literal, Any, cast


from . import _export_list, _utils, _factories, _adapters
from .interface import (
    T,
    AnyInjector,
    AsyncFuncResult,
    EnvType,
    FuncResult,
    ScopeType,
    SupportsAsyncInject,
    SupportsInject,
    SupportsRegisterFactory,
)

__all__ = export = _export_list.ExportList()  # type: ignore

#: Type defining mode literals.
#:
#: Used by :func:`register_func` and :func:`provides` helpers.
Mode = Literal["auto", "manual", "passthrough"]


@export
def inject_annotated(injector: SupportsInject, typ: type[T], *metadata: Any) -> T:
    """Helper that builds and injects annotated type preserving the original
    type on return value.

    Since PyDIO works using type-to-factory maps it is not possible to use two
    different factories per single type. To work around this limitation,
    existing type can be wrapped with :obj:`typing.Annotated` special form and
    have user-defined metadata attached.

    For example:

        from typing import Annotated

        HostName = Annotated[str, "hostname"]
        UserName = Annotated[str, "username"]

    And now, if this helper is used, you don't loose the original type at the
    cost of having to remember the wrapped type, and the metadata::

        hostname = inject_annotated(injector, str, "hostname")
        username = inject_annotated(injector, str, "username")
        # both `hostname` and `username` are now interpreted as `str`

    :param injector:
        The injector to use.

    :param typ:
        The expected return value type.

    :param metadata:
        The tuple with metadata set for a given *typ*.
    """
    return injector.inject(_utils.build_annotated(cast(Hashable, typ), *metadata))


@export
async def async_inject_annotated(injector: SupportsAsyncInject, typ: type[T], *metadata: Any) -> T:
    """See as :func:`inject_annotated` docs.

    This helper does the same, but is meant to be used with async injector.
    """
    return await injector.inject(_utils.build_annotated(cast(Hashable, typ), *metadata))


@export
def register_func(
    provider: SupportsRegisterFactory,
    typ: type[T] | Any,
    func: Callable[..., FuncResult[T] | AsyncFuncResult[T]],
    *,
    scope: ScopeType = ScopeType(),
    env: EnvType = None,
    mode: Mode = "manual",
) -> None:
    """Register user-defined function as a resource factory inside given
    provider.

    This method inspect the type of the user function and then wraps it
    with either :class:`pydio.v1.interface.ResourceFactoryLike`- or
    :class:`pydio.v1.interface.AsyncResourceFactoryLike`-capable object, which
    is then registered inside given provider.

    :param provider:
        The provider to register in.

    :param typ:
        The type or a special form (e.g. :obj:`typing.Annotated`) to register
        factory for.

    :param func:
        The function to register as a factory for the given *typ*.

        Following types are supported:
        - functions,
        - generator functions,
        - async functions,
        - async generator functions.

    :param scope:
        The scope to register factory in.

        Scopes are organized into trees and are tightly correlated with scoped
        injectors (see :meth:`pydio.v1.interface.InjectorLike.scoped` or
        :meth:`pydio.v1.interface.AsyncInjectorLike.scoped`) and are basically
        used to define allowed lifetime of a resource. PyDIO does not use
        neither singletons, nor global state, and the only mechanism to limit
        lifetime of a resource is scoping.

        Imagine you have three things:
        - configuration that never changes
        - database connection that is kept alive
        - database session that must be committed/rolled back when client
          request ends

        All af these can easily be modelled in PyDIO using scopes:
        - you can use root scope ``()`` for configuration data (the default)
        - you can use e.g. ``('app',)`` scope for database connection
        - and you can use e.g. ``('app', 'request')`` scope for a single
          application request

        .. important::
            There must not be any other factory registered for *typ* under the
            same scope and environment.

    :param env:
        The environment to register factory for.

        Environments allow to pick a different implementation of the same
        interface depending on things like whether or not we are dealing with
        production environment, or a testing one. For instance, in-memory
        SQLite database can be used when testing, while a normal PostgreSQL
        will be used when in production.

        .. important::
            There must not be any other factory registered for *typ* under the
            same scope and environment.

    :param mode:
        Configures how dependencies (if any) of the registered resource factory
        are going to be resolved.

        Following values are available:

        ``manual``

            Allows to decide which arguments from the list below are going to
            be used by the factory function:
            - *injector* - to pass injector
            - *typ* - to pass registered type
            - *scope* - to pass registered scope
            - *env* - to pass registered environment
            The user can pick any subset from the list above, including empty
            set (no arguments).

            Type hints are optional in this mode (names are important), and
            injections of dependent types (if needed) must be done manually via
            *injector* parameter.

            This is the default mode and it basically mimics behavior of a pre
            1.x PyDIO releases.

        ``auto``

            Allows to define a custom set of arguments and their types and
            forces PyDIO to automatically resolve those dependencies (using
            type hints as injection arguments) before the factory function is
            called. When factory function is finally called, it receives
            injected objects in place of each of declared argument.

            This mode also allows declaring factory functions without arguments
            (meaning: no dependencies), but it DOES NOT allow skipping
            annotations, as those are required to resolve dependencies.

            .. important::
                When this mode is used you cannot access injector or factory
                metadata (type, scope and environment) directly like you would
                for the ``manual`` mode.

        ``passthrough``

            Pass injector as is, requiring factory function to accept exactly
            one positional argument, which is the injector object implementing
            either :class:`pydio.v1.interface.SupportsInject` or
            :class:`pydio.v1.interface.SupportsAsyncInject` protocols.

            This is the fastest possible way to call the factory as no runtime
            checks are made. It is recommended to use this mode instead of
            ``manual`` if injections are made manually and just the injector is
            used by the factory function.

            .. important::
                There are no sync vs async runtime checks when this mode is
                used.
    """
    if not callable(func):
        raise TypeError(f"Cannot use non-callable object {func!r} as a resource factory")
    unpacked_func = _utils.unpack_partial(func)
    if mode == "manual":
        adapted_func = _adapters.adapt_func_for_manual_mode(unpacked_func, typ, scope=scope, env=env)
    elif mode == "auto":
        adapted_func = _adapters.adapt_func_for_auto_mode(unpacked_func)
    else:
        adapted_func = unpacked_func
    if inspect.isasyncgenfunction(unpacked_func):
        adapted_func = cast(Callable[[SupportsAsyncInject], AsyncGenerator[T, None]], adapted_func)
        return provider.register_factory(
            typ,
            _factories.AsyncGeneratorFactory(adapted_func),
            scope=scope,
            env=env,
        )
    if inspect.iscoroutinefunction(unpacked_func):
        adapted_func = cast(Callable[[SupportsAsyncInject], Awaitable[T]], adapted_func)
        return provider.register_factory(typ, _factories.AsyncFunctionFactory(adapted_func), scope=scope, env=env)
    if inspect.isgeneratorfunction(unpacked_func):
        adapted_func = cast(Callable[[AnyInjector], Generator[T, None, None]], adapted_func)
        return provider.register_factory(typ, _factories.GeneratorFactory(adapted_func), scope=scope, env=env)
    adapted_func = cast(Callable[[AnyInjector], T], adapted_func)
    return provider.register_factory(typ, _factories.FunctionFactory(adapted_func), scope=scope, env=env)


@export
def register_constant(
    provider: SupportsRegisterFactory,
    typ: type[T] | Any,
    value: T,
    *,
    scope: ScopeType = ScopeType(),
    env: EnvType = None,
) -> None:
    """Similar to :func:`register_func`, but meant to be used for registering
    plain constant objects instead of factories.

    Behind the scenes this method creates a factory that satisfies
    :class:`pydio.v1.interface.ResourceFactoryLike` protocol but is
    optimized for plain objects.

    :param provider:
        The provider to register in.

    :param typ:
        The type of the instance to register.

        It is recommended to use custom type alias here, or to use
        :obj:`typing.Annotated`.

        For example, a good type candidate for constant object may be
        similar to this::

            provider.register_instance(Annotated[int, "https.defaultPort"], 443)

    :param value:
        The constant value to associate with given *typ*.

    :param scope:
        See *scope* parameter of the :func:`register_func` function.

    :param env:
        See *env* parameter of the :func:`register_func` function.
    """
    return provider.register_factory(typ, _factories.ConstantFactory(value), scope=scope, env=env)


@export
def provides(
    provider: SupportsRegisterFactory,
    typ: type[T] | Any,
    *,
    scope: ScopeType = ScopeType(),
    env: EnvType = None,
    mode: Mode = "manual",
):
    """Decorates provided user function as a resource factory.

    This is a decorator version of the :func:`register_func` helper.
    """

    def decorator(func: Callable[..., FuncResult[T] | AsyncFuncResult[T]]):
        register_func(provider, typ, func, scope=scope, env=env, mode=mode)
        return func

    return decorator
