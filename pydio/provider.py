# ---------------------------------------------------------------------------
# pydio/provider.py
#
# Copyright (C) 2021 Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
#
# This file is part of PyDio library and is released under the terms of the
# MIT license: http://opensource.org/licenses/mit-license.php.
#
# See LICENSE.txt for details.
# ---------------------------------------------------------------------------
from typing import Hashable

from . import _unbound_factories, exc
from .base import IUnboundFactoryRegistry


class Provider(IUnboundFactoryRegistry):
    """Used to record user-defined object factories or instances and bind
    them with particular key, that can later be used by
    :meth:`IInjector.inject`."""

    def __init__(self):
        self._unbound_factories = {}

    def _check_key_availability(self, key, env):
        found = self._unbound_factories.get(key, {}).get(env)
        if found is not None:
            raise self.DoubleRegistrationError(key=key, env=env)

    def _iter_factory_funcs(self):
        for envs in self._unbound_factories.values():
            for unbound_factory in envs.values():
                yield unbound_factory

    def get(self, key, env=None):
        """See :meth:`IUnboundFactoryRegistry.get`."""
        envs = self._unbound_factories.get(key, {})
        found = envs.get(env)
        if found is None and env != None:
            return envs.get(None)
        return found

    def has_awaitables(self):
        """See :meth:`IUnboundFactoryRegistry.has_awaitables`."""
        return any(
            factory.is_awaitable() for factory in self._iter_factory_funcs()
        )

    def attach(self, provider: 'Provider'):
        """Attach given provider to this provider.

        This effectively extends current provider with object factories
        registered to the other one.

        Use this if you need to split your providers across multiple modules.
        """
        for key, envs in provider._unbound_factories.items():  # pylint: disable=protected-access
            for env, unbound_factory in envs.items():
                self._check_key_availability(key, env)
                self._unbound_factories.setdefault(key,
                                                   {})[env] = unbound_factory

    def register_func(self, key, func, scope=None, env=None):
        """Register user factory function.

        :param key:
            Key to be used for **func**.

            See :meth:`IInjector.inject` for more info.

        :param func:
            User-defined function to be registered.

            This can be normal function, coroutine, generator or async
            denerator.

        :param scope:
            Optional scope to be assigned.

        :param env:
            Optional environment to be assigned
        """
        self._check_key_availability(key, env)
        self._unbound_factories.setdefault(key, {})[env] =\
            _unbound_factories.UnboundFunctionFactory(func, key, scope=scope, env=env)

    def register_instance(self, key, value, scope=None, env=None):
        """Same as :meth:`register_func`, but for registration of constant
        objects.

        If your application has some global configuration data you want to
        inject using PyDio - that's the method you should use.
        """
        self._check_key_availability(key, env)
        self._unbound_factories.setdefault(key, {})[env] =\
            _unbound_factories.UnboundInstanceFactory(value, scope=scope, env=env)

    def provides(self, key, scope=None, env=None):
        """Same as :meth:`register_func`, but to be used as a decorator.

        Here's an example:

        .. testcode::

            from pydio.api import Provider

            provider = Provider()

            @provider.provides('spam')
            def make_spam():
                return 'give me more spam'
        """

        def decorator(func):
            self.register_func(key, func, scope=scope, env=env)
            return func

        return decorator

    class DoubleRegistrationError(exc.ProviderError):
        """Raised when same ``(key, env)`` tuple was used twice during
        registration.

        :param key:
            Registered key

        :param env:
            Registered environment
        """
        message_template = "Cannot register twice for: key={self.key!r}, env={self.env!r}"

        def __init__(self, key, env):
            super().__init__(key=key, env=env)

        @property
        def key(self) -> Hashable:
            return self.params['key']

        @property
        def env(self) -> Hashable:
            return self.params['env']
