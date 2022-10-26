# ---------------------------------------------------------------------------
# pydio/injector.py
#
# Copyright (C) 2021 - 2022 Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
#
# This file is part of PyDio library and is released under the terms of the
# MIT license: http://opensource.org/licenses/mit-license.php.
#
# See LICENSE.txt for details.
# ---------------------------------------------------------------------------
import threading
import weakref
from typing import Awaitable, Hashable, Optional

from . import exc
from .base import IInjector, IUnboundFactoryRegistry


class Injector(IInjector):
    """Dependency injector main class.

    :param provider:
        Unbound factory provider to work on

    :param env:
        Name of the environment this injector will use when making queries to
        :class:`IUnboundFactoryRegistry` object given via **provider**.

        This can be obtained f.e. from environment variable. Once injector is
        created you will not be able to change this.

        See :meth:`IUnboundFactoryRegistry.get` for more details.
    """

    def __init__(self, provider: IUnboundFactoryRegistry, env: Hashable = None):
        self._provider = provider
        self._env = env
        self._cache = {}
        self._lock = threading.RLock()
        self._scope = None
        self._children = []
        self.__parent = None

    @property
    def _parent(self):
        if self.__parent is not None:
            return self.__parent()
        return None

    @_parent.setter
    def _parent(self, value):
        self.__parent = weakref.ref(value)

    @property
    def env(self) -> Optional[Hashable]:
        """Environment assigned to this injector."""
        return self._env

    def inject(self, key):
        """See :class:`IInjector.inject`."""
        if key in self._cache:
            return self._cache[key].get_instance()
        with self._lock:
            if self.is_closed():
                raise self.AlreadyClosedError()
            if key in self._cache:
                return self._cache[key].get_instance()
            unbound_instance = self._provider.get(key, self._env)
            if unbound_instance is None:
                raise self.NoProviderFoundError(key=key, env=self._env)
            if unbound_instance.scope != self._scope:
                if self._parent is not None:
                    return self._parent.inject(key)
                raise self.OutOfScopeError(
                    key=key,
                    scope=self._scope,
                    required_scope=unbound_instance.scope,
                )
            instance = unbound_instance.bind(self)
            self._cache[key] = instance
            return instance.get_instance()

    def scoped(self, scope: Hashable, env: Hashable = None) -> IInjector:
        """See :meth:`pydio.base.IInjector.scoped`."""
        if env is not None:
            parent_env = self._env
            if parent_env is not None and parent_env != env:
                raise ValueError(
                    "scoped() got an invalid value for parameter 'env': expected {!r} or None, got {!r}"
                    .format(parent_env, env)
                )
        with self._lock:
            injector = self.__class__(self._provider, env=env or self._env)
            self._children.append(injector)
            injector._parent = self  # pylint: disable=protected-access
            injector._scope = scope  # pylint: disable=protected-access
            return injector

    def close(self) -> Optional[Awaitable[None]]:
        """See :meth:`pydio.base.IInjector.close`."""
        if self._provider is not None:
            with self._lock:
                provider = self._provider
                awaitables = []
                for child in self._children:
                    maybe_awaitable = child.close()
                    if maybe_awaitable is not None:
                        awaitables.append(maybe_awaitable)
                for instance in self._cache.values():
                    maybe_awaitable = instance.close()
                    if maybe_awaitable is not None:
                        awaitables.append(maybe_awaitable)
                if not provider.has_awaitables():
                    self._provider = None
                else:

                    async def do_async_close(awaitables):
                        self._provider = None
                        for awaitable in awaitables:
                            await awaitable

                    return do_async_close(awaitables)

    def is_closed(self) -> bool:
        """Return True if this injector was closed or False otherwise."""
        return self._provider is None

    class NoProviderFoundError(exc.InjectorError):
        """Raised when there was no matching provider found for given key.

        :param key:
            Searched key

        :param env:
            Searched environment
        """
        message_template = "No provider found for: key={self.key!r}, env={self.env!r}"

        def __init__(self, key, env):
            super().__init__(key=key, env=env)

        @property
        def key(self) -> Hashable:
            return self.params['key']

        @property
        def env(self) -> Hashable:
            return self.params['env']

    class OutOfScopeError(exc.InjectorError):
        """Raised when there was attempt to create object that was registered
        for different scope.

        :param key:
            Searched key

        :param scope:
            Injector's own scope

        :param required_scope:
            Required scope
        """
        message_template =\
            "Cannot inject {self.key!r} due to scope mismatch: "\
            "{self.required_scope!r} (required) != {self.scope!r} (owned)"

        def __init__(self, key, scope, required_scope):
            super().__init__(
                key=key, scope=scope, required_scope=required_scope
            )

        @property
        def key(self) -> Hashable:
            return self.params['key']

        @property
        def scope(self) -> Hashable:
            return self.params['scope']

        @property
        def required_scope(self) -> Hashable:
            return self.params['required_scope']

    class AlreadyClosedError(exc.InjectorError):
        """Raised when operation on a closed injector was performed."""
        message_template = "This injector was already closed"
