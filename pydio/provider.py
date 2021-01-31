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
        if key in self._factory_funcs:
            raise self.DoubleRegistrationError(key=key)
        self._factory_funcs[key] =\
            _factory.GenericUnboundFactory(
                self.__get_factory_class_for(func), key, func, scope=scope)

    def __get_factory_class_for(self, func):
        if inspect.isasyncgenfunction(func):
            return _factory.AsyncGeneratorFactory
        elif inspect.iscoroutinefunction(func):
            return _factory.CoroutineFactory
        elif inspect.isgeneratorfunction(func):
            return _factory.GeneratorFactory
        else:
            return _factory.FunctionFactory

    def provides(self, key, **kwargs):

        def decorator(func):
            self.register_func(key, func, **kwargs)
            return func

        return decorator
