# ---------------------------------------------------------------------------
# pydio/injector.py
#
# Copyright (C) 2021 Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
#
# This file is part of PyDio library and is released under the terms of the
# MIT license: http://opensource.org/licenses/mit-license.php.
#
# See LICENSE.txt for details.
# ---------------------------------------------------------------------------
import contextlib
import inspect
import weakref
from typing import Hashable

from . import exc
from .base import IInjector, IUnboundFactoryRegistry


class Injector(
    IInjector, contextlib.AbstractContextManager,
    contextlib.AbstractAsyncContextManager
):

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

    def __init__(self, provider: IUnboundFactoryRegistry, env: Hashable = None):
        self._provider = provider
        self._env = env
        self._cache = {}
        self._scope = None
        self._children = []
        self.__parent = None

    def __exit__(self, *args):
        self.close()

    async def __aexit__(self, *args):
        maybe_coroutine = self.close()
        if inspect.iscoroutine(maybe_coroutine):
            await maybe_coroutine

    @property
    def _parent(self):
        if self.__parent is not None:
            return self.__parent()
        return None

    @_parent.setter
    def _parent(self, value):
        self.__parent = weakref.ref(value)

    @property
    def env(self):
        return self._env

    @property
    def scope(self):
        return self._scope

    def inject(self, key):
        if self._provider is None:
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

    def scoped(self, scope):
        injector = self.__class__(self._provider)
        self._children.append(injector)
        injector._parent = self  # pylint: disable=protected-access
        injector._scope = scope  # pylint: disable=protected-access
        return injector

    def close(self):

        def do_close():
            self._provider = None
            for child in self._children:
                child.close()
            for instance in self._cache.values():
                instance.close()

        async def do_async_close():
            self._provider = None
            for child in self._children:
                await child.close()
            for instance in self._cache.values():
                if instance.is_awaitable():
                    await instance.close()
                else:
                    instance.close()

        if not self._provider.has_awaitables():
            return do_close()
        return do_async_close()
