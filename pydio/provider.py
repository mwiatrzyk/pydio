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
import inspect

from . import _factory
from .base import DEFAULT_ENV, DEFAULT_SCOPE, IProvider


class Provider(IProvider):

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

    def get(self, key, env=DEFAULT_ENV):
        envs = self._unbound_factories.get(key, {})
        found = envs.get(env)
        if found is None and env != DEFAULT_ENV:
            return envs.get(DEFAULT_ENV)
        return found

    def has_awaitables(self):
        return any(
            factory.is_awaitable() for factory in self._iter_factory_funcs()
        )

    def attach(self, provider: 'Provider'):
        for key, envs in provider._unbound_factories.items():  # pylint: disable=protected-access
            for env, unbound_factory in envs.items():
                self._check_key_availability(key, env)
                self._unbound_factories.setdefault(key,
                                                   {})[env] = unbound_factory

    def register_func(self, key, func, scope=DEFAULT_SCOPE, env=DEFAULT_ENV):
        self._check_key_availability(key, env)
        self._unbound_factories.setdefault(key, {})[env] =\
            _factory.GenericUnboundFactory(
                self.__get_factory_class_for(func), key, func, scope=scope, env=env)

    def register_instance(
        self, key, value, scope=DEFAULT_SCOPE, env=DEFAULT_ENV
    ):
        self._check_key_availability(key, env)
        self._unbound_factories.setdefault(key, {})[env] =\
            _factory.UnboundInstanceFactory(value, scope=scope, env=env)

    @staticmethod
    def __get_factory_class_for(func):
        if inspect.isasyncgenfunction(func):
            return _factory.AsyncGeneratorFactory
        if inspect.iscoroutinefunction(func):
            return _factory.CoroutineFactory
        if inspect.isgeneratorfunction(func):
            return _factory.GeneratorFactory
        return _factory.FunctionFactory

    def provides(self, key, scope=DEFAULT_SCOPE, env=DEFAULT_ENV):

        def decorator(func):
            self.register_func(key, func, scope=scope, env=env)
            return func

        return decorator
