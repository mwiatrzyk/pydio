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
"""Interface definitions."""

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

        On success, this method returns created object or awaitable pointing
        to created object. On failure, it raises
        :exc:`pydio.exc.InjectorError`.

        :param key:
            Identifier of underlying object factory to be used.

            This can be either class object (f.e. base class or interface), a
            hashable (f.e. string or a number), or a special key wrapper from
            :mod:`pydio.keys`.

            Please be aware that same key has to be used in provider during
            registration of object factory.
        """


class IFactory(abc.ABC):
    """Interface for bound factories.

    Bound factories are managed by :class:`IInjector` objects and are
    responsible for construction of target object that is later returned by
    :meth:`IInjector.inject`. Each factory should wrap one kind of object
    factory function provided by user (f.e. normal function or a coroutine,
    but never both).
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

        Value returned by this method is later also returned by
        :meth:`IInjector.inject` method.
        """


class IUnboundFactory(abc.ABC):
    """Interface for unbound factories.

    Unbound factories are created and managed by
    :class:`IUnboundFactoryRegistry` objects. The role of this class is to
    wrap user-specified factory functions that are being registered to
    providers.
    """

    @property
    @abc.abstractmethod
    def scope(self) -> Optional[Hashable]:
        """Name of the scope assigned to this factory.

        Factories with scopes defined can only be used by injectors with same
        scope set.
        """

    @abc.abstractmethod
    def is_awaitable(self) -> bool:
        """Return True if this factory produces awaitable :class:`IFactory`
        instances or False otherwise."""

    @abc.abstractmethod
    def bind(self, injector: IInjector) -> IFactory:
        """Create :class:`IFactory` object to be owned by given injector.

        :param injector:
            The owner of bound factory object to be created
        """


class IUnboundFactoryRegistry(abc.ABC):
    """Interface for :class:`IUnboundFactory` objects registry.

    Factory registries are used by :class:`IInjector` objects to find
    :class:`IUnboundFactory` object that matches key that was given to
    :meth:`IInjector.inject` call.
    """

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
        """Get :class:`IUnboundFactory` registered for given key and
        environment (if given).

        If no factory was found, then return None.

        :param key:
            See :meth:`IInjector.inject`

        :param env:
            Environment name.

            Same **key** can be reused by multiple environments, but none can
            have that key duplicated. This is used to provide several
            different implementations of one key that depend on environment
            on which application is executed (f.e. different database may be
            needed in testing, and different in production)
        """

    @abc.abstractmethod
    def has_awaitables(self) -> bool:
        """Return True if this factory registry contains awaitable factories
        or False otherwise.

        Behind the scenes, this will check if there is at least one unbound
        factory for which :meth:`IUnboundFactory.is_awaitable` returns True.
        """
