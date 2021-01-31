import pytest

from mockify.mock import ABCMock
from mockify.core import satisfied

from pydio.base import IInjector
from pydio.provider import Provider


@pytest.fixture
def uut():
    return Provider()


@pytest.fixture
def injector():
    mock = ABCMock('injector', IInjector)
    with satisfied(mock):
        yield mock


def factory_function(_, key):
    return key


def test_one_key_cannot_be_used_twice(uut):
    uut.register_func('foo', factory_function)
    with pytest.raises(Provider.DoubleRegistrationError) as excinfo:
        uut.register_func('foo', factory_function)
    assert excinfo.value.key == 'foo'


def test_if_attached_provider_contains_duplicated_keys_it_will_be_rejected(uut):
    other = Provider()
    other.register_func('foo', factory_function)
    uut.register_func('foo', factory_function)
    with pytest.raises(Provider.DoubleRegistrationError) as excinfo:
        uut.attach(other)


def test_register_instance(uut, injector):
    uut.register_instance('foo', 123)
    unbound_factory = uut.get('foo')
    factory = unbound_factory.bind(injector)
    assert factory.get_instance() == 123


def test_instance_cannot_be_registered_if_key_is_already_in_use(uut):
    uut.register_func('foo', factory_function)
    with pytest.raises(Provider.DoubleRegistrationError) as excinfo:
        uut.register_instance('foo', 123)
