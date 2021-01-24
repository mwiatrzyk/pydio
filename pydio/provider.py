import inspect
import functools

from .base import IProvider, IUnboundInstance, IInstance


class _Instance(IInstance):

    def __init__(self, func):
        self._target = func()
        self._cached_target = None

    def get(self):
        if inspect.iscoroutine(self._target):
            return self.__wrap_coroutine_target()
        elif inspect.isgenerator(self._target):
            return self.__wrap_generator_target()
        else:
            return self._target

    def __wrap_generator_target(self):
        if self._cached_target is not None:
            return self._cached_target
        value = next(self._target)
        self._cached_target = value
        return value

    async def __wrap_coroutine_target(self):
        if self._cached_target is not None:
            return self._cached_target
        result = await self._target
        self._cached_target = result
        return result

    def invalidate(self):
        if inspect.isgenerator(self._target):
            try:
                next(self._target)
            except StopIteration:
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

    def register_func(self, key, func, scope=None):
        self._factory_funcs[key] = _UnboundInstance(func)

    def provides(self, key, **kwargs):

        def decorator(func):
            self.register_func(key, func, **kwargs)
            return func

        return decorator
