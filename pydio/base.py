import abc

from typing import Hashable, Callable, Type, TypeVar, Union, overload

from . import exc

T, U = TypeVar('T'), TypeVar('U')


class IInstance(abc.ABC):
    """Provides API to manipulate instances created by :class:`IInjector`.

    Instances of this class are created by :class:`IUnboundInstance`
    subclasses.
    """

    @abc.abstractmethod
    def get(self) -> Union[T, U]:
        """Get wrapped object.

        This should always return same instance.
        """

    @abc.abstractmethod
    def is_valid(self) -> bool:
        """Check if object returned by :meth:`get` is valid and can still be
        used."""

    @abc.abstractmethod
    def invalidate(self):
        """Invalidate object returned by :meth:`get`.

        Invalidation may trigger resource clearing, connection shutdown
        etc. - depending on what was implemented in provider. Please note
        that invalidation is only meaningful for generator-based providers;
        in other cases this will do nothing.
        """


class IInjector(abc.ABC):
    """Provides injector API."""

    class NoProviderFound(exc.Base):
        message_template = "No provider found for key: {self.key!r}"

    @overload
    def inject(self, key: Type[T]) -> T:
        pass

    @overload
    def inject(self, key: Hashable) -> U:
        pass

    @abc.abstractmethod
    def inject(self, key):
        """Injects instance for given ``key``.

        If no provider specified for ``key``, this will raise
        :exc:`IInjector.NoProviderFound` exception. Otherwise it will either
        return matching instance from cache (if exists) or create the
        instance, fill cache with it and return it. Each injector instance
        will always inject same object for given ``key``.

        :param key:
            Key pointing to instance to be injected.

            This can be any hashable object, however it will usually be some
            kind of interface.
        """

    @abc.abstractmethod
    def close(self):
        """Closes this injector.

        Behind the scenes, this method will perform cleanup actions on all
        instances created by this injector. This effectively makes
        :meth:`inject` to be unusable for this injector.
        """


class IUnboundInstance(abc.ABC):
    """Provides API for creating :class:`IInstance` objects.

    Unbound instances are created and managed by :class:`IProvider`
    subclasses.
    """

    @abc.abstractmethod
    def bind(self, injector: IInjector) -> IInstance:
        """Binds this unbound instance with given params.

        :param injector:
            Instance of :class:`IInjector` to be bound with produced
            :class:`IInstance` object
        """


class IProvider(abc.ABC):

    @overload
    def get(self, key: Type[T]) -> IUnboundInstance:
        pass

    @overload
    def get(self, key: Hashable) -> IUnboundInstance:
        pass

    @abc.abstractmethod
    def get(self, key):
        pass

    @abc.abstractmethod
    def register_func(self, key: Hashable, func: Callable, scope: Hashable=None):
        pass
