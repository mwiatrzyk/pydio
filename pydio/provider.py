import abc
import inspect
import functools

from . import _factory
from .base import IProvider


class Provider(IProvider):

    def __init__(self):
        self._factory_funcs = {}

    def get(self, key):
        return self._factory_funcs.get(key)

    def has_awaitables(self):
        return any(factory.is_awaitable() for factory in self._factory_funcs.values())

    def attach(self, provider: 'Provider'):
        for k, v in provider._factory_funcs.items():
            self._factory_funcs[k] = v

    def register_func(self, key, func, scope=None):
        if inspect.isgeneratorfunction(func):
            self._factory_funcs[key] = _factory.UnboundGeneratorFactory(key, func, scope=scope)
        elif inspect.isasyncgenfunction(func):
            self._factory_funcs[key] = _factory.UnboundAsyncGeneratorFactory(key, func, scope=scope)
        elif inspect.iscoroutinefunction(func):
            self._factory_funcs[key] = _factory.UnboundCoroutineFactory(key, func, scope=scope)
        else:
            self._factory_funcs[key] = _factory.UnboundFunctionFactory(key, func, scope=scope)

    def provides(self, key, **kwargs):

        def decorator(func):
            self.register_func(key, func, **kwargs)
            return func

        return decorator
