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
"""Abstract base classes for PyDio library.

This was made to make use of annotations easier, as all implementations
depend on this base module, not on concrete implementation.

.. data:: DEFAULT_ENV

    Default value for env.

    This is used if no user-defined environment was assigned.

.. data:: DEFAULT_SCOPE

    Default value for scope.

    This is used if no user-defined scope was used.
"""
import abc
import contextlib
from typing import Any, Callable, Hashable, Type, TypeVar, Union, overload, Awaitable, Optional

from . import _utils, exc

T, U = TypeVar('T'), TypeVar('U')

CloseResult = Union[None, Awaitable[None]]

NULL = _utils.Constant('NULL')

DEFAULT_ENV = _utils.Constant('DEFAULT_ENV')

DEFAULT_SCOPE = _utils.Constant('DEFAULT_SCOPE')


class IInjector(
    contextlib.AbstractContextManager, contextlib.AbstractAsyncContextManager
):
    """Base class for injectors.

    Injectors are used in application code to create and inject objects into
    the application. Additionally, injectors are owners of created objects,
    so the object lives for as long, as the injector does.

    Injectors are both async and non-async context managers and can be used
    along with ``with`` statement::

        with injector:
            return run_app(injector)

    Or with ``async with`` statement::

        async with injector:
            return await run_app(injector)

    When injector goes out of context, then :meth:`close` is called to free
    any allocated resources. Injector can no longer be used once it was
    closed.
    """

    class NoProviderFoundError(exc.InjectorError):
        """Raised when there was no matching provider found for given :attr:`key`.

        :param key:
            The key passed to injector's :meth:`IInjector.inject` method
        """
        message_template = "No provider found for key: {self.key!r}"

        @property
        def key(self) -> Hashable:
            return self.params['key']

    class OutOfScopeError(exc.InjectorError):
        """Raised if injector is not able to use factory that has been marked
        as available from different scope.

        :param key:
            The key passed to injector's :meth:`IInjector.inject` method

        :param expected_scope:
            The scope that is expected

        :param given_scope:
            The scope assigned to injector that raised this exception
        """
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

    class AlreadyClosedError(exc.InjectorError):
        """Raised when operation on a closed injector takes place."""
        message_template = "This injector was already closed"

    @overload
    def inject(self, key: Type[T]) -> Union[T, Awaitable[T]]:
        pass

    @overload
    def inject(self, key: Hashable) -> Union[U, Awaitable[U]]:
        pass

    @abc.abstractmethod
    def inject(self, key):
        """Inject object for given key.

        When called for the first time, then it performs a lookup to find
        matching factory (using API provided by :class:`IProvider`), and then
        uses it to create object. When called for the second time, then it
        returns already created object.

        :param key:
            The key to be used.

            This key must match the one used during registration in
            :class:`IProvider` object
        """

    @abc.abstractmethod
    def scoped(self, scope: Hashable) -> 'IInjector':
        """Create and return a scoped injector.

        Created injector will become a children of current one, it will be
        able to use parent or grandparent to inject objects, but it will only
        be able to manage lifetime of objects created by factories with same
        scope. Thanks to this, it will be able to create injector
        hierarchies, like in this example:

            * **global** (living for as long as the Python process does)
            * **class** (living for as long as some class does)
            * **method** (created before method is executed, closed just after
              method execution is done)

        Of course it's up to the user how to use scopes and how to name them.

        :param scope:
            User-defined name of the scope.

            To use full potential of scopes, you will have to additionally
            use same scope when registering factory function in
            :class:`IProvider` object.
        """

    @abc.abstractmethod
    def close(self) -> CloseResult:
        """Close this injector.

        When this is called, all objects created by this injector are also
        closed, and all children injectors (if any) are closed as well.
        Injector can no longer be used after close.

        If at least one coroutine- or async generator-based factory is used,
        then this method will return a coroutine; you will have to await on
        it to perform close operations asynchronously.
        """


class IFactory(abc.ABC):
    """Base class for bound factories.

    Objects of this class are owned by :class:`IInjector` objects, so once
    owning injector is closed, the factory must also be closed.
    """

    @staticmethod
    @abc.abstractmethod
    def is_awaitable() -> bool:
        """Return True if this factory manages awaitable objects or False
        otherwise."""

    @abc.abstractmethod
    def get_instance(
        self
    ) -> Union[T, U]:  # TODO: Union[T, U, NULL] (fails on NULL currently)
        """Return underlying object.

        This is singleton factory of target object; on the first call, the
        object must be created. On subsequent calls same object must be
        returned.
        """

    @abc.abstractmethod
    def close(self) -> CloseResult:
        """Close this factory.

        This must return awaitable if :meth:`is_awaitable` returns True.
        Called by :meth:`IInjector.close` during injector shutdown.
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
        this defaults to :attr:`DEFAULT_SCOPE` constant. Unbound factory can
        only be used by injector with matching scope.
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
        """Raised when same key was used twice.

        :param key:
            Key that was used

        :param env:
            Environment that was used
        """
        message_template = "Cannot register twice for: key={self.key!r}, env={self.env!r}"

        @property
        def key(self) -> Hashable:
            return self.params['key']

        @property
        def env(self) -> Hashable:
            return self.params['env']

    @overload
    def get(self, key: Type[T], env: Hashable = DEFAULT_ENV) -> Optional[IUnboundFactory]:
        pass

    @overload
    def get(
        self, key: Hashable, env: Hashable = DEFAULT_ENV
    ) -> Optional[IUnboundFactory]:
        pass

    @abc.abstractmethod
    def get(self, key, env=DEFAULT_ENV):
        """Get :class:`IUnboundFactory` registered for given key and env.

        If no factory was found, then return ``None``.

        :param key:
            Key to be used

        :param env:
            Environment to be used
        """

    @abc.abstractmethod
    def register_func(
        self,
        key: Hashable,
        func: Callable,
        scope: Hashable = DEFAULT_SCOPE,
        env: Hashable = DEFAULT_ENV
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
            injectors with same scope.

        :param env:
            Environment name to assign value to.

            Same key can be reused in different environments.
        """

    @abc.abstractmethod
    def register_instance(
        self,
        key: Hashable,
        value: Any,
        scope: Hashable = DEFAULT_SCOPE,
        env: Hashable = DEFAULT_ENV
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
