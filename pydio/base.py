import abc

from typing import Hashable, Callable, Type, TypeVar, Union, overload

from . import exc

T, U = TypeVar('T'), TypeVar('U')


class IInjector(abc.ABC):

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
        pass


class IInstance(abc.ABC):

    @property
    @abc.abstractmethod
    def target(self) -> Union[T, U]:
        pass

    @abc.abstractmethod
    def is_valid(self) -> bool:
        pass

    @abc.abstractmethod
    def invalidate(self):
        pass


class IUnboundInstance(abc.ABC):

    @abc.abstractmethod
    def bind(self, injector: IInjector) -> IInstance:
        pass


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
    def provides(self, key: Hashable) -> Callable:
        pass
