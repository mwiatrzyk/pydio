import functools

from . import exc, _utils
from .base import IUnboundFactory, IFactory, NULL

_UNDEFINED = _utils.Constant('_UNDEFINED')


class GeneratorFactory(IFactory):

    def __init__(self, func):
        self._generator = func()
        self._instance = _UNDEFINED

    @staticmethod
    def is_awaitable():
        return False

    def get_instance(self):
        if self._instance is _UNDEFINED:
            self._instance = next(self._generator)
        return self._instance

    def close(self):
        prev_instance = self._instance
        self._instance = NULL
        if prev_instance is not _UNDEFINED:
            try:
                next(self._generator)
            except StopIteration:
                pass


class AsyncGeneratorFactory(IFactory):

    def __init__(self, func):
        self._generator = func()
        self._instance = _UNDEFINED

    @staticmethod
    def is_awaitable():
        return True

    def get_instance(self):
        async def async_get_instance():
            if self._instance is _UNDEFINED:
                self._instance = await self._generator.__anext__()
            return self._instance
        return async_get_instance()

    def close(self):
        async def async_close():
            prev_instance = self._instance
            self._instance = NULL
            if prev_instance is not _UNDEFINED:
                try:
                    await self._generator.__anext__()
                except StopAsyncIteration:
                    pass
        return async_close()


class CoroutineFactory(IFactory):

    def __init__(self, func):
        self._awaitable = func()
        self._instance = _UNDEFINED

    @staticmethod
    def is_awaitable():
        return True

    def get_instance(self):
        async def async_get_instance():
            if self._instance is _UNDEFINED:
                self._instance = await self._awaitable
            return self._instance
        return async_get_instance()

    def close(self):
        async def async_close():
            self._instance = NULL
        return async_close()


class FunctionFactory(IFactory):

    def __init__(self, func):
        self._instance = func()

    @staticmethod
    def is_awaitable():
        return False

    def get_instance(self):
        return self._instance

    def close(self):
        self._instance = NULL


class InstanceFactory(IFactory):

    def __init__(self, value):
        self._value = value

    @staticmethod
    def is_awaitable():
        return False

    def get_instance(self):
        return self._value

    def close(self):
        self._value = NULL


class GenericUnboundFactory(IUnboundFactory):

    def __init__(self, factory_class, key, func, scope=None):
        self._factory_class = factory_class
        self._key = key
        self._func = func
        self._scope = scope

    @property
    def scope(self):
        return self._scope

    def is_awaitable(self):
        return self._factory_class.is_awaitable()

    def bind(self, injector):
        return self._factory_class(functools.partial(self._func, injector, self._key))


class UnboundInstanceFactory(IUnboundFactory):

    def __init__(self, value, scope=None):
        self._value = value
        self._scope = scope

    @property
    def scope(self):
        return self._scope

    def is_awaitable(self):
        return False

    def bind(self, *args):
        return InstanceFactory(self._value)
