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
import weakref
from typing import Hashable

from . import exc
from .base import DEFAULT_ENV, DEFAULT_SCOPE, IInjector, IProvider


class Injector(IInjector):

    def __init__(self, provider: IProvider, env: Hashable = DEFAULT_ENV):
        self._provider = provider
        self._env = env
        self._cache = {}
        self._scope = DEFAULT_SCOPE
        self._children = []
        self.__parent = None

    def __exit__(self, *args):
        self.close()

    @property
    def _parent(self):
        if self.__parent is not None:
            return self.__parent()
        return None

    @_parent.setter
    def _parent(self, value):
        self.__parent = weakref.ref(value)

    def inject(self, key):
        if self._provider is None:
            raise exc.AlreadyClosedError()
        if key in self._cache:
            return self._cache[key].get_instance()
        unbound_instance = self._provider.get(key, self._env)
        if unbound_instance is None:
            raise self.NoProviderFoundError(key=key)
        if unbound_instance.scope != self._scope:
            if self._parent is not None:
                return self._parent.inject(key)
            raise self.OutOfScopeError(
                key=key,
                expected_scope=unbound_instance.scope,
                given_scope=self._scope
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
