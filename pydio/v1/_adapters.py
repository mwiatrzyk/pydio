from __future__ import annotations

import functools
import inspect
from typing import (
    Any,
    AsyncGenerator,
    Callable,
    Generator,
)

from pydio.v1 import _compat
from pydio.v1.exc import UserFactoryDeclarationError, UserFactoryPreconditionError
from pydio.v1.interface import supports_async_inject, supports_inject

from . import _utils
from .interface import (
    T,
    AnyFuncType,
    AsyncFuncResult,
    EnvType,
    FuncResult,
    ScopeType,
    SupportsAsyncInject,
    SupportsInject,
)

_MANUAL_MODE_ALLOWED_PARAMS: set[str] = {"injector", "typ", "scope", "env"}


def _make_async_injector_required_error(func: Callable, injector: SupportsInject) -> UserFactoryPreconditionError:
    return UserFactoryPreconditionError(
        func,
        injector,
        "Incompatible injector used; please use async injector, or make factory non-async",
        injector_given_implements=SupportsInject,
        injector_required_implements=SupportsAsyncInject,
    )


def _make_non_async_injector_required_error(
    func: Callable, injector: SupportsAsyncInject
) -> UserFactoryPreconditionError:
    return UserFactoryPreconditionError(
        func,
        injector,
        "Incompatible injector used; please use non-async injector, or make factory async",
        injector_given_implements=SupportsAsyncInject,
        injector_required_implements=SupportsInject,
    )


def adapt_func_for_manual_mode(
    func: Callable[..., FuncResult[T] | AsyncFuncResult[T]],
    typ: type[T] | Any,
    *,
    scope: ScopeType = ScopeType(),
    env: EnvType = None,
) -> AnyFuncType[T]:
    """Adapts user provided factory for *manual* mode.

    This mode allows to defined factory function with any combination (empty
    included) of the following arguments:

    - *injector* - to access current injector,
    - *typ* - to access type for which the factory was created,
    - *scope* - to access scope in which the factory was created,
    - *env* - to access environment where factory was created.

    Type annotations for these arguments are not required (although
    recommended) as match is made by argument name, not its annotation (unlike
    *auto* mode).

    When adapted factory is defined with *injector* argument then it requires
    injector to be async if factory is async, or non-async otherwise. The check
    is skipped if *injector* argument is not used.

    :param func:
        The callable to wrap.

    :param typ:
        The type to pass if ``typ`` param is used.

    :param scope:
        The scope to pass if ``scope`` param is used.

    :param env:
        The environment to pass if ``env`` param is used.
    """

    def make_kwargs(injector: SupportsInject | SupportsAsyncInject) -> dict:
        kw: dict[str, Any] = {}
        if "injector" in declared_params:
            kw["injector"] = injector
        if "typ" in declared_params:
            kw["typ"] = typ
        if "scope" in declared_params:
            kw["scope"] = scope
        if "env" in declared_params:
            kw["env"] = env
        return kw

    declared_params = _utils.get_func_signature(func).parameters
    excessive_params = set(declared_params) - _MANUAL_MODE_ALLOWED_PARAMS
    if excessive_params:
        raise UserFactoryDeclarationError(
            func,
            "Excessive parameters found; only predefined parameter names can be used with `manual` mode.",
            allowed_params=_MANUAL_MODE_ALLOWED_PARAMS,
            excessive_params=excessive_params,
        )

    if inspect.isasyncgenfunction(func):

        @functools.wraps(func)
        def wrapped_async_gen(injector: SupportsInject | SupportsAsyncInject) -> AsyncGenerator[T]:
            async def make_generator():
                return func(**kw)

            kw = make_kwargs(injector)
            if "injector" in kw and supports_inject(injector):
                raise _make_async_injector_required_error(func, injector)
            return _compat.AsyncGeneratorProxy(make_generator)  # type: ignore

        return wrapped_async_gen

    if inspect.iscoroutinefunction(func):

        @functools.wraps(func)
        async def wrapped_coroutine(injector: SupportsInject | SupportsAsyncInject) -> T:
            kw = make_kwargs(injector)
            if "injector" in kw and supports_inject(injector):
                raise _make_async_injector_required_error(func, injector)
            return await func(**kw)

        return wrapped_coroutine

    if inspect.isgeneratorfunction(func):

        @functools.wraps(func)
        def wrapped_generator(injector: SupportsInject | SupportsAsyncInject) -> Generator[T, None, None]:
            kw = make_kwargs(injector)
            if "injector" in kw and supports_async_inject(injector):
                raise _make_non_async_injector_required_error(func, injector)
            return _compat.GeneratorProxy(func(**kw))  # type: ignore

        return wrapped_generator

    assert inspect.isfunction(func)  # Just to satisfy type checker

    @functools.wraps(func)
    def wrapped_func(injector: SupportsInject | SupportsAsyncInject) -> T:
        kw = make_kwargs(injector)
        if "injector" in kw and supports_async_inject(injector):
            raise _make_non_async_injector_required_error(func, injector)
        return func(**kw)

    return wrapped_func


