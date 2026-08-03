from __future__ import annotations

import inspect
from typing import Any, Annotated, cast


from . import _export_list, _utils, _factories
from .interface import (
    T,
    AnyFuncType,
    EnvType,
    ScopeType,
    SupportsInject,
    SupportsRegisterFactory,
)

__all__ = export = _export_list.ExportList()  # type: ignore


@export
def inject_type(injector: SupportsInject, typ: type[T]) -> T:
    """Helper for injecting objects of given type.

    It is a tiny wrapper over :meth:`SupportsInject.inject` method that casts
    returned any object into instance of *typ*.

    .. note::
        For performance reasons there are no runtime checks if returned object
        is a real *typ* instance; the helper is just doing a cast using
        :func:`typing.cast` function that basically just changes type hint for
        return value.

    :param injector:
        The injector to use.

    :param typ:
        The type of instance to inject.
    """
    return cast(T, injector.inject(typ))


@export
def inject_annotated_type(injector: SupportsInject, typ: type[T], *args: Any) -> T:
    """Helper for injecting values provided as ``Annotated[typ, *args]``.

    It builds an :obj:`typing.Annotated` object using given *typ* and *args*
    and then uses it as a key when calling :meth:`SupportsIndex.inject` method.
    Finally, the call either ends with exception (if no matching provider was
    found) or returns injected object casted as *typ*.

    .. note::
        For performance reasons there are no runtime checks if returned object
        is a real *typ* instance; the helper is just doing a cast using
        :func:`typing.cast` function that basically just changes type hint for
        return value.

    :param injector:
        The injector to use.

    :param key:
        The type to inject.
    """
    # TODO: Maybe there is a better way to construct Annotated?
    key = Annotated.__class_getitem__((typ, *args))  # type: ignore
    return cast(T, injector.inject(key))


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
