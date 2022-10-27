# ---------------------------------------------------------------------------
# pydio/_unbound_factories.py
#
# Copyright (C) 2021 - 2022 Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
#
# This file is part of PyDio library and is released under the terms of the
# MIT license: http://opensource.org/licenses/mit-license.php.
#
# See LICENSE.txt for details.
# ---------------------------------------------------------------------------
import functools
import inspect

from . import _factories
from .base import IUnboundFactory


class UnboundFunctionFactory(IUnboundFactory):

    def __init__(self, func, key, scope=None, env=None):  # pylint: disable=too-many-arguments
        self._factory_class = self.__get_factory_class_for(func)
        self._key = key
        self._func = func
        self._func_params = inspect.signature(func).parameters
        self._scope = scope
        self._env = env

    @staticmethod
    def __get_factory_class_for(func):
        if inspect.isasyncgenfunction(func):
            return _factories.AsyncGeneratorFactory
        if inspect.iscoroutinefunction(func):
            return _factories.CoroutineFactory
        if inspect.isgeneratorfunction(func):
            return _factories.GeneratorFactory
        return _factories.FunctionFactory

    @property
    def scope(self):
        return self._scope

    def is_awaitable(self):
        return self._factory_class.awaitable

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

    def __init__(self, value, scope=None, env=None):
        self._value = value
        self._scope = scope
        self._env = env

    @property
    def scope(self):
        return self._scope

    def is_awaitable(self):
        return False

    def bind(self, *args):
        del args
        return _factories.InstanceFactory(self._value)
