from __future__ import annotations

import collections.abc
import functools
import inspect
from typing import (
    Any,
    AsyncGenerator,
    Awaitable,
    Callable,
    Generator,
)

from pydio.v1.exc import FactoryDeclarationError, IncompatibleInjectorUsedError
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
    incorrect = set(declared_params) - _MANUAL_MODE_ALLOWED_PARAMS
    if incorrect:
        raise FactoryDeclarationError(
            func,
            "Parameters out of allowed set are found in function declaration; "
            f"extra found: {sorted(incorrect)}, allowed set: {sorted(_MANUAL_MODE_ALLOWED_PARAMS)}",
        )

    if inspect.isasyncgenfunction(func):

        @functools.wraps(func)
        def wrapped_async_gen(injector: SupportsInject | SupportsAsyncInject) -> AsyncGenerator[T]:
            kw = make_kwargs(injector)
            if "injector" in kw and supports_inject(injector):
                raise IncompatibleInjectorUsedError(func, injector)
            return _AsyncGeneratorProxy(func(**kw))

        return wrapped_async_gen

    if inspect.iscoroutinefunction(func):

        @functools.wraps(func)
        async def wrapped_coroutine(injector: SupportsInject | SupportsAsyncInject) -> T:
            kw = make_kwargs(injector)
            if "injector" in kw and supports_inject(injector):
                raise IncompatibleInjectorUsedError(func, injector)
            return await func(**kw)

        return wrapped_coroutine

    if inspect.isgeneratorfunction(func):

        @functools.wraps(func)
        def wrapped_generator(injector: SupportsInject | SupportsAsyncInject) -> Generator[T, None, None]:
            kw = make_kwargs(injector)
            if "injector" in kw and supports_async_inject(injector):
                raise IncompatibleInjectorUsedError(func, injector)
            return _GeneratorProxy(func(**kw))

        return wrapped_generator

    assert inspect.isfunction(func)  # Just to satisfy type checker

    @functools.wraps(func)
    def wrapped_func(injector: SupportsInject | SupportsAsyncInject) -> T:
        kw = make_kwargs(injector)
        if "injector" in kw and supports_async_inject(injector):
            raise IncompatibleInjectorUsedError(func, injector)
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
            raise IncompatibleInjectorUsedError(func, injector)
        for name, param in declared_params.items():
            kw[name] = await injector.inject(param.annotation)
        return kw

    def resolve_deps(injector: SupportsInject | SupportsAsyncInject) -> dict:
        kw = {}
        if declared_params and supports_async_inject(injector):
            raise IncompatibleInjectorUsedError(func, injector)
        for name, param in declared_params.items():
            kw[name] = injector.inject(param.annotation)
        return kw

    declared_params = _utils.get_func_signature(func).parameters
    for param in declared_params.values():
        if param.annotation is inspect.Parameter.empty:
            raise FactoryDeclarationError(func, "Not all arguments have annotations set")

    if inspect.isasyncgenfunction(func):

        @functools.wraps(func)
        def wrapped_async_gen(injector: SupportsInject | SupportsAsyncInject) -> AsyncGenerator[T, None]:
            async def make_generator():
                kw = await async_resolve_deps(injector)
                return func(**kw)

            return _AsyncGeneratorAutoProxy(make_generator)

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
            return _GeneratorProxy(func(**kw))

        return wrapped_gen

    assert inspect.isfunction(func)

    @functools.wraps(func)
    def wrapped_func(injector: SupportsInject | SupportsAsyncInject) -> Generator[T, None, None]:
        kw = resolve_deps(injector)
        return func(**kw)

    return wrapped_func


class _AsyncGeneratorProxy(collections.abc.AsyncGenerator[T]):
    def __init__(self, target: AsyncGenerator[T]) -> None:
        self.__target = target

    async def asend(self, value: None) -> T:
        return await self.__target.asend(value)

    async def athrow(self, typ, val=None, tb=None, /) -> T:
        return await self.__target.athrow(typ, val, tb)


class _AsyncGeneratorAutoProxy(collections.abc.AsyncGenerator[T]):
    def __init__(self, factory: Callable[[], Awaitable[AsyncGenerator[T]]]) -> None:
        self.__factory = factory
        self.__target: AsyncGenerator[T] | None = None

    async def __require_target(self) -> AsyncGenerator[T]:
        # FIXME: Is there a better way of achieving this?
        if self.__target is None:
            self.__target = await self.__factory()
        return self.__target

    async def asend(self, value: None) -> T:
        target = await self.__require_target()
        return await target.asend(value)

    async def athrow(self, typ, val=None, tb=None, /) -> T:
        target = await self.__require_target()
        return await target.athrow(typ, val, tb)


class _GeneratorProxy(collections.abc.Generator[T]):
    def __init__(self, target: Generator[T]) -> None:
        self.__target = target

    def send(self, value: None) -> T:
        return self.__target.send(value)

    def throw(self, typ, val=None, tb=None) -> T:
        return self.__target.throw(typ, val, tb)
