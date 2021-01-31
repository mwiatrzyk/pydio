import abc
import contextlib

from typing import Hashable, Callable, Type, TypeVar, Union, overload

from . import exc

T, U = TypeVar('T'), TypeVar('U')


class IInjector(contextlib.AbstractContextManager):

    class NoProviderFound(exc.Base):
        message_template = "No provider found for key: {self.key!r}"

    class AlreadyClosed(exc.Base):
        message_template = "Injector was already closed"

    class OutOfScope(exc.Base):
        message_template = "Cannot inject {self.key!r} due to scope mismatch: {self.expected_scope!r} (expected) != {self.given_scope} (given)"

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

    @abc.abstractmethod
    def is_awaitable(self) -> bool:
        pass

    @abc.abstractmethod
    def get_instance(self) -> Union[T, U]:
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

    @overload
    def get(self, key: Type[T], scope: Hashable=None) -> IUnboundFactory:
        pass

    @overload
    def get(self, key: Hashable, scope: Hashable=None) -> IUnboundFactory:
        pass

    @abc.abstractmethod
    def get(self, key, scope=None):
        pass

    @abc.abstractmethod
    def register_func(self, key: Hashable, func: Callable, scope: Hashable=None):
        pass
