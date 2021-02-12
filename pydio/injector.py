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
from typing import Awaitable, Hashable, Optional

from . import _compat, exc
from .base import IInjector, IUnboundFactoryRegistry


class Injector(
    IInjector, contextlib.AbstractContextManager,
    _compat.AbstractAsyncContextManager
):
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

    def inject(self, key):
        """See :class:`IInjector.inject`."""
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

    def scoped(self, scope: Hashable, env: Hashable = None) -> 'Injector':
        """Create scoped injector that is a child of current one.

        Scoped injectors can only operate on :class:`IUnboundFactory` objects
        with :attr:`IUnboundFactory.scope` attribute being equal to given
        scope.

        :param scope:
            User-defined scope name.

        :param env:
            User-defined environment name for newly created injector and all
            its descendants.

            This option is applicable only if none of the ancestors of newly
            created injector has environment set. Otherwise, setting this will
            cause :exc:`ValueError` exception.
        """
        if env is not None:
            parent_env = self.__get_parent_env()
            if parent_env is not None:
                raise ValueError("environment was already set by parent: {}".format(parent_env))
        injector = self.__class__(self._provider)
        self._children.append(injector)
        injector._parent = self  # pylint: disable=protected-access
        injector._scope = scope  # pylint: disable=protected-access
        injector._env = env  # pylint: disable=protected-access
        return injector

    def __get_parent_env(self):
        parent = self
        while parent is not None:
            env = parent._env  # pylint: disable=protected-access
            if env is not None:
                return env
            parent = parent._parent  # pylint: disable=protected-access

    def close(self) -> Optional[Awaitable[None]]:
        """Close this injector.

        Closing injector invalidates injector and makes it unusable.

        It also cleans up resources acquired by all generator-based object
        factories that were used.
        """

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
                maybe_coroutine = instance.close()
                if inspect.iscoroutine(maybe_coroutine):
                    await maybe_coroutine

        if self._provider is not None:  # FIXME: docs, quickstart, app.shutdown() required this if to work
            if not self._provider.has_awaitables():
                return do_close()
            return do_async_close()