def adapt_func_for_auto_mode(func: Callable[..., FuncResult[T] | AsyncFuncResult[T]]) -> AnyFuncType[T]:
    """Adapts user provided factory for *auto* mode.

    This mode allows to parse function's arguments and automatically inject all
    dependencies using their annotations as types to inject. Then the target
    function is called with all needed objects already in place.

    Requires async injector for async factories, and non-async one for
    non-async factories. Also, each argument must have type annotation defined.

    :param func:
        The function to adapt.
    """

    async def async_resolve_deps(injector: SupportsInject | SupportsAsyncInject) -> dict:
        kw = {}
        if declared_params and supports_inject(injector):
            raise _make_async_injector_required_error(func, injector)
        for name, param in declared_params.items():
            kw[name] = await injector.inject(param.annotation)
        return kw

    def resolve_deps(injector: SupportsInject | SupportsAsyncInject) -> dict:
        kw = {}
        if declared_params and supports_async_inject(injector):
            raise _make_non_async_injector_required_error(func, injector)
        for name, param in declared_params.items():
            kw[name] = injector.inject(param.annotation)
        return kw

    declared_params = _utils.get_func_signature(func).parameters
    unannotated_params: set[str] = set()
    for param in declared_params.values():
        if param.annotation is inspect.Parameter.empty:
            unannotated_params.add(param.name)
    if unannotated_params:
        raise UserFactoryDeclarationError(
            func,
            "Parameters without annotations found; all parameters must have annotations set for `auto` mode.",
            unannotated_params=unannotated_params,
        )

    if inspect.isasyncgenfunction(func):

        @functools.wraps(func)
        def wrapped_async_gen(injector: SupportsInject | SupportsAsyncInject) -> AsyncGenerator[T, None]:
            async def make_generator():
                kw = await async_resolve_deps(injector)
                return func(**kw)

            return _compat.AsyncGeneratorProxy(make_generator)  # type: ignore

        return wrapped_async_gen

    if inspect.iscoroutinefunction(func):

        @functools.wraps(func)
        async def wrapped_coroutine(injector: SupportsInject | SupportsAsyncInject) -> T:
            kw = await async_resolve_deps(injector)
            return await func(**kw)

        return wrapped_coroutine

    if inspect.isgeneratorfunction(func):

        @functools.wraps(func)
        def wrapped_gen(injector: SupportsInject | SupportsAsyncInject) -> Generator[T, None, None]:
            kw = resolve_deps(injector)
            return _compat.GeneratorProxy(func(**kw))  # type: ignore

        return wrapped_gen

    assert inspect.isfunction(func)

    @functools.wraps(func)
    def wrapped_func(injector: SupportsInject | SupportsAsyncInject) -> Generator[T, None, None]:
        kw = resolve_deps(injector)
        return func(**kw)

    return wrapped_func
