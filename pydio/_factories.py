# ---------------------------------------------------------------------------
# pydio/_factories.py
#
# Copyright (C) 2021 - 2023 Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
#
# This file is part of PyDio library and is released under the terms of the
# MIT license: http://opensource.org/licenses/mit-license.php.
#
# See LICENSE.txt for details.
# ---------------------------------------------------------------------------
from .base import IFactory

_UNDEFINED = object()


class GeneratorFactory(IFactory):
    awaitable = False

    def __init__(self, func):
        self._generator = func()
        self._instance = _UNDEFINED

    def get_instance(self):
        if self._instance is _UNDEFINED:
            self._instance = next(self._generator)
        return self._instance

    def close(self, exc_type=None, exc=None, tb=None):
        prev_instance = self._instance
        self._instance = None
        if prev_instance is not _UNDEFINED:
            if exc_type is None:
                try:
                    next(self._generator)
                except StopIteration:
                    pass
            else:
                try:
                    self._generator.throw(exc_type, exc, tb)
                except StopIteration:
                    raise exc
                else:
                    raise


class AsyncGeneratorFactory(IFactory):
    awaitable = True

    def __init__(self, func):
        self._generator = func()
        self._instance = _UNDEFINED

    def get_instance(self):

        async def async_get_instance():
            if self._instance is _UNDEFINED:
                self._instance = await self._generator.__anext__()
            return self._instance

        return async_get_instance()

    def close(self, exc_type=None, exc=None, tb=None):

        async def async_close():
            prev_instance = self._instance
            self._instance = None
            if prev_instance is not _UNDEFINED:
                if exc_type is None:
                    try:
                        await self._generator.__anext__()
                    except StopAsyncIteration:
                        pass
                else:
                    try:
                        await self._generator.athrow(exc_type, exc, tb)
                    except StopAsyncIteration:
                        raise exc

        return async_close()


class CoroutineFactory(IFactory):
    awaitable = True

    def __init__(self, func):
        self._awaitable = func()
        self._instance = _UNDEFINED

    def get_instance(self):

        async def async_get_instance():
            if self._instance is _UNDEFINED:
                self._instance = await self._awaitable
            return self._instance

        return async_get_instance()

    def close(self, exc_type=None, exc=None, tb=None):

        async def async_close():
            self._instance = None

        return async_close()


class FunctionFactory(IFactory):
    awaitable = False

    def __init__(self, func):
        self._instance = func()

    def get_instance(self):
        return self._instance

    def close(self, exc_type=None, exc=None, tb=None):
        self._instance = None


class InstanceFactory(IFactory):
    awaitable = False

    def __init__(self, value):
        self._value = value

    def get_instance(self):
        return self._value

    def close(self, exc_type=None, exc=None, tb=None):
        self._value = None
