# ---------------------------------------------------------------------------
# pydio/_factory.py
#
# Copyright (C) 2021 Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
#
# This file is part of PyDio library and is released under the terms of the
# MIT license: http://opensource.org/licenses/mit-license.php.
#
# See LICENSE.txt for details.
# ---------------------------------------------------------------------------
import functools
import inspect

from . import _utils
from .base import DEFAULT_ENV, DEFAULT_SCOPE, NULL, IFactory, IUnboundFactory

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

    def __init__(
        self,
        factory_class,
        key,
        func,
        scope=DEFAULT_SCOPE,
        env=DEFAULT_ENV
    ):  # pylint: disable=too-many-arguments
        self._factory_class = factory_class
        self._key = key
        self._func = func
        self._func_params = inspect.signature(func).parameters
        self._scope = scope
        self._env = env

    @property
    def scope(self):
        return self._scope

    def is_awaitable(self):
        return self._factory_class.is_awaitable()

    def bind(self, injector):
        return self._factory_class(self.__make_partial(injector))

    def __make_partial(self, injector):
        # TODO: Current implementation requires factory functions to use args
        # with forced name. Although those params can be given in any order, I
        # would like to rewrite this part to allow matching by annotation, so
        # different names could be used
        kwargs = {}
        if 'injector' in self._func_params:
            kwargs['injector'] = injector
        if 'key' in self._func_params:
            kwargs['key'] = self._key
        if 'env' in self._func_params:
            kwargs['env'] = self._env
        return functools.partial(self._func, **kwargs)


class UnboundInstanceFactory(IUnboundFactory):

    def __init__(self, value, scope=DEFAULT_SCOPE, env=DEFAULT_ENV):
        self._value = value
        self._scope = scope
        self._env = env

    @property
    def scope(self):
        return self._scope

    def is_awaitable(self):
        return False

    def bind(self, *_):
        return InstanceFactory(self._value)
