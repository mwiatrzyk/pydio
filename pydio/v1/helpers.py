from __future__ import annotations

import inspect
from typing import Callable, Hashable, Literal, Any, cast


from . import _export_list, _utils, _factories, _adapters
from .interface import (
    T,
    AnyFuncType,
    AsyncFuncResult,
    EnvType,
    FuncResult,
    ScopeType,
    SupportsAsyncInject,
    SupportsInject,
    SupportsRegisterFactory,
)

__all__ = export = _export_list.ExportList()  # type: ignore


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
    func: AnyFuncType[T],
    *,
    scope: ScopeType = ScopeType(),
    env: EnvType = None,
) -> None:
    """Register user-defined function as a resource factory inside given
    provider.

    This method inspect the type of the user function and then wraps it
    with either :class:`pydio.v1.interface.ResourceFactoryLike`- or
    :class:`pydio.v1.interface.AsyncResourceFactoryLike`-capable object, which
    is then registered inside given provider.

    :param typ:
        The type or special form (e.g. :obj:`typing.Annotated`) to register
        factory for.

    :param func:
        The function to register as a factory for *typ*.

        Following functions are supported:
        - normal functions,
        - generator functions,
        - async functions,
        - async generator functions.

    :param scope:
        The scope to register *func* in.

        There must not be any other factory registered for *typ* under the
        same scope and environment.

    :param env:
        The environment to register *func* for.

        There must not be any other factory registered for *typ* under the
        same scope and environment.
    """
    unpacked_func = _utils.unpack_partial(func)
    if inspect.isasyncgenfunction(unpacked_func):
        return provider.register_factory(typ, _factories.AsyncGeneratorFactory(unpacked_func), scope=scope, env=env)
    if inspect.iscoroutinefunction(unpacked_func):
        return provider.register_factory(typ, _factories.AsyncFunctionFactory(unpacked_func), scope=scope, env=env)
    if inspect.isgeneratorfunction(unpacked_func):
        return provider.register_factory(typ, _factories.GeneratorFactory(unpacked_func), scope=scope, env=env)
    if callable(unpacked_func):
        return provider.register_factory(typ, _factories.FunctionFactory(unpacked_func), scope=scope, env=env)
    raise TypeError(f"Cannot use non-callable {type(func).__qualname__!r} type as resource factory")


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

    :param typ:
        The type of the instance to register.

        It is recommended to use custom type alias here, or to use
        :obj:`typing.Annotated`.

        For example, a good type candidate for constant object may be
        similar to this::

            provider.register_instance(Annotated[int, "https.defaultPort"], 443)

    :param scope:
        The scope to register instance in.

        There must not be any other factory or instance registered for
        *typ* under the same scope and environment.

    :param env:
        The environment to register instance for.

        For example, testing environment may use different constants that
        the production one and this is the place that allows to have
        several different values registered for one type.

        There must not be any other factory or instance registered for
        *typ* under the same scope and environment.
    """
    return provider.register_factory(typ, _factories.ConstantFactory(value), scope=scope, env=env)


@export
def provides(
    provider: SupportsRegisterFactory,
    typ: type[T] | Any,
    *,
    scope: ScopeType = ScopeType(),
    env: EnvType = None,
    mode: Literal["manual", "passthrough", "auto"] = "manual",
):
    """Decorates provided user function as a resource factory.

    :param provider:
        The provider to use.

    :param typ:
        The type to register factory for.

    :param scope:
        The scope to register factory in.

    :param env:
        The environment to register factory for.

    :param mode:
        Configures how to pass injector to the decorated factory.

        Following values are available:

        - *manual* - allow to manually define what arguments the function will
          receive when called. The function will accept any combination
          (including empty) of the arguments from the following list:
          - *injector* - to pass injector
          - *typ* - to pass registered type
          - *scope* - to pass registered scope
          - *env* - to pass registered environment

        - *passthrough* - pass injector as is, require factory function to
          accept exactly one positional argument. This is the fastest possible
          way to call the factory as no runtime decisions are made.

          .. important::
                There are no sync vs async runtime checks when this mode is
                used.

        - *auto* - expect any arguments to be defined and require all to have
          annotations set. These annotations are then used to inject needed
          objects and call the function accordingly. This mode allows to inject
          based on annotations without touching injector directly.
    """

    def decorator(func: Callable[..., FuncResult[T] | AsyncFuncResult[T]]):
        if mode == "manual":
            register_func(
                provider,
                typ,
                _adapters.adapt_func_for_manual_mode(func, typ, scope=scope, env=env),
                scope=scope,
                env=env,
            )
        elif mode == "auto":
            register_func(provider, typ, _adapters.adapt_func_for_auto_mode(func), scope=scope, env=env)
        else:
            register_func(provider, typ, func, scope=scope, env=env)
        return func

    return decorator
