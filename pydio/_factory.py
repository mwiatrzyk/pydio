import functools

from .base import IUnboundFactory, IFactory

_NOT_SET = object()


class GeneratorFactory(IFactory):

    def __init__(self, func):
        self._generator = func()
        self._instance = _NOT_SET

    def get_instance(self):
        if self._instance is _NOT_SET:
            self._instance = next(self._generator)
        return self._instance

    def is_awaitable(self):
        return False

    def close(self):
        try:
            next(self._generator)
        except StopIteration:
            pass


class AsyncGeneratorFactory(IFactory):

    def __init__(self, func):
        self._generator = func()
        self._instance = _NOT_SET

    def get_instance(self):
        async def async_get_instance():
            if self._instance is _NOT_SET:
                self._instance = await self._generator.__anext__()
            return self._instance
        return async_get_instance()

    def is_awaitable(self):
        return True

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

    def get_instance(self):
        async def async_get_instance():
            if self._instance is _NOT_SET:
                self._instance = await self._awaitable
            return self._instance
        return async_get_instance()

    def is_awaitable(self):
        return True

    def close(self):
        pass


class FunctionFactory(IFactory):

    def __init__(self, func):
        self._instance = func()

    def get_instance(self):
        return self._instance

    def is_awaitable(self):
        return False

    def close(self):
        pass


class BaseUnboundFactory(IUnboundFactory):

    def __init__(self, key, func, scope=None):
        self._key = key
        self._func = func
        self._scope = scope

    @property
    def scope(self):
        return self._scope


class UnboundGeneratorFactory(BaseUnboundFactory):

    def is_awaitable(self):
        return False

    def bind(self, injector):
        return GeneratorFactory(functools.partial(self._func, injector, self._key))


class UnboundCoroutineFactory(BaseUnboundFactory):

    def is_awaitable(self):
        return True

    def bind(self, injector):
        return CoroutineFactory(functools.partial(self._func, injector, self._key))


class UnboundAsyncGeneratorFactory(BaseUnboundFactory):

    def is_awaitable(self):
        return True

    def bind(self, injector):
        return AsyncGeneratorFactory(functools.partial(self._func, injector, self._key))


class UnboundFunctionFactory(BaseUnboundFactory):

    def is_awaitable(self):
        return False

    def bind(self, injector):
        return FunctionFactory(functools.partial(self._func, injector, self._key))
