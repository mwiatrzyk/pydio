"""Module containing provider types."""

from __future__ import annotations

from typing import Any

from pydio.v1 import _export_list
from pydio.v1.exc import (
    FactoryNotFoundError,
    FactoryAlreadyExistsError,
    OutOfScopeError,
    FactoryLookupError,
)
from pydio.v1.interface import (
    AsyncResourceFactoryLike,
    EnvType,
    ResourceFactoryLike,
    ScopeType,
    T,
    SupportsRequireFactory,
)

__all__ = export = _export_list.ExportList()  # type: ignore

_ROOT_SCOPE: ScopeType = ScopeType()


@export
class Provider:
    """Type factory registry and provider.

    Providers are used to build static maps of types and their associated
    factories later used by injectors to create instances of associated types.
    Providers can be organized into trees, where one root can have several
    leaves attached. This allows providers to be split into dedicated
    submodules, and later combined together so that the injector will be able
    to access all of them.
    """

    def __init__(self) -> None:
        self.__creator_registry: dict[Any, dict[EnvType, dict]] = {}
        self.__nested_providers: list[SupportsRequireFactory] = []

    def attach(self, other: SupportsRequireFactory):
        """Attach other provider to this one.

        When no factory is found in current provider, lookup recurses into
        attached ones (preserving the attach call order) before giving up.

        :param other:
            The other provider to attach.
        """
        self.__nested_providers.append(other)

    def register_factory(
        self,
        typ: type[T] | Any,
        factory: ResourceFactoryLike[T] | AsyncResourceFactoryLike[T],
        *,
        scope: ScopeType = ScopeType(),
        env: EnvType = None,
    ) -> None:
        """See :meth:`pydio.v1.interface.ProviderLike.register_factory`."""
        envs = self.__creator_registry.setdefault(typ, {})
        scopes = envs.setdefault(env, {})
        for name in scope:
            scopes = scopes.setdefault(name, {})
        if _ROOT_SCOPE in scopes:
            raise FactoryAlreadyExistsError(typ, scope, env)
        scopes[_ROOT_SCOPE] = factory

    def require_factory(
        self, typ: type[T] | Any, *, scope: ScopeType = ScopeType(), env: EnvType = None
    ) -> ResourceFactoryLike[T] | AsyncResourceFactoryLike[T]:
        """See :meth:`pydio.v1.interface.ProviderLike.require_factory`."""
        envs = self.__creator_registry.get(typ, {})
        scopes = envs.get(env, {}) or envs.get(None, {})
        if not scopes:
            for nested_provider in self.__nested_providers:
                try:
                    return nested_provider.require_factory(typ, scope=scope, env=env)
                except FactoryLookupError:
                    pass
            raise FactoryNotFoundError(typ, env)
        last_scopes = current_scopes = scopes
        for name in scope:
            current_scopes = current_scopes.get(name, {})
            if not current_scopes:
                break
            last_scopes = current_scopes
        factory = last_scopes.get(_ROOT_SCOPE)
        if factory is None:
            existing_scopes: list[ScopeType] = []
            self.__collect_existing_scopes(existing_scopes, scopes, ScopeType())
            raise OutOfScopeError(typ, env, scope, tuple(existing_scopes))
        return factory

    def __collect_existing_scopes(self, out: list[ScopeType], visited: dict, current: ScopeType) -> None:
        for k, v in visited.items():
            if k is _ROOT_SCOPE:
                out.append(current)
            else:
                self.__collect_existing_scopes(out, v, current + (k,))


# class _FactoryProxy:
#     class Manual:
#         _allowed_params = {"injector", "typ", "scope", "env"}

#         def __init__(self, target: Callable[..., Any], typ: type | Any, scope: ScopeType, env: EnvType):
#             self.__target = target
#             self.__declared_params = inspect.signature(target).parameters
#             self.__typ = typ
#             self.__scope = scope
#             self.__env = env
#             extra_params = sorted(set(self.__declared_params) - self._allowed_params)
#             if extra_params:
#                 raise UserFactoryDeclarationError(
#                     self.__target,
#                     f"Factory was declared with unsupported parameters: {', '.join(extra_params)}",
#                     f"Supported parameters are: {', '.join(sorted(self._allowed_params))}",
#                 )

#         def __call__(self, injector: SupportsInject | SupportsAsyncInject) -> Any:
#             declared_params = self.__declared_params
#             kwargs = {}
#             if "injector" in declared_params:
#                 if as_async_injector(injector) is not None:
#                     raise UserFactoryDeclarationError(
#                         self.__target,
#                         "Cannot pass async injector to a non-async factory.",
#                         "Please define factory using `async def` if you want to use it with async injector.",
#                     )
#                 kwargs["injector"] = injector
#             if "typ" in declared_params:
#                 kwargs["typ"] = self.__typ
#             if "scope" in declared_params:
#                 kwargs["scope"] = self.__scope
#             if "env" in declared_params:
#                 kwargs["env"] = self.__env
#             return self.__target(**kwargs)

#     class Auto:
#         def __init__(self, target: Callable[..., Any]):
#             self.__target = target

#         def __call__(self, injector: SupportsInject | SupportsAsyncInject) -> Any:
#             kwargs = {}
#             declared_params = _utils.get_func_signature(self.__target).parameters
#             if declared_params and as_async_injector(injector) is not None:
#                 raise TypeError(
#                     f"Cannot evaluate dependencies for non-async factory {self.__target!r} when async injector is used. "
#                     "Please define factory using `async def` if you want to use it with async injector."
#                 )
#             for name, param in declared_params.items():
#                 kwargs[name] = injector.inject(param.annotation)
#             return self.__target(**kwargs)

#     class AsyncManual:
#         _allowed_params = {"injector", "typ", "scope", "env"}

#         def __init__(self, target: Callable[..., Awaitable[Any]], typ: type | Any, scope: ScopeType, env: EnvType):
#             self.__target = target
#             self.__declared_params = inspect.signature(target).parameters
#             self.__typ = typ
#             self.__scope = scope
#             self.__env = env
#             extra_params = sorted(set(self.__declared_params) - self._allowed_params)
#             if extra_params:
#                 raise UserFactoryDeclarationError(
#                     self.__target,
#                     f"Factory was declared with unsupported parameters: {', '.join(extra_params)}",
#                     f"Supported parameters are: {', '.join(sorted(self._allowed_params))}",
#                 )

#         async def __call__(self, injector: SupportsAsyncInject) -> Any:
#             declared_params = self.__declared_params
#             kwargs = {}
#             if "injector" in declared_params:
#                 kwargs["injector"] = injector
#             if "typ" in declared_params:
#                 kwargs["typ"] = self.__typ
#             if "scope" in declared_params:
#                 kwargs["scope"] = self.__scope
#             if "env" in declared_params:
#                 kwargs["env"] = self.__env
#             return await self.__target(**kwargs)
