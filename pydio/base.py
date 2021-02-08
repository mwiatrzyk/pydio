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
"""Base types for PyDio library."""

import abc
import contextlib
from typing import Any, Callable, Hashable, Type, TypeVar, Union, overload, Awaitable, Optional

from . import exc

T, U = TypeVar('T'), TypeVar('U')


class IInjector(
    contextlib.AbstractContextManager, contextlib.AbstractAsyncContextManager
):
    """Base class for injectors."""

    class NoProviderFoundError(exc.InjectorError):
        """Raised when there was no matching provider found for given key.

        :param key:
            Searched key

        :param env:
            Searched environment
        """
        message_template = "No provider found for: key={self.key!r}, env={self.env!r}"

        def __init__(self, key, env):
            super().__init__(key=key, env=env)

        @property
        def key(self) -> Hashable:
            return self.params['key']

        @property
        def env(self) -> Hashable:
            return self.params['env']

    class OutOfScopeError(exc.InjectorError):
        """Raised when there was attempt to create object that was registered
        for different scope.

        :param key:
            Searched key

        :param scope:
            Injector's own scope

        :param required_scope:
            Required scope
        """
        message_template =\
            "Cannot inject {self.key!r} due to scope mismatch: "\
            "{self.required_scope!r} (required) != {self.scope!r} (owned)"

        def __init__(self, key, scope, required_scope):
            super().__init__(key=key, scope=scope, required_scope=required_scope)

        @property
        def key(self) -> Hashable:
            return self.params['key']

        @property
        def scope(self) -> Hashable:
            return self.params['scope']

        @property
        def required_scope(self) -> Hashable:
            return self.params['required_scope']

    class AlreadyClosedError(exc.InjectorError):
        """Raised when operation on a closed injector was performed."""
        message_template = "This injector was already closed"

    @property
    @abc.abstractmethod
    def env(self) -> Optional[Hashable]:
        """Return environment assigned to this injector."""

    @property
    @abc.abstractmethod
    def scope(self) -> Optional[Hashable]:
        """Return scope assigned to this injector.

        For root injector this will be ``None``.
        """

    @overload
    def inject(self, key: Type[T]) -> Union[T, Awaitable[T]]:
        pass

    @overload
    def inject(self, key: Hashable) -> Union[U, Awaitable[U]]:
        pass

    @abc.abstractmethod
    def inject(self, key):
        """Inject object for given key.

        On success, this returns object created by matching factory. On
        failure (f.e. when there was no provider found for given key, or when
        injector was already closed) this method raises
        :exc:`pydio.exc.InjectorError` exception.

        :param key:
            Searched key
        """

    @abc.abstractmethod
    def scoped(self, scope: Hashable) -> 'IInjector':
        """Create and return a scoped injector.

        Scoped injectors can only create objects using factories with same
        scope assigned. If no such factory was found, they can fall back to
        ancestor - up to the root injector. Side scopes are not visible.

        This can be used to limit object's lifetime to a particular scope,
        say application or single action.

        Scopes are completely user-defined.

        :param scope:
            User-defined scope name
        """

    @abc.abstractmethod
    def close(self) -> Optional[Awaitable[None]]:
        """Close this injector.

        This effectively calls :meth:`IFactory.close` for all factories
        created by this injector.

        If there are children scoped injectors created from this one, they
        are closed as well.

        If at least one of provided object factories is awaitable, then this
        method returns a coroutine that must be awaited to perform closing
        operation.

        When injector is used as context- or async context manager, this
        method will automatically be closed when leaving context.
        """


class IFactory(abc.ABC):
    """Base class for bound factories.

    These classes are responsible for actual creation of target objects.
    Instances of this class are managed by :class:`IInjector` objects and are
    produced by :meth:`IUnboundFactory.bind` method.
    """

    @staticmethod
    @abc.abstractmethod
    def is_awaitable() -> bool:
        """Return True if this factory manages awaitable objects or False
        otherwise."""

    @abc.abstractmethod
    def get_instance(
        self
    ) -> Union[T, U]:  # TODO: Union[T, U, None] (fails on None currently)
        """Create and return target object.

        This object is later returned by :meth:`IInjector.inject` method.
        """

    @abc.abstractmethod
    def close(self) -> Optional[Awaitable[None]]:
        """Close this factory.

        If underlying object factory function is awaitable, then this must
        return awaitable as well.
        """


class IUnboundFactory(abc.ABC):
    """Base class for unbound factories.

    Unbound factories are created and managed by :class:`IProvider` objects.
    The role of this class is to wrap user-specified factory functions that
    are being registered to providers.
    """

    @property
    @abc.abstractmethod
    def scope(self) -> Hashable:
        """Return user-defined scope for this factory.

        This is set by the user during registration. If no scope was given,
        this defaults to :attr:`None` constant. Unbound factory can
        only be used by injector with equal :attr:`IInjector.scope`
        attribute.
        """

    @abc.abstractmethod
    def is_awaitable(self) -> bool:
        """Return True if this factory produces awaitable :class:`IFactory`
        instances or False otherwise."""

    @abc.abstractmethod
    def bind(self, injector: IInjector) -> IFactory:
        """Create :class:`IFactory` object to be owned by given injector.

        :param injector:
            Injector to be bound
        """


class IProvider(abc.ABC):
    """Base class for providers."""

    class DoubleRegistrationError(exc.ProviderError):
        """Raised when same ``(key, env)`` tuple was used twice during
        registration.

        :param key:
            Registered key

        :param env:
            Registered environment
        """
        message_template = "Cannot register twice for: key={self.key!r}, env={self.env!r}"

        def __init__(self, key, env):
            super().__init__(key=key, env=env)

        @property
        def key(self) -> Hashable:
            return self.params['key']

        @property
        def env(self) -> Hashable:
            return self.params['env']

    @overload
    def get(self, key: Type[T], env: Hashable = None) -> Optional[IUnboundFactory]:
        pass

    @overload
    def get(
        self, key: Hashable, env: Hashable = None
    ) -> Optional[IUnboundFactory]:
        pass

    @abc.abstractmethod
    def get(self, key, env=None):
        """Get :class:`IUnboundFactory` registered for given key and (if
        given) environment.

        If no factory was found, then return ``None``.

        :param key:
            Searched key

        :param env:
            Searched environment
        """

    @abc.abstractmethod
    def register_func(
        self,
        key: Hashable,
        func: Callable,
        scope: Hashable = None,
        env: Hashable = None
    ):
        """Register given user-defined function as a factory.

        :param key:
            The key to be used

        :param func:
            Function to be registered.

            This can be normal function, coroutine function, generator or
            async generator.

        :param scope:
            The scope for this factory.

            If this is given, registered factory will only be available to
            injectors with equal :attr:`IInjector.scope` attribute.

        :param env:
            Environment name to assign value to.

            Same key can be reused in different environments. This is to
            achieve different implementations depending on environment the
            application is running in. For example, for development this
            could be some kind of stub, for testing this will be some kind of
            mock, and for production - this will be production
            implementation.
        """

    @abc.abstractmethod
    def register_instance(
        self,
        key: Hashable,
        value: Any,
        scope: Hashable = None,
        env: Hashable = None
    ):
        """Register given user-defined instance.

        This is a form of constant registering and can be used to inject some
        global objects like config modules etc.

        :param key:
            The key to be used

        :param value:
            The value to be assigned

        :param scope:
            The scope for this value.

            If this is given, value will only be available to injectors with
            same scope.

        :param env:
            Environment name to assign value to.

            Same key can be reused in different environments.
        """
