# ---------------------------------------------------------------------------
# pydio/base.py
#
# Copyright (C) 2021 - 2023 Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>
#
# This file is part of PyDio library and is released under the terms of the
# MIT license: http://opensource.org/licenses/mit-license.php.
#
# See LICENSE.txt for details.
# ---------------------------------------------------------------------------
"""Interface definitions."""

import abc
import contextlib
import typing
from typing import Awaitable, Hashable, Optional, TypeVar, Union

from . import _compat

T = TypeVar('T')


class IInjector(
    contextlib.AbstractContextManager, _compat.AbstractAsyncContextManager
):
    """Definition of injector interface."""

    @abc.abstractmethod
    def inject(self, key: Hashable) -> Union[T, Awaitable[T]]:
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

    @abc.abstractmethod
    def scoped(self, scope: Hashable, env: Hashable = None) -> 'IInjector':
        """Create scoped injector that is a child of current one.

        Scoped injectors can only operate on
        :class:`pydio.base.IUnboundFactory` objects with
        :attr:`pydio.base.IUnboundFactory.scope` attribute being equal to
        given scope.

        :param scope:
            User-defined scope name.

        :param env:
            User-defined environment name for newly created injector and all
            its descendants.

            This option is applicable only if none of the ancestors of newly
            created injector has environment set. Otherwise, setting this will
            cause :exc:`ValueError` exception.
        """

    @abc.abstractmethod
    def close(self) -> Optional[Awaitable[None]]:
        """Close this injector.

        Closing injector invalidates injector and makes it unusable.

        It also cleans up internal cache by calling :meth:`IFactory.close`
        for each factory being in use by this injector. If this injector has
        children injectors (created by calling :meth:`scoped` method) then
        those are closed as well (recursively).
        """


class IFactory(abc.ABC):
    """Interface for bound factories.

    Bound factories are managed by :class:`IInjector` objects and are
    responsible for construction of target object that is later returned by
    :meth:`IInjector.inject`. Each factory should wrap one kind of object
    factory function provided by user (f.e. normal function or a coroutine,
    but never both).

    .. deprecated:: 0.4.0
        This will be removed from the public interface.
    """

    @abc.abstractmethod
    def get_instance(self) -> Optional[Union[T, Awaitable[T]]]:
        """Create and return target object.

        Value returned by this method is later also returned by
        :meth:`IInjector.inject` method.
        """

    @abc.abstractmethod
    def close(
        self,
        exc_type: typing.Type[BaseException] = None,
        exc: BaseException = None,
        tb=None
    ):
        """Close this factory.

        When called, underlying instance is cleared and calling
        :meth:`get_instance` again will return None. This method may also
        invoke some additional custom-defined clearing actions (if supported
        by implementation).

        :param exc_type:
            Exception type.

            This will be set with exception class object when underlying
            factory is closed due to exception being raised.

            .. versionadded:: 0.4.0

        :param exc:
            Exception object.

            This will be set with exception instance when underlying factory is
            closed due to exception being raised.

            .. versionadded:: 0.4.0

        :param tb:
            Traceback object.

            This will be set when underlying factory is closed due to exception
            being raised.

            .. versionadded:: 0.4.0
        """


class IUnboundFactory(abc.ABC):
    """Interface for unbound factories.

    Unbound factories are created and managed by
    :class:`IUnboundFactoryRegistry` objects. The role of this class is to
    wrap user-specified factory functions that are being registered to
    providers.

    .. deprecated:: 0.4.0
        This will be removed from the public interface.
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

    .. deprecated:: 0.4.0
        This will be removed from the public interface.
    """

    @abc.abstractmethod
    def get(self,
            key: Hashable,
            env: Hashable = None) -> Optional[IUnboundFactory]:
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
