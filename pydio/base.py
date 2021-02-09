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
from typing import Awaitable, Hashable, Optional, Type, TypeVar, Union, overload

T, U = TypeVar('T'), TypeVar('U')


class IInjector(abc.ABC):
    """Definition of injector interface."""

    @overload
    def inject(self, key: Type[T]) -> Union[T, Awaitable[T]]:
        pass

    @overload
    def inject(self, key: Hashable) -> Union[U, Awaitable[U]]:
        pass

    @abc.abstractmethod
    def inject(self, key):
        """Create and return object for given hashable key.

        On success, this method returns created object. On failure, it raises
        :exc:`pydio.exc.InjectorError`.

        This method may return a coroutine if object factory used to create
        output object is a coroutine.

        :param key:
            Identifier of underlying object factory to be used.
        """


class IFactory(abc.ABC):
    """Base class for bound factories.

    These classes are responsible for actual creation of target objects.
    Instances of this class are managed by :class:`IInjector` objects and are
    produced by :meth:`IUnboundFactory.bind` method.
    """

    @overload
    def get_instance(self) -> Optional[Union[T, Awaitable[T]]]:
        pass

    @overload
    def get_instance(self) -> Optional[Union[U, Awaitable[U]]]:
        pass

    @abc.abstractmethod
    def get_instance(self):
        """Create and return target object.

        This object is later returned by :meth:`IInjector.inject` method.
        """


class IUnboundFactory(abc.ABC):
    """Base class for unbound factories.

    Unbound factories are created and managed by :class:`IUnboundFactoryRegistry` objects.
    The role of this class is to wrap user-specified factory functions that
    are being registered to providers.
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


class IUnboundFactoryRegistry(abc.ABC):
    """Provides read-only access to :class:`IUnboundFactory` object
    registry."""

    @overload
    def get(self,
            key: Type[T],
            env: Hashable = None) -> Optional[IUnboundFactory]:
        pass

    @overload
    def get(self,
            key: Hashable,
            env: Hashable = None) -> Optional[IUnboundFactory]:
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
    def has_awaitables(self) -> bool:
        """Return True if this factory registry contains awaitable factories
        or False otherwise.

        Implementations will do this by querying underlying storage to find
        at least one :class:`IUnboundFactory` object for which
        :meth:`IUnboundFactory.is_awaitable` returns True.
        """
