# ---------------------------------------------------------------------------
# pydio/base.py
#
# Copyright (C) 2021 Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
#
# This file is part of PyDio library and is released under the terms of the
# MIT license: http://opensource.org/licenses/mit-license.php.
#
# See LICENSE.txt for details.
# ---------------------------------------------------------------------------
import abc
import contextlib
from typing import Any, Callable, Hashable, Type, TypeVar, Union, overload

from . import _utils, exc

T, U = TypeVar('T'), TypeVar('U')

NULL = _utils.Constant('NULL')

DEFAULT_ENV = _utils.Constant('DEFAULT_ENV')

DEFAULT_SCOPE = _utils.Constant('DEFAULT_SCOPE')


class IInjector(contextlib.AbstractContextManager):

    class NoProviderFoundError(exc.InjectorError):
        message_template = "No provider found for key: {self.key!r}"

        @property
        def key(self) -> Hashable:
            return self.params['key']

    class OutOfScopeError(exc.InjectorError):
        message_template =\
            "Cannot inject {self.key!r} due to scope mismatch: "\
            "{self.expected_scope!r} (expected) != {self.given_scope!r} (given)"

        @property
        def key(self) -> Hashable:
            return self.params['key']

        @property
        def expected_scope(self) -> Hashable:
            return self.params['expected_scope']

        @property
        def given_scope(self) -> Hashable:
            return self.params['given_scope']

    @overload
    def inject(self, key: Type[T]) -> T:
        pass

    @overload
    def inject(self, key: Hashable) -> U:
        pass

    @abc.abstractmethod
    def inject(self, key):
        pass

    @abc.abstractmethod
    def scoped(self, scope: Hashable) -> 'IInjector':
        pass

    @abc.abstractmethod
    def close(self):
        pass


class IFactory(abc.ABC):

    @staticmethod
    @abc.abstractmethod
    def is_awaitable() -> bool:
        pass

    @abc.abstractmethod
    def get_instance(
        self
    ) -> Union[T, U]:  # TODO: Union[T, U, NULL] (fails on NULL currently)
        pass

    @abc.abstractmethod
    def close(self):
        pass


class IUnboundFactory(abc.ABC):

    @property
    @abc.abstractmethod
    def scope(self) -> Hashable:
        pass

    @abc.abstractmethod
    def is_awaitable(self) -> bool:
        pass

    @abc.abstractmethod
    def bind(self, injector: IInjector) -> IFactory:
        pass


class IProvider(abc.ABC):

    class DoubleRegistrationError(exc.ProviderError):
        message_template = "Cannot register twice for: key={self.key!r}, env={self.env!r}"

        @property
        def key(self) -> Hashable:
            return self.params['key']

        @property
        def env(self) -> Hashable:
            return self.params['env']

    @overload
    def get(self, key: Type[T], env: Hashable = DEFAULT_ENV) -> IUnboundFactory:
        pass

    @overload
    def get(
        self, key: Hashable, env: Hashable = DEFAULT_ENV
    ) -> IUnboundFactory:
        pass

    @abc.abstractmethod
    def get(self, key, env=DEFAULT_ENV):
        pass

    # TODO: Rename to register_factory
    @abc.abstractmethod
    def register_func(
        self,
        key: Hashable,
        func: Callable,
        scope: Hashable = DEFAULT_SCOPE,
        env: Hashable = DEFAULT_ENV
    ):
        pass

    @abc.abstractmethod
    def register_instance(
        self,
        key: Hashable,
        value: Any,
        scope: Hashable = DEFAULT_SCOPE,
        env: Hashable = DEFAULT_ENV
    ):
        pass
