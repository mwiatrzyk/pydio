import inspect
import functools

from .base import IProvider, IUnboundInstance, IInstance


class _Instance(IInstance):

    def __init__(self, func):
        self._target = func()
        self._cached_target = None

    @property
    def target(self):
        if inspect.iscoroutine(self._target):
            return self.__wrap_coroutine_target()
        return self._target

    async def __wrap_coroutine_target(self):
        if self._cached_target is not None:
            return self._cached_target
        result = await self._target
        self._cached_target = result
        return result

    def invalidate(self):
        pass

    def is_valid(self):
        return True


class _UnboundInstance(IUnboundInstance):

    def __init__(self, func):
        self._func = func

    def bind(self, injector):
        return _Instance(functools.partial(self._func, injector))


class Provider(IProvider):

    def __init__(self):
        self._factory_funcs = {}

    def get(self, key):
        return self._factory_funcs.get(key)

    def provides(self, key):

        def decorator(func):
            self._factory_funcs[key] = _UnboundInstance(func)
            return func

        return decorator
