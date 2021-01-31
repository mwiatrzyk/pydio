import functools

from .base import IUnboundFactory, IFactory

_NOT_SET = object()


class GeneratorFactory(IFactory):

    def __init__(self, func):
        self._generator = func()
        self._instance = _NOT_SET

    @staticmethod
    def is_awaitable():
        return False

    def get_instance(self):
        if self._instance is _NOT_SET:
            self._instance = next(self._generator)
        return self._instance

    def close(self):
        try:
            next(self._generator)
        except StopIteration:
            pass


class AsyncGeneratorFactory(IFactory):

    def __init__(self, func):
        self._generator = func()
        self._instance = _NOT_SET

    @staticmethod
    def is_awaitable():
        return True

    def get_instance(self):
        async def async_get_instance():
            if self._instance is _NOT_SET:
                self._instance = await self._generator.__anext__()
            return self._instance
        return async_get_instance()

    def close(self):
        async def async_close():
            try:
                await self._generator.__anext__()
            except StopAsyncIteration:
                pass
        return async_close()


class CoroutineFactory(IFactory):

    def __init__(self, func):
        self._awaitable = func()
        self._instance = _NOT_SET

    @staticmethod
    def is_awaitable():
        return True

    def get_instance(self):
        async def async_get_instance():
            if self._instance is _NOT_SET:
                self._instance = await self._awaitable
            return self._instance
        return async_get_instance()

    def close(self):
        pass


class FunctionFactory(IFactory):

    def __init__(self, func):
        self._instance = func()

    @staticmethod
    def is_awaitable():
        return False

    def get_instance(self):
        return self._instance

    def close(self):
        pass


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
