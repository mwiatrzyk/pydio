"""Module containing provider types."""

from __future__ import annotations

from typing import Any

from pydio.v1 import _export_list
from pydio.v1.exc import (
    FactoryNotFoundError,
    FactoryAlreadyExistsError,
    OutOfScopeError,
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
        """Attach nested provider to this one.

        When no factory is found in current provider, lookup recurses into
        nested ones (preserving the attach call order) before giving up.

        :param other:
            The nested provider to attach.
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
        envs_found = self.__creator_registry.get(typ, {})
        scopes_found = envs_found.get(env, {}) or envs_found.get(None, {})
        if not scopes_found:
            nested_existing_scopes: set[ScopeType] = set()
            for nested_provider in self.__nested_providers:
                try:
                    return nested_provider.require_factory(typ, scope=scope, env=env)
                except OutOfScopeError as e:
                    nested_existing_scopes.update(e.existing_scopes)
                except FactoryNotFoundError:
                    pass
            if nested_existing_scopes:
                raise OutOfScopeError(sorted(nested_existing_scopes), typ=typ, scope=scope, env=env)
            raise FactoryNotFoundError(typ, scope, env)
        last_scopes = current_scopes = scopes_found
        for name in scope:
            current_scopes = current_scopes.get(name, {})
            if not current_scopes:
                break
            last_scopes = current_scopes
        factory = last_scopes.get(_ROOT_SCOPE)
        if factory is None:
            existing_scopes: list[ScopeType] = []
            self.__collect_existing_scopes(existing_scopes, scopes_found, ScopeType())
            raise OutOfScopeError(existing_scopes, typ=typ, scope=scope, env=env)
        return factory

    def __collect_existing_scopes(self, out: list[ScopeType], visited: dict, current: ScopeType) -> None:
        for k, v in visited.items():
            if k is _ROOT_SCOPE:
                out.append(current)
            else:
                self.__collect_existing_scopes(out, v, current + (k,))
